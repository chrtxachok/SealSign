"""Аудит метаданных зеркала SignverOD; изображения и лицензия не проверяются."""

import argparse
import ast
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

REPOSITORY = "mk-chang/SignverOD_Datset"
REVISION = "c24bbbcc079138b9740cdc8f3afaed37c6ff5b0a"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def audit(directory: Path) -> dict:
    tree = json.loads((directory / "tree.json").read_text(encoding="utf-8"))
    if tree.get("truncated") is not False or tree.get("sha") != REVISION:
        raise ValueError("Нужен полный Git tree зафиксированной ревизии")
    image_blobs = [
        item
        for item in tree["tree"]
        if item["type"] == "blob"
        and item["path"].startswith("images/")
        and Path(item["path"]).suffix.lower() in {".png", ".jpg", ".jpeg"}
    ]
    blob_counts = Counter(item["sha"] for item in image_blobs)
    images = read_csv(directory / "image_ids.csv")
    categories = {row["id"]: row["name"] for row in read_csv(directory / "categories.csv")}
    image_index = defaultdict(list)
    for image in images:
        image_index[image["id"]].append(image)
    splits = {}
    split_ids = {}
    for split in ("train", "test"):
        rows = read_csv(directory / f"{split}.csv")
        split_ids[split] = {row["image_id"] for row in rows}
        invalid_geometry = unknown_classes = 0
        for row in rows:
            unknown_classes += row["category_id"] not in categories
            try:
                x, y, width, height = ast.literal_eval(row["bbox"])
                valid = all(math.isfinite(v) for v in (x, y, width, height))
                valid = valid and x >= 0 and y >= 0 and width > 0 and height > 0
                valid = valid and x + width <= 1.000001 and y + height <= 1.000001
            except (ValueError, TypeError, SyntaxError):
                valid = False
            invalid_geometry += not valid
        splits[split] = {
            "annotation_rows": len(rows),
            "distinct_image_id_values": len(split_ids[split]),
            "category_rows": dict(sorted(Counter(row["category_id"] for row in rows).items())),
            "rows_with_unknown_image_id": sum(row["image_id"] not in image_index for row in rows),
            "rows_with_ambiguous_image_id": sum(
                len(image_index[row["image_id"]]) > 1 for row in rows
            ),
            "duplicate_annotation_id_excess": len(rows) - len({row["id"] for row in rows}),
            "invalid_normalized_xywh_rows": invalid_geometry,
            "unknown_class_rows": unknown_classes,
        }
    inputs = {}
    for name in ("categories.csv", "image_ids.csv", "train.csv", "test.csv", "labelmap.txt"):
        data = (directory / name).read_bytes()
        inputs[name] = {
            "url": f"https://raw.githubusercontent.com/{REPOSITORY}/{REVISION}/{name}",
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
    return {
        "audit_date": "2026-11-06",
        "repository": REPOSITORY,
        "revision": REVISION,
        "scope": "metadata_only_no_image_decode_no_visual_qc",
        "accepted_for_training": False,
        "minimum_original_pages": 5000,
        "git_tree": {
            "url": f"https://api.github.com/repos/{REPOSITORY}/git/trees/{REVISION}?recursive=1",
            "image_files": len(image_blobs),
            "distinct_git_blob_ids": len(blob_counts),
            "byte_identical_duplicate_excess": len(image_blobs) - len(blob_counts),
            "byte_identical_duplicate_groups": sum(count > 1 for count in blob_counts.values()),
            "image_bytes": sum(item["size"] for item in image_blobs),
        },
        "image_metadata": {
            "rows": len(images),
            "distinct_id_values": len(image_index),
            "ambiguous_id_values": sum(len(value) > 1 for value in image_index.values()),
            "distinct_filenames": len({row["file_name"] for row in images}),
        },
        "categories": categories,
        "splits": splits,
        "cross_split_image_id_value_overlap": len(split_ids["train"] & split_ids["test"]),
        "overlap_interpretation": "ID collisions prevent treating this as confirmed page leakage",
        "inputs": inputs,
        "blockers": [
            "below_5000_even_before_decoding_and_near_duplicate_review",
            "no_stamp_category",
            "ambiguous_image_ids_require_upstream_source_namespaces",
            "primary_dataset_license_not_yet_verified",
            "images_not_downloaded_or_reviewed",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.directory)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Аудит записан: {args.output}; accepted_for_training=false")


if __name__ == "__main__":
    main()
