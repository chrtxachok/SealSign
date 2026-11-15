"""Pixel audit verifies source checksums and never marks candidates reviewed."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from PIL import Image

spec = importlib.util.spec_from_file_location(
    "green_audit", Path(__file__).parents[1] / "scripts/audit_green_pixels.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def make_bundle(tmp_path):
    root = tmp_path / "bundle"
    root.mkdir()
    pages = []
    for idx, color in enumerate(("green", "white")):
        path = root / f"{idx}.png"
        Image.new("RGB", (10, 10), color).save(path)
        pages.append(
            {
                "page_id": str(idx),
                "normalized_path": path.name,
                "normalized_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "source_images_root": "stamps/train/images",
            }
        )
    (root / "manifest.jsonl").write_text("".join(json.dumps(p) + "\n" for p in pages))
    return root


def test_green_candidate_is_not_an_approval(tmp_path):
    root = make_bundle(tmp_path)
    # CSS green is (0,128,0), below the deliberately narrow threshold.
    Image.new("RGB", (10, 10), (0, 255, 0)).save(root / "0.png")
    pages = [json.loads(line) for line in (root / "manifest.jsonl").read_text().splitlines()]
    pages[0]["normalized_sha256"] = hashlib.sha256((root / "0.png").read_bytes()).hexdigest()
    (root / "manifest.jsonl").write_text("".join(json.dumps(p) + "\n" for p in pages))
    report = module.audit(root, tmp_path / "out")
    assert report["images"] == 2 and report["candidates"] == 1
    assert report["candidate_is_not_verified_annotation"] is True
    assert report["accepted_for_training"] is False


def test_changed_image_is_rejected(tmp_path):
    root = make_bundle(tmp_path)
    (root / "0.png").write_bytes(b"changed")
    with pytest.raises(ValueError, match="checksum"):
        module.audit(root, tmp_path / "out")
    assert not (tmp_path / "out").exists()
