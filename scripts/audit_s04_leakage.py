"""Find exact decoded and perceptually similar pages for local adjudication."""

import argparse
import hashlib
import io
import json
from collections import Counter
from contextlib import ExitStack
from itertools import combinations
from pathlib import Path
from zipfile import ZipFile

from PIL import Image, ImageOps

from scripts.audit_leakage import dhash

QC = Path("artifacts/data-qc")
REVIEW = QC / "s04-3000-review-v2"
MERGED = REVIEW / "merged-first-review-v1.json"
HOLDOUT_SPLIT = QC / "s04-teaching-v1/split.json"
HOLDOUT_MANIFEST = Path("artifacts/annotation-batches/batch-001-agent-v7/manifest.jsonl")
ARCHIVES = Path("artifacts/data-audit/mapo80")
THRESHOLD = 6


def fingerprint(archive, row):
    raw = archive.read(row["file"])
    source_hash = hashlib.sha256(raw).hexdigest()
    if source_hash != row["sha256"]:
        raise ValueError(f"Source checksum mismatch for {row['id']}")
    with Image.open(io.BytesIO(raw)) as original:
        rgb = ImageOps.exif_transpose(original).convert("RGB")
    pixels = hashlib.sha256(f"{rgb.width}x{rgb.height}:".encode())
    pixels.update(rgb.tobytes())
    return (
        source_hash,
        pixels.hexdigest(),
        dhash(rgb),
        dhash(rgb.transpose(Image.Transpose.TRANSPOSE)),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists")

    cohort = [
        {**row, "id": row["queue_index"], "holdout": False}
        for row in json.loads(MERGED.read_bytes())["pages"]
    ]
    holdout_ids = {
        p for group in json.loads(HOLDOUT_SPLIT.read_bytes())["splits"]["test"] for p in group
    }
    for line in HOLDOUT_MANIFEST.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["page_id"] in holdout_ids:
            cohort.append(
                {
                    "id": row["page_id"],
                    "archive": f"{row['original_split']}.zip",
                    "file": row["relative_path"],
                    "sha256": row["sha256"],
                    "holdout": True,
                }
            )
    if {row["id"] for row in cohort if row["holdout"]} != holdout_ids:
        raise ValueError("Teaching test incomplete")
    with ExitStack() as stack:
        archives = {
            name: stack.enter_context(ZipFile(ARCHIVES / name))
            for name in sorted({row["archive"] for row in cohort})
        }
        for row in cohort:
            row["fingerprint"] = fingerprint(archives[row["archive"]], row)

    pairs = []
    counts = Counter()
    for a, b in combinations(cohort, 2):
        if a["holdout"] and b["holdout"]:
            continue
        a_raw, a_pix, a_h, a_v = a["fingerprint"]
        b_raw, b_pix, b_h, b_v = b["fingerprint"]
        distance = (a_h ^ b_h).bit_count() + (a_v ^ b_v).bit_count()
        exact_bytes = a_raw == b_raw
        exact_pixels = a_pix == b_pix
        if exact_bytes or exact_pixels or distance <= THRESHOLD:
            pairs.append(
                {
                    "a": a["id"],
                    "b": b["id"],
                    "teaching_test": b["holdout"],
                    "same_source_bytes": exact_bytes,
                    "same_rgb_pixels": exact_pixels,
                    "dhash_distance": distance,
                }
            )
            counts["candidate_pairs"] += 1
            counts["cross_teaching_test_candidates"] += b["holdout"]
            counts["exact_source_pairs"] += exact_bytes
            counts["exact_rgb_pairs"] += exact_pixels
    result = {
        "schema_version": "sealsign-additional-leakage-audit-v1",
        "input_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (MERGED, HOLDOUT_SPLIT, HOLDOUT_MANIFEST)
        },
        "candidate_pages": len(cohort) - len(holdout_ids),
        "teaching_test_pages": len(holdout_ids),
        "horizontal_vertical_dhash_threshold": THRESHOLD,
        "counts": dict(counts),
        "pairs": pairs,
    }
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(result["counts"]))


if __name__ == "__main__":
    main()
