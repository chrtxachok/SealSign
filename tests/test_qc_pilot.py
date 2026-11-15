"""Pilot selection preserves the test holdout and stays reproducible."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from PIL import Image

spec = importlib.util.spec_from_file_location(
    "qc_pilot", Path(__file__).parents[1] / "scripts/prepare_qc_pilot.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def bundle(tmp_path):
    root = tmp_path / "bundle"
    (root / "images").mkdir(parents=True)
    pages, images = [], []
    for i, split in enumerate(["train", "train", "test"]):
        path = root / "images" / f"{i}.png"
        Image.new("RGB", (12, 12), (i, 0, 0)).save(path)
        checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        page_id = str(i)
        images.append({"id": i, "page_id": page_id, "file_name": f"images/{i}.png"})
        pages.append(
            {
                "page_id": page_id,
                "original_split": split,
                "normalized_path": f"images/{i}.png",
                "normalized_sha256": checksum,
                "sha256": checksum,
                "review_status": "unreviewed",
                "exclusion_reason": None,
                "relative_path": f"{i}.png",
            }
        )
    (root / "manifest.jsonl").write_text("".join(json.dumps(p) + "\n" for p in pages))
    (root / "annotations.json").write_text(json.dumps({"images": images, "annotations": []}))
    return root


def test_pilot_excludes_test_and_is_repeatable(tmp_path):
    source = bundle(tmp_path)
    module.prepare(source, tmp_path / "first", 2, 42)
    module.prepare(source, tmp_path / "second", 2, 42)
    a = json.loads((tmp_path / "first/pilot.json").read_text())
    b = json.loads((tmp_path / "second/pilot.json").read_text())
    assert a == b
    assert set(a["page_ids"]) == {"0", "1"}
    assert a["reviewed"] is False and a["accepted_for_training"] is False
    with pytest.raises(ValueError, match="Not enough"):
        module.prepare(source, tmp_path / "too-large", 3, 42)


def test_pilot_rejects_changed_image_and_cleans_up(tmp_path):
    source = bundle(tmp_path)
    (source / "images/0.png").write_bytes(b"changed")
    with pytest.raises(ValueError, match="checksum"):
        module.prepare(source, tmp_path / "invalid", 2, 42)
    assert not (tmp_path / "invalid").exists()
