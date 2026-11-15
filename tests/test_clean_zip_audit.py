"""Candidate audit distinguishes valid stamps from accepted two-class data."""

import importlib.util
import io
import zipfile
from pathlib import Path

from PIL import Image

spec = importlib.util.spec_from_file_location(
    "clean_zip", Path(__file__).parents[1] / "scripts/audit_clean_zip.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_duplicates_and_invalid_labels_are_reported(tmp_path):
    image = io.BytesIO()
    Image.new("RGB", (20, 30), "white").save(image, format="PNG")
    archives = []
    for split, label in [("train", "0 .5 .5 .2 .2"), ("val", "1 .5 .5 .2 .2")]:
        archive = tmp_path / f"{split}.zip"
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr(f"images/{split}/a.png", image.getvalue())
            z.writestr(f"labels/{split}/a.txt", label)
        archives.append(archive)
    result = module.audit(archives, tmp_path / "report.json")
    assert result["distinct_source_sha256"] == 1
    assert result["exact_duplicate_groups_crossing_archives"] == 1
    assert result["archives"][0]["counts"]["valid_stamp_boxes"] == 1
    assert result["archives"][1]["errors"]["Unmapped source class"] == 1
    assert result["accepted_for_training"] is False
