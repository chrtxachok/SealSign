"""Applying review edits preserves the source and cannot grant final QC."""

import importlib.util
import io
import json
import zipfile
from pathlib import Path

import pytest
from PIL import Image

from sealsign.data.importer import import_zip, sha256
from sealsign.data.validator import validate_bundle

spec = importlib.util.spec_from_file_location(
    "apply_review", Path(__file__).parents[1] / "scripts/apply_annotation_review.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_apply_edits_keeps_source_and_unreviewed_state(tmp_path):
    raw = io.BytesIO()
    Image.new("RGB", (100, 100), "white").save(raw, format="PNG")
    archive = tmp_path / "source.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("images/train/a.png", raw.getvalue())
        z.writestr("labels/train/a.txt", "0 .5 .5 .2 .2")
    root = tmp_path / "bundle"
    import_zip(
        archive,
        {
            "archive_id": "fixture",
            "sha256": sha256(archive),
            "sources": [
                {
                    "images": "images/train",
                    "labels": "labels/train",
                    "format": "bbox",
                    "class_map": {"0": 0},
                    "original_split": "train",
                }
            ],
        },
        root,
    )
    source_hash = sha256(root / "annotations.json")
    page = json.loads((root / "manifest.jsonl").read_text())
    data = {
        "schema_version": "sealsign-review-v1",
        "manifest_sha256": sha256(root / "manifest.jsonl"),
        "annotations_sha256": source_hash,
        "reviewer": "fixture",
        "accepted_for_training": False,
        "pages": [
            {
                "page_id": page["page_id"],
                "image_sha256": page["normalized_sha256"],
                "width": 100,
                "height": 100,
                "review_status": "unreviewed",
                "stamp_checked": False,
                "signature_checked": False,
                "objects": [{"category_id": 1, "bbox": [10, 20, 30, 40]}],
            }
        ],
    }
    review = tmp_path / "review.json"
    review.write_text(json.dumps(data))
    out = tmp_path / "edited"
    report = module.apply(root, review, out)
    assert report["first_review_pages"] == 0
    assert sha256(root / "annotations.json") == source_hash
    assert validate_bundle(out)["annotations"] == 1
    edited = json.loads((out / "manifest.jsonl").read_text())
    assert edited["review_status"] == "unreviewed"
    assert json.loads((out / "report.json").read_text())["objects_by_class"] == {"1": 1}
    with pytest.raises(ValueError, match="exists"):
        module.apply(root, review, out)

    data["manifest_sha256"] = sha256(out / "manifest.jsonl")
    data["annotations_sha256"] = sha256(out / "annotations.json")
    original_review_hash = sha256(review)
    review.write_text(json.dumps(data))
    third = tmp_path / "third"
    module.apply(out, review, third)
    assert (third / "review-history" / f"{original_review_hash}.json").is_file()
