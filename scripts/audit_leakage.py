"""Research-only duplicate audit. Similarity candidates require human review."""

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path, PurePosixPath

from PIL import Image, ImageOps


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def dhash(image):
    image = ImageOps.grayscale(image).resize((9, 8), Image.Resampling.LANCZOS)
    pixels = list(image.get_flattened_data())
    result = 0
    for row in range(8):
        for col in range(8):
            result = (result << 1) | (pixels[row * 9 + col] > pixels[row * 9 + col + 1])
    return result


def audit(bundles, output, threshold=2):
    if not 0 <= threshold <= 4:
        raise ValueError("Hamming threshold must be in 0..4")
    if output.exists():
        raise ValueError("Output already exists")
    pages, ids, inputs = [], set(), []
    for bundle in bundles:
        root = bundle.resolve()
        manifest, annotations = root / "manifest.jsonl", root / "annotations.json"
        inputs.append(
            {
                "bundle": bundle.name,
                "manifest_sha256": sha256(manifest),
                "annotations_sha256": sha256(annotations),
            }
        )
        for line in manifest.read_text(encoding="utf-8").splitlines():
            page = json.loads(line)
            if page["page_id"] in ids:
                raise ValueError("Repeated page_id across bundles")
            ids.add(page["page_id"])
            if not page.get("normalized_path") or page.get("exclusion_reason"):
                continue
            path = (root / page["normalized_path"]).resolve()
            if not path.is_relative_to(root) or sha256(path) != page["normalized_sha256"]:
                raise ValueError("Image path or checksum mismatch")
            with Image.open(path) as image:
                image.load()
                fingerprint = dhash(image)
            name = PurePosixPath(page["relative_path"]).name.split(".rf.")[0]
            pages.append(
                {
                    "id": page["page_id"],
                    "archive": page["archive_id"],
                    "source_sha256": page["sha256"],
                    "normalized_sha256": page["normalized_sha256"],
                    "name_prefix": name,
                    "original_split": page.get("original_split") or "unknown",
                    "split_group": "val"
                    if page.get("original_split") == "valid"
                    else page.get("original_split") or "unknown",
                    "dhash": fingerprint,
                }
            )
    pages.sort(key=lambda x: x["id"])
    exact = defaultdict(list)
    prefixes = defaultdict(list)
    for page in pages:
        if page["source_sha256"]:
            exact[page["source_sha256"]].append(page)
        # Prefixes have meaning only within the same source archive.
        prefixes[(page["archive"], page["name_prefix"])].append(page)
    pairs = []
    counts = Counter()
    for a, b in combinations(pages, 2):
        # Only examine cross-source or cross-upstream-split pairs; within-split
        # similarity is not needed to detect an existing partition crossing.
        if a["archive"] == b["archive"] and a["split_group"] == b["split_group"]:
            continue
        distance = (a["dhash"] ^ b["dhash"]).bit_count()
        same_bytes = bool(a["source_sha256"]) and a["source_sha256"] == b["source_sha256"]
        same_name = a["archive"] == b["archive"] and a["name_prefix"] == b["name_prefix"]
        same_normalized = a["normalized_sha256"] == b["normalized_sha256"]
        if same_bytes or same_normalized or same_name or distance <= threshold:
            counts["exact_pairs"] += same_bytes
            counts["same_prefix_pairs"] += same_name
            counts["same_normalized_pairs"] += same_normalized
            counts["dhash_candidate_pairs"] += distance <= threshold
            if same_bytes and a["archive"] == b["archive"]:
                counts["exact_cross_split_pairs"] += 1
            if same_name:
                counts["prefix_cross_split_pairs"] += 1
            if a["archive"] != b["archive"]:
                counts["cross_source_candidate_pairs"] += 1
            pairs.append(
                {
                    "page_id_a": a["id"],
                    "page_id_b": b["id"],
                    "archive_a": a["archive"],
                    "archive_b": b["archive"],
                    "original_split_a": a["original_split"],
                    "original_split_b": b["original_split"],
                    "same_source_bytes": same_bytes,
                    "same_normalized_bytes": same_normalized,
                    "same_name_prefix": same_name,
                    "dhash_distance": distance,
                    "review_status": "unreviewed",
                }
            )
    report = {
        "schema_version": "sealsign-leakage-audit-v1",
        "inputs": inputs,
        "pages_examined": len(pages),
        "source_exact_duplicate_groups": sum(len(v) > 1 for v in exact.values()),
        "same_archive_prefix_groups": sum(len(v) > 1 for v in prefixes.values()),
        "threshold": threshold,
        "candidate_pairs": len(pairs),
        "counts": dict(counts),
        "near_duplicate_reviewed": False,
        "accepted_for_training": False,
    }
    output.mkdir(parents=True)
    try:
        with (output / "candidate-pairs.csv").open("w", encoding="utf-8", newline="") as stream:
            fields = [
                "page_id_a",
                "page_id_b",
                "archive_a",
                "archive_b",
                "original_split_a",
                "original_split_b",
                "same_source_bytes",
                "same_normalized_bytes",
                "same_name_prefix",
                "dhash_distance",
                "review_status",
            ]
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(pairs)
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except Exception:
        import shutil

        shutil.rmtree(output)
        raise
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundles", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--threshold", type=int, default=2)
    args = parser.parse_args()
    print(json.dumps(audit(args.bundles, args.output, args.threshold)))


if __name__ == "__main__":
    main()
