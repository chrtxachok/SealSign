"""Apply validated edits to a separate research bundle without granting final QC."""

import argparse
import importlib.util
import json
import shutil
import tempfile
from collections import Counter
from pathlib import Path

from sealsign.data.geometry import to_yolo
from sealsign.data.importer import sha256
from sealsign.data.validator import validate_bundle


def apply(bundle, review, output):
    spec = importlib.util.spec_from_file_location(
        "review_validator", Path(__file__).with_name("validate_annotation_review.py")
    )
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    summary = validator.validate(bundle, review)
    if output.exists():
        raise ValueError("Output already exists")
    data = json.loads(review.read_text(encoding="utf-8"))
    original = json.loads((bundle / "annotations.json").read_text())
    records = [json.loads(line) for line in (bundle / "manifest.jsonl").read_text().splitlines()]
    edits = {page["page_id"]: page for page in data["pages"]}
    images = {im["page_id"]: im for im in original["images"]}
    objects = []
    for record in records:
        if record["page_id"] not in edits:
            continue
        edit = edits[record["page_id"]]
        record["annotation_version"] = "sealsign-data-v1+review-" + sha256(review)[:12]
        # First review still needs an independent second review; never label final QC here.
        record["review_status"] = "unreviewed"
        record["annotation_status"] = "present" if edit["objects"] else "empty_unreviewed"
        record["first_review"] = {
            "reviewer": data["reviewer"],
            "status": edit["review_status"],
            "stamp_checked": edit["stamp_checked"],
            "signature_checked": edit["signature_checked"],
            "note": edit.get("note", ""),
        }
        for obj in edit["objects"]:
            x, y, w, h = obj["bbox"]
            objects.append(
                {
                    "id": len(objects) + 1,
                    "image_id": images[record["page_id"]]["id"],
                    "category_id": obj["category_id"],
                    "bbox": [x, y, w, h],
                    "area": w * h,
                    "iscrowd": 0,
                }
            )
    previous = len(original["annotations"])
    original["annotations"] = objects
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent, prefix=".review-") as temp:
        target = Path(temp) / "bundle"
        shutil.copytree(bundle, target)
        shutil.rmtree(target / "previews")
        (target / "previews").mkdir()
        (target / "annotations.json").write_text(
            json.dumps(original, ensure_ascii=False, indent=2) + "\n"
        )
        (target / "manifest.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)
        )
        for page_id, edit in edits.items():
            im = images[page_id]
            (target / "unreviewed-yolo" / f"{page_id}.txt").write_text(
                to_yolo(edit["objects"], im["width"], im["height"])
            )
        if (target / "review-source.json").exists():
            history = target / "review-history"
            history.mkdir(exist_ok=True)
            previous_review = target / "review-source.json"
            shutil.copy2(previous_review, history / (sha256(previous_review) + ".json"))
        shutil.copy2(review, target / "review-source.json")
        report = json.loads((target / "report.json").read_text())
        report.update(
            objects_by_class=dict(Counter(str(o["category_id"]) for o in objects)),
            annotation_status_counts=dict(Counter(r["annotation_status"] for r in records)),
            review_export_sha256=sha256(review),
            accepted_for_training=False,
        )
        (target / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        result = {
            **summary,
            "previous_objects": previous,
            "review_sha256": sha256(review),
            "source_annotations_sha256": sha256(bundle / "annotations.json"),
            "output_annotations_sha256": sha256(target / "annotations.json"),
        }
        (target / "review-application.json").write_text(json.dumps(result, indent=2) + "\n")
        validate_bundle(target)
        target.rename(output)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("bundle", type=Path)
    p.add_argument("review", type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    print(json.dumps(apply(a.bundle, a.review, a.output)))


if __name__ == "__main__":
    main()
