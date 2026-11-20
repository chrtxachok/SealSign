"""An editor export is bound to its source and cannot bypass geometry/QC gates."""

import importlib.util
import json
from pathlib import Path

import pytest
from PIL import Image


def load(name):
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).parents[1] / f"scripts/{name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load("build_annotation_editor")
validator = load("validate_annotation_review")


def make_source(tmp_path):
    root = tmp_path / "bundle"
    root.mkdir()
    image = root / "page.png"
    Image.new("RGB", (100, 80), "white").save(image)
    page = {
        "page_id": "page-one",
        "normalized_path": "page.png",
        "exclusion_reason": None,
        "normalized_sha256": builder.sha256(image),
        "width": 100,
        "height": 80,
    }
    (root / "manifest.jsonl").write_text(json.dumps(page) + "\n")
    (root / "annotations.json").write_text(
        json.dumps(
            {
                "images": [
                    {
                        "id": 1,
                        "page_id": "page-one",
                        "file_name": "page.png",
                        "width": 100,
                        "height": 80,
                    }
                ],
                "annotations": [],
            }
        )
    )
    review = {
        "schema_version": "sealsign-review-v1",
        "manifest_sha256": builder.sha256(root / "manifest.jsonl"),
        "annotations_sha256": builder.sha256(root / "annotations.json"),
        "reviewer": "fixture",
        "accepted_for_training": False,
        "pages": [
            {
                "page_id": "page-one",
                "image_sha256": page["normalized_sha256"],
                "width": 100,
                "height": 80,
                "review_status": "first_review",
                "stamp_checked": True,
                "signature_checked": True,
                "objects": [{"category_id": 1, "bbox": [10, 10, 30, 20]}],
            }
        ],
    }
    return root, review


def test_offline_editor_and_review(tmp_path):
    root, review = make_source(tmp_path)
    result = builder.build(root, tmp_path / "editor.html")
    assert result["pages"] == 1 and result["accepted_for_training"] is False
    assert "data:image/png;base64," in (tmp_path / "editor.html").read_text(encoding="utf-8")
    file = tmp_path / "review.json"
    file.write_text(json.dumps(review))
    assert validator.validate(root, file)["first_review_pages"] == 1
    with pytest.raises(ValueError, match="exists"):
        builder.build(root, tmp_path / "editor.html")


@pytest.mark.parametrize("kind", ["hash", "bbox", "flags", "missing"])
def test_invalid_export_rejected(tmp_path, kind):
    root, review = make_source(tmp_path)
    if kind == "hash":
        review["manifest_sha256"] = "wrong"
    if kind == "bbox":
        review["pages"][0]["objects"][0]["bbox"][2] = 1000
    if kind == "flags":
        review["pages"][0]["signature_checked"] = False
    if kind == "missing":
        review["pages"] = []
    file = tmp_path / "review.json"
    file.write_text(json.dumps(review))
    with pytest.raises(ValueError):
        validator.validate(root, file)
