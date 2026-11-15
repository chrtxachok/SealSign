"""Leakage checks must find exact cross-split copies without accepting candidates."""

import importlib.util
import json
from pathlib import Path

import pytest
from PIL import Image

spec = importlib.util.spec_from_file_location(
    "leakage", Path(__file__).parents[1] / "scripts/audit_leakage.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def make_bundle(tmp_path):
    root = tmp_path / "bundle"
    root.mkdir()
    pages = []
    for number, split in enumerate(["train", "valid", "train"]):
        path = root / f"{number}.png"
        Image.new("RGB", (15, 15), ("white" if number != 2 else "black")).save(path)
        digest = module.sha256(path)
        pages.append(
            {
                "page_id": str(number),
                "archive_id": "example",
                "sha256": digest,
                "normalized_sha256": digest,
                "normalized_path": path.name,
                "relative_path": f"{number}.png",
                "original_split": split,
                "exclusion_reason": None,
            }
        )
    (root / "manifest.jsonl").write_text("".join(json.dumps(p) + "\n" for p in pages))
    (root / "annotations.json").write_text("{}")
    return root


def test_exact_duplicate_crosses_split(tmp_path):
    bundle = make_bundle(tmp_path)
    out = tmp_path / "out"
    report = module.audit([bundle], out)
    assert report["counts"]["exact_cross_split_pairs"] == 1
    assert report["accepted_for_training"] is False
    assert report["near_duplicate_reviewed"] is False
    assert "page_id_a,page_id_b" in (out / "candidate-pairs.csv").read_text()
    with pytest.raises(ValueError, match="already exists"):
        module.audit([bundle], out)


def test_modified_image_fails_without_output(tmp_path):
    bundle = make_bundle(tmp_path)
    (bundle / "0.png").write_bytes(b"changed")
    with pytest.raises(ValueError, match="checksum"):
        module.audit([bundle], tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_valid_and_val_are_same_upstream_split(tmp_path):
    bundle = make_bundle(tmp_path)
    manifest = bundle / "manifest.jsonl"
    pages = [json.loads(line) for line in manifest.read_text().splitlines()]
    pages[0]["original_split"] = "valid"
    pages[1]["original_split"] = "val"
    manifest.write_text("".join(json.dumps(p) + "\n" for p in pages))
    report = module.audit([bundle], tmp_path / "out")
    assert report["counts"].get("exact_cross_split_pairs", 0) == 0
