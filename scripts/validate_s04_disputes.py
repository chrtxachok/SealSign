"""Validate incremental S04 adjudication against the merged first pass."""

import argparse
import hashlib
import json
import math
from pathlib import Path


def validate_bbox(bbox, width, height):
    if not isinstance(bbox, list) or len(bbox) != 4:
        raise ValueError("Expected a bbox with four coordinates")
    if any(type(value) not in (int, float) or not math.isfinite(value) for value in bbox):
        raise ValueError("Invalid bbox coordinate")
    x, y, w, h = bbox
    if not (0 <= x < x + w <= width and 0 <= y < y + h <= height):
        raise ValueError("BBox exceeds the EXIF-normalized image bounds")


def validate_class(category):
    if type(category) is not int or category not in (0, 1):
        raise ValueError("Expected category 0 (stamp) or 1 (signature)")


def validate_page_decisions(review, original):
    regions = review["regions"]
    if [region["bbox"] for region in regions] != [
        region["bbox"] for region in original["disputed_regions"]
    ]:
        raise ValueError("Reviewed bbox list differs from the original disputed bbox list")

    width, height = original["width"], original["height"]
    for region in regions:
        decision = region["decision"]
        if decision not in ("accept", "reject", "unresolved"):
            raise ValueError(f"Unknown decision: {decision!r}")
        if not isinstance(region["reason"], str) or not region["reason"].strip():
            raise ValueError("Missing reason for region decision")
        if decision == "accept":
            validate_class(region["category_id"])
            validate_bbox(region.get("replacement_bbox", region["bbox"]), width, height)
        elif "category_id" in region or "replacement_bbox" in region:
            raise ValueError("Only accepted regions can set class or replacement bbox")

    for annotation in review.get("additional_annotations", []):
        validate_class(annotation["category_id"])
        validate_bbox(annotation["bbox"], width, height)


def load_dispute_decisions(merged_path, decisions_dir):
    merged_raw = merged_path.read_bytes()
    merged_sha256 = hashlib.sha256(merged_raw).hexdigest()
    pages = json.loads(merged_raw)["pages"]
    if [page["queue_index"] for page in pages] != list(range(1, 3001)):
        raise ValueError("Merged first pass must contain positions 1 through 3000 in order")
    disputed = {page["queue_index"]: page for page in pages if page["review_status"] == "disputed"}
    reviewed = {}
    input_sha256 = {}
    for path in sorted(decisions_dir.glob("qc-decisions-*.json")):
        raw = path.read_bytes()
        batch = json.loads(raw)
        if batch["schema_version"] != "sealsign-dispute-review-v1":
            raise ValueError(f"{path.name}: unexpected review schema")
        if batch["merged_sha256"] != merged_sha256:
            raise ValueError(f"{path.name}: merged first-pass checksum mismatch")
        if not isinstance(batch["reviewer"], str) or not batch["reviewer"].strip():
            raise ValueError(f"{path.name}: missing reviewer")
        for review in batch["pages"]:
            index = review["queue_index"]
            if type(index) is not int or index not in disputed or index in reviewed:
                raise ValueError(f"{path.name}: unexpected or repeated position {index!r}")
            try:
                validate_page_decisions(review, disputed[index])
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(f"{path.name}, position {index}: {error}") from error
            reviewed[index] = review
        input_sha256[path.name] = hashlib.sha256(raw).hexdigest()

    open_positions = sorted(disputed.keys() - reviewed.keys())
    unresolved = [
        index
        for index, review in reviewed.items()
        if any(region["decision"] == "unresolved" for region in review["regions"])
    ]
    summary = {
        "merged_sha256": merged_sha256,
        "batch_sha256": input_sha256,
        "first_pass_pages": len(pages),
        "disputed_pages": len(disputed),
        "adjudicated_pages": len(reviewed),
        "fully_resolved_pages": len(reviewed) - len(unresolved),
        "still_unresolved_pages": len(unresolved),
        "not_yet_adjudicated_pages": len(open_positions),
        "next_queue_index": open_positions[0] if open_positions else None,
    }
    return reviewed, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--merged", type=Path, required=True)
    parser.add_argument("--decisions-dir", type=Path, required=True)
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    _, summary = load_dispute_decisions(args.merged, args.decisions_dir)
    print(json.dumps(summary, indent=2))
    if args.require_complete and summary["not_yet_adjudicated_pages"]:
        parser.exit(status=1, message="Some disputed pages still await adjudication\n")


if __name__ == "__main__":
    main()
