"""Find aligned document-background candidates; never infer accepted original counts."""

import argparse
import csv
import io
import json
import shutil
import tempfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

from PIL import Image, ImageChops, ImageDraw, ImageOps

from sealsign.data.geometry import parse_labels
from sealsign.data.importer import sha256, zip_inventory

SIZE = 128
GRID = 4
PARAMETERS = {
    "size": SIZE,
    "grid": GRID,
    "tile_hash": "mean-threshold-8x8",
    "tile_min_range": 40,
    "tile_min_dark_pixels": 20,
    "tile_max_mask_pixels": 256,
    "max_bucket_pages": 200,
    "min_shared_tiles": 4,
    "min_visible_fraction": 0.5,
    "min_ink_pixels": 128,
    "dark_threshold": 200,
    "pixel_tolerance": 12,
    "min_close_fraction": 0.85,
    "min_ink_iou": 0.70,
}


def fingerprint(image, objects):
    """Normalize geometry only; retain original orientation and exclude labelled stamps."""
    width, height = image.size
    gray = ImageOps.grayscale(image).resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    mask = Image.new("L", (SIZE, SIZE))
    draw = ImageDraw.Draw(mask)
    for obj in objects:
        x, y, w, h = obj["bbox"]
        draw.rectangle(
            (
                x / width * SIZE - 2,
                y / height * SIZE - 2,
                (x + w) / width * SIZE + 2,
                (y + h) / height * SIZE + 2,
            ),
            fill=255,
        )
    tiles = {}
    side = SIZE // GRID
    for row in range(GRID):
        for col in range(GRID):
            bounds = (col * side, row * side, (col + 1) * side, (row + 1) * side)
            tile = gray.crop(bounds)
            pixels = list(tile.get_flattened_data())
            if (
                max(pixels) - min(pixels) < PARAMETERS["tile_min_range"]
                or sum(v < 200 for v in pixels) < PARAMETERS["tile_min_dark_pixels"]
                or mask.crop(bounds).histogram()[255] > PARAMETERS["tile_max_mask_pixels"]
            ):
                continue
            small = list(tile.resize((8, 8), Image.Resampling.LANCZOS).get_flattened_data())
            mean = sum(small) / len(small)
            value = 0
            for pixel in small:
                value = (value << 1) | (pixel < mean)
            # Position is part of the key: different regions cannot match by accident.
            tiles[row * GRID + col] = value
    return bytes(gray.get_flattened_data()), bytes(mask.get_flattened_data()), tiles


def compare(a, b):
    """Compare visible background, requiring ink agreement as well as white space."""
    av, am, bv, bm = [Image.frombytes("L", (SIZE, SIZE), v) for v in [a[0], a[1], b[0], b[1]]]
    visible_mask = ImageOps.invert(ImageChops.lighter(am, bm))
    visible = visible_mask.histogram()[255]
    close_mask = ImageChops.difference(av, bv).point(
        lambda v: 255 if v <= PARAMETERS["pixel_tolerance"] else 0
    )
    close = ImageChops.darker(visible_mask, close_mask).histogram()[255]
    dark_a, dark_b = [
        ImageChops.darker(
            visible_mask, im.point(lambda v: 255 if v < PARAMETERS["dark_threshold"] else 0)
        )
        for im in [av, bv]
    ]
    ink_a, ink_b = dark_a.histogram()[255], dark_b.histogram()[255]
    intersection = ImageChops.darker(dark_a, dark_b).histogram()[255]
    union = ImageChops.lighter(dark_a, dark_b).histogram()[255]
    close_fraction = close / visible if visible else 0.0
    ink_iou = intersection / union if union else 0.0
    passed = (
        visible >= SIZE * SIZE * PARAMETERS["min_visible_fraction"]
        and min(ink_a, ink_b) >= PARAMETERS["min_ink_pixels"]
        and close_fraction >= PARAMETERS["min_close_fraction"]
        and ink_iou >= PARAMETERS["min_ink_iou"]
    )
    return passed, visible, close_fraction, ink_iou


def candidates(features):
    buckets = defaultdict(list)
    for index, feature in enumerate(features):
        for position, value in feature[2].items():
            buckets[position, value].append(index)
    ignored = sum(len(v) > PARAMETERS["max_bucket_pages"] for v in buckets.values())
    buckets = {key: v for key, v in buckets.items() if len(v) <= PARAMETERS["max_bucket_pages"]}
    pairs = []
    compared = 0
    for a, feature in enumerate(features):
        shared = Counter()
        for key in feature[2].items():
            shared.update(b for b in buckets.get(key, []) if b > a)
        for b, count in sorted(shared.items()):
            if count < PARAMETERS["min_shared_tiles"]:
                continue
            compared += 1
            passed, visible, close, iou = compare(feature, features[b])
            if passed:
                pairs.append((a, b, count, visible, close, iou))
    return pairs, ignored, compared


def audit(archives, output):
    if output.exists():
        raise ValueError("Output already exists")
    if len({p.resolve() for p in archives}) != len(archives):
        raise ValueError("Repeated archive")
    records, features, inputs = [], [], []
    for path in sorted(archives):
        archive_hash = sha256(path)
        with zipfile.ZipFile(path) as archive:
            entries = zip_inventory(archive)
            names = sorted(
                n
                for n in entries
                if n.startswith("images/")
                and PurePosixPath(n).suffix.lower() in {".jpg", ".jpeg", ".png"}
            )
            for name in names:
                if entries[name].file_size > 64 * 1024**2:
                    raise ValueError("Image exceeds byte budget")
                label = str(
                    PurePosixPath(name.replace("images/", "labels/", 1)).with_suffix(".txt")
                )
                if label not in entries or entries[label].file_size > 4 * 1024**2:
                    raise ValueError("Missing or oversized label")
                with Image.open(io.BytesIO(archive.read(name))) as image:
                    if image.width * image.height > 50_000_000:
                        raise ValueError("Image exceeds pixel budget")
                    if image.getexif().get(274, 1) != 1:
                        raise ValueError("EXIF requires coordinate review")
                    image.load()
                    objects = parse_labels(
                        archive.read(label).decode("utf-8"), "bbox", {"0": 0}, *image.size
                    )
                    features.append(fingerprint(image, objects))
                records.append({"archive_sha256": archive_hash, "archive": path.name, "file": name})
        inputs.append({"filename": path.name, "sha256": archive_hash, "images": len(names)})
    pairs, ignored, compared = candidates(features)
    counts = Counter()
    for a, b, *_ in pairs:
        counts["cross_archive_pairs"] += (
            records[a]["archive_sha256"] != records[b]["archive_sha256"]
        )
    report = {
        "schema_version": "sealsign-background-candidates-v1",
        "inputs": inputs,
        "parameters": PARAMETERS,
        "images": len(records),
        "pages_with_at_least_four_active_tiles": sum(len(x[2]) >= 4 for x in features),
        "common_buckets_ignored": ignored,
        "pairs_with_at_least_four_shared_tiles": compared,
        "candidate_pairs": len(pairs),
        "cross_archive_candidate_pairs": counts["cross_archive_pairs"],
        "pairs_reviewed": False,
        "independent_originals_proven": False,
        "accepted_for_training": False,
        "limitations": [
            "Aligned, sufficiently textured pages only; rotation, crops and scans can be missed.",
            "Source stamp boxes may be incomplete; signatures are not masked.",
            "Frequent tile buckets and low-ink pages are omitted, so this is not exhaustive.",
            "Matching templates can pass; candidates never establish original counts or groups.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent, prefix=".background-audit-") as temp:
        target = Path(temp) / "result"
        target.mkdir()
        with (target / "candidate-pairs.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(
                [
                    "archive_a",
                    "file_a",
                    "archive_b",
                    "file_b",
                    "shared_tiles",
                    "visible_pixels",
                    "close_fraction",
                    "ink_iou",
                    "review_status",
                ]
            )
            for a, b, shared, visible, close, iou in pairs:
                writer.writerow(
                    [
                        records[a]["archive"],
                        records[a]["file"],
                        records[b]["archive"],
                        records[b]["file"],
                        shared,
                        visible,
                        close,
                        iou,
                        "unreviewed",
                    ]
                )
        (target / "inventory.json").write_text(json.dumps(records, indent=2) + "\n")
        (target / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        shutil.move(str(target), output)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archives", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.archives, args.output)))


if __name__ == "__main__":
    main()
