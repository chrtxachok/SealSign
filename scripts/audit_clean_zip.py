"""Audit candidate ZIPs; structural checks do not establish full two-class QC."""

import argparse
import hashlib
import io
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

from PIL import Image, ImageChops

from sealsign.data.geometry import parse_labels
from sealsign.data.importer import sha256, zip_inventory


def audit(archives, output):
    report = {
        "accepted_for_training": False,
        "archives": [],
        "visual_qc_complete": False,
        "signature_annotations_verified": False,
    }
    hashes = defaultdict(list)
    for path in archives:
        counts = Counter()
        errors = Counter()
        with zipfile.ZipFile(path) as archive:
            entries = zip_inventory(archive)
            bad = archive.testzip()
            if bad:
                raise ValueError("ZIP CRC failure")
            names = sorted(
                n for n in entries if PurePosixPath(n).suffix.lower() in {".jpg", ".jpeg", ".png"}
            )
            labels = set()
            for name in names:
                if entries[name].file_size > 64 * 1024**2:
                    raise ValueError("Image exceeds byte budget")
                raw = archive.read(name)
                digest = hashlib.sha256(raw).hexdigest()
                hashes[digest].append(path.name)
                counts["images"] += 1
                parts = list(PurePosixPath(name).parts)
                if "images" not in parts:
                    raise ValueError("Unexpected image layout")
                parts[parts.index("images")] = "labels"
                label = str(PurePosixPath(*parts).with_suffix(".txt"))
                labels.add(label)
                try:
                    with Image.open(io.BytesIO(raw)) as image:
                        if image.width * image.height > 50_000_000:
                            raise ValueError("Image exceeds pixel budget")
                        image.load()
                        if image.getexif().get(274, 1) != 1:
                            raise ValueError("EXIF requires source coordinate review")
                        red, green, blue = image.convert("RGB").split()
                        mask = ImageChops.multiply(
                            ImageChops.multiply(
                                red.point(lambda v: 255 if v <= 40 else 0),
                                green.point(lambda v: 255 if v >= 200 else 0),
                            ),
                            blue.point(lambda v: 255 if v <= 40 else 0),
                        )
                        counts["bright_green_candidates"] += mask.histogram()[255] >= 30
                        counts["decoded"] += 1
                        if label not in entries:
                            counts["missing_labels"] += 1
                            continue
                        if entries[label].file_size > 4 * 1024**2:
                            raise ValueError("Label exceeds budget")
                        text = archive.read(label).decode("utf-8")
                        counts["label_rows"] += len(
                            [line for line in text.splitlines() if line.strip()]
                        )
                        counts["empty_unreviewed_labels"] += not text.strip()
                        objects = parse_labels(text, "bbox", {"0": 0}, image.width, image.height)
                        counts["valid_label_pages"] += 1
                        counts["valid_stamp_boxes"] += len(objects)
                except (ValueError, OSError, UnicodeError) as error:
                    errors[str(error)] += 1
            counts["orphan_labels"] = sum(
                n.endswith(".txt") and "labels" in PurePosixPath(n).parts and n not in labels
                for n in entries
            )
            report["archives"].append(
                {
                    "filename": path.name,
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                    "zip_crc_verified": True,
                    "counts": dict(counts),
                    "errors": dict(errors),
                }
            )
    report["distinct_source_sha256"] = len(hashes)
    report["exact_duplicate_groups"] = sum(len(v) > 1 for v in hashes.values())
    report["exact_duplicate_groups_crossing_archives"] = sum(
        len(set(v)) > 1 for v in hashes.values()
    )
    report["green_rule"] = "at least 30 pixels with R<=40 G>=200 B<=40; candidate only"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archives", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.archives, args.output)))


if __name__ == "__main__":
    main()
