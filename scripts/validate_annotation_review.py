"""Verify an editor export against its immutable pilot; do not apply or approve it."""

import argparse
import json
import math
from pathlib import Path

from sealsign.data.importer import sha256


def validate(bundle, review):
    data = json.loads(review.read_text(encoding="utf-8"))
    if (
        data.get("schema_version") != "sealsign-review-v1"
        or data.get("manifest_sha256") != sha256(bundle / "manifest.jsonl")
        or data.get("annotations_sha256") != sha256(bundle / "annotations.json")
        or data.get("accepted_for_training") is not False
    ):
        raise ValueError("Wrong source or review schema")
    if not isinstance(data.get("reviewer"), str):
        raise ValueError("Missing reviewer")
    pages = {
        p["page_id"]: p
        for p in map(json.loads, (bundle / "manifest.jsonl").read_text().splitlines())
        if p.get("normalized_path") and not p.get("exclusion_reason")
    }
    seen = set()
    reviewed, objects = 0, 0
    for page in data["pages"]:
        identifier = page["page_id"]
        if identifier not in pages or identifier in seen:
            raise ValueError("Unknown or repeated page")
        seen.add(identifier)
        source = pages[identifier]
        if page["image_sha256"] != source["normalized_sha256"] or (
            page["width"],
            page["height"],
        ) != (source["width"], source["height"]):
            raise ValueError("Image identity mismatch")
        if page["review_status"] not in {"unreviewed", "first_review"}:
            raise ValueError("Unsupported review status")
        if type(page["stamp_checked"]) is not bool or type(page["signature_checked"]) is not bool:
            raise ValueError("Invalid class review flags")
        if page["review_status"] == "first_review":
            if (
                not data["reviewer"].strip()
                or not page["stamp_checked"]
                or not page["signature_checked"]
            ):
                raise ValueError("Incomplete class review")
            reviewed += 1
        boxes = set()
        for obj in page["objects"]:
            if type(obj["category_id"]) is not int or obj["category_id"] not in {0, 1}:
                raise ValueError("Invalid class")
            bbox = obj["bbox"]
            if len(bbox) != 4 or not all(
                type(v) in (int, float) and math.isfinite(v) for v in bbox
            ):
                raise ValueError("Invalid bbox")
            x, y, w, h = bbox
            if (
                x < 0
                or y < 0
                or min(w, h) <= 0
                or x + w > source["width"] + 1e-7
                or y + h > source["height"] + 1e-7
            ):
                raise ValueError("Out-of-bounds bbox")
            key = (obj["category_id"], *bbox)
            if key in boxes:
                raise ValueError("Duplicate bbox")
            boxes.add(key)
            objects += 1
    if seen != set(pages):
        raise ValueError("Missing pilot pages")
    return {
        "pages": len(seen),
        "first_review_pages": reviewed,
        "objects": objects,
        "accepted_for_training": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("review", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.bundle, args.review)))


if __name__ == "__main__":
    main()
