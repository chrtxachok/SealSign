"""Report the state of local research bundles without promoting their QC status."""

import importlib.util
import json
from collections import Counter
from pathlib import Path

from sealsign.data.importer import sha256
from sealsign.data.validator import validate_bundle

BUNDLES = {
    "mapo80_pilot50": Path("artifacts/data-import/mapo80-pilot50-user-final-v5"),
    "mapo80_batch001": Path("artifacts/annotation-batches/batch-001-agent-v6"),
    "doclaynet_001": Path("artifacts/data-import/doclaynet-pilot12-v1/first-reviewed-bundle"),
    "doclaynet_002": Path("artifacts/data-import/doclaynet-pilot-next12-v1/first-reviewed-bundle"),
    **{
        f"doclaynet_{name}": Path(
            f"artifacts/data-import/doclaynet-pilot-{name}-v1/first-reviewed-bundle"
        )
        for name in ("024-035", "036-047", "048-059", "060-071", "072-083", "084-100")
    },
}


def inspect_bundle(path):
    result = validate_bundle(path)
    pages = [json.loads(line) for line in (path / "manifest.jsonl").read_text().splitlines()]
    coco = json.loads((path / "annotations.json").read_text())
    first = sum(page.get("first_review", {}).get("status") == "first_review" for page in pages)
    classes = Counter(str(item["category_id"]) for item in coco["annotations"])
    groups_assigned = sum(bool(page.get("group_id")) for page in pages)
    return {
        "pages": result["pages"],
        "first_review_pages": first,
        "canonical_review_status_counts": dict(Counter(p["review_status"] for p in pages)),
        "annotation_boxes_by_class": dict(classes),
        "pages_with_group_id": groups_assigned,
        "manifest_sha256": sha256(path / "manifest.jsonl"),
        "annotations_sha256": sha256(path / "annotations.json"),
        "accepted_for_training": False,
    }


def main():
    report = {
        "schema_version": "sealsign-training-readiness-v1",
        "bundles": {name: inspect_bundle(path) for name, path in BUNDLES.items()},
        "python_packages_available": {
            name: importlib.util.find_spec(name) is not None
            for name in ("torch", "torchvision", "ultralytics")
        },
        "interpretation": (
            "Bundle counts may overlap and do not establish unique or accepted pages."
        ),
        "accepted_for_training": False,
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
