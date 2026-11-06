"""ZIP audit must reject unsafe inputs and distinguish copies from originals."""

import importlib.util
import zipfile
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "audit_dataset_zip", Path(__file__).parents[1] / "scripts/audit_dataset_zip.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_exact_copies_and_unreviewed_labels(tmp_path):
    path = tmp_path / "fixture.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("stamps/train/images/a.png", b"same image bytes")
        archive.writestr("stamps/val/images/b.png", b"same image bytes")
        archive.writestr("stamps/labels/a.txt", "0 0.5 0.5 0.2 0.2\n")
        archive.writestr("stamps/labels/b.txt", "")
    report = module.audit(path)
    assert report["components"]["stamps"]["extra_exact_copies"] == 1
    assert (
        report["components"]["stamps"]["exact_duplicate_hash_groups_crossing_upstream_splits"] == 1
    )
    assert report["components"]["stamps"]["empty_labels"] == 1
    assert report["accepted_for_training"] is False
    assert report["original_pages_verified"] is False


@pytest.mark.parametrize("name", ["../image.png", "/image.png", "folder\\image.png"])
def test_reject_unsafe_paths(tmp_path, name):
    path = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(name, b"data")
    with pytest.raises(ValueError, match="Unsafe"):
        module.audit(path)


def test_reject_corrupt_member(tmp_path):
    path = tmp_path / "corrupt.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("a.png", b"original payload")
    path.write_bytes(path.read_bytes().replace(b"original payload", b"modified payload"))
    with pytest.raises(zipfile.BadZipFile, match="CRC"):
        module.audit(path)


def test_reject_symlink(tmp_path):
    path = tmp_path / "symlink.zip"
    member = zipfile.ZipInfo("link")
    member.create_system = 3
    member.external_attr = 0o120777 << 16
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(member, "outside")
    with pytest.raises(ValueError, match="Unsafe"):
        module.audit(path)
