"""Conversion, provenance and safety tests use generated images only."""

import io
import json
import zipfile

import pytest
from PIL import Image

from sealsign.data.geometry import parse_labels
from sealsign.data.importer import import_zip, sha256
from sealsign.data.validator import validate_bundle


def image_bytes(orientation=1):
    image = Image.new("RGB", (100, 60), "white")
    exif = Image.Exif()
    exif[274] = orientation
    stream = io.BytesIO()
    image.save(stream, format="PNG", exif=exif)
    return stream.getvalue()


def fixture(tmp_path, labels="0 0.2 0.35 0.2 0.3\n", orientation=1, extras=None):
    path = tmp_path / "source.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("train/images/a.png", image_bytes(orientation))
        if labels is not None:
            archive.writestr("train/labels/a.txt", labels)
        for name, content in (extras or {}).items():
            archive.writestr(name, content)
    return path, {
        "archive_id": "synthetic-v1",
        "sha256": sha256(path),
        "sources": [
            {
                "images": "train/images",
                "labels": "train/labels",
                "format": "bbox",
                "class_map": {"0": 1, "1": 0},
                "original_split": "train",
            }
        ],
    }


def test_import_reproducible_bundle_and_exif(tmp_path):
    path, config = fixture(tmp_path, orientation=6)
    first, second = tmp_path / "first", tmp_path / "second"
    report = import_zip(path, config, first)
    import_zip(path, config, second)
    assert report["input_images"] == report["canonical_images"] == 1
    assert report["accepted_for_training"] is False
    assert validate_bundle(first)["annotations"] == 1
    for name in ("annotations.json", "manifest.jsonl", "report.json"):
        assert (first / name).read_bytes() == (second / name).read_bytes()
    coco = json.loads((first / "annotations.json").read_text())
    assert (coco["images"][0]["width"], coco["images"][0]["height"]) == (60, 100)
    obj = coco["annotations"][0]
    assert obj["category_id"] == 1
    assert obj["bbox"] == pytest.approx([30, 10, 18, 20])
    manifest = json.loads((first / "manifest.jsonl").read_text())
    assert manifest["source_exif_orientation"] == 6
    assert manifest["original_split"] == "train" and manifest["split"] is None
    assert manifest["review_status"] == "unreviewed"
    assert len(list((first / "previews").glob("*.png"))) == 1
    with pytest.raises(ValueError, match="already exists"):
        import_zip(path, config, first)


@pytest.mark.parametrize("labels,status", [(None, "missing"), ("", "empty_unreviewed")])
def test_missing_and_empty_never_become_negatives(tmp_path, labels, status):
    path, config = fixture(tmp_path, labels=labels)
    output = tmp_path / "bundle"
    import_zip(path, config, output)
    manifest = json.loads((output / "manifest.jsonl").read_text())
    assert manifest["annotation_status"] == status
    assert manifest["review_status"] == "unreviewed"
    assert validate_bundle(output)["annotations"] == 0


@pytest.mark.parametrize(
    "orientation,expected",
    [
        (1, [10, 12, 20, 18]),
        (2, [70, 12, 20, 18]),
        (3, [70, 30, 20, 18]),
        (4, [10, 30, 20, 18]),
        (5, [12, 10, 18, 20]),
        (6, [30, 10, 18, 20]),
        (7, [30, 70, 18, 20]),
        (8, [12, 70, 18, 20]),
    ],
)
def test_all_exif_orientations(orientation, expected):
    objects = parse_labels("0 0.2 0.35 0.2 0.3", "bbox", {"0": 1}, 100, 60, orientation)
    assert objects[0]["bbox"] == pytest.approx(expected)


def test_polygon_instances_and_explicit_mapping():
    objects = parse_labels(
        "0 .1 .2 .3 .2 .2 .5\n1 .5 .5 .8 .5 .8 .9", "polygon", {"0": 1, "1": 0}, 100, 60
    )
    assert [obj["category_id"] for obj in objects] == [1, 0]
    assert objects[0]["bbox"] == pytest.approx([10, 12, 20, 18])
    assert objects[1]["bbox"] == pytest.approx([50, 30, 30, 24])


@pytest.mark.parametrize(
    "line",
    ["9 .2 .2 .1 .1", "0 nan .2 .1 .1", "0 .2 .2 0 .1", "0 .95 .2 .2 .1", "0 .2 .2 .1 .1 extra"],
)
def test_bad_geometry_is_excluded_without_partial_annotations(tmp_path, line):
    path, config = fixture(tmp_path, labels=line)
    output = tmp_path / "bundle"
    report = import_zip(path, config, output)
    assert report["excluded_images"] == 1
    assert report["canonical_images"] == 0
    assert validate_bundle(output)["annotations"] == 0


def test_corrupt_image_stays_in_inventory(tmp_path):
    path, config = fixture(tmp_path, extras={"train/images/b.png": b"broken"})
    output = tmp_path / "bundle"
    report = import_zip(path, config, output)
    assert report["input_images"] == 2 and report["excluded_images"] == 1
    pages = [json.loads(line) for line in (output / "manifest.jsonl").read_text().splitlines()]
    assert pages[1]["decode_status"] == "error" and pages[1]["sha256"]


@pytest.mark.parametrize(
    "extra", ["../escape.txt", "/escape.txt", "C:/escape.txt", "train/labels/orphan.txt"]
)
def test_unsafe_archive_or_orphan_is_not_published(tmp_path, extra):
    path, config = fixture(tmp_path, extras={extra: b""})
    output = tmp_path / "bundle"
    with pytest.raises(ValueError):
        import_zip(path, config, output)
    assert not output.exists()


def test_hash_mismatch_rejected(tmp_path):
    path, config = fixture(tmp_path)
    config["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        import_zip(path, config, tmp_path / "bundle")


def test_validator_catches_tampered_geometry_and_image(tmp_path):
    path, config = fixture(tmp_path)
    output = tmp_path / "bundle"
    import_zip(path, config, output)
    file = output / "annotations.json"
    coco = json.loads(file.read_text())
    coco["annotations"][0]["bbox"][2] = 10000
    file.write_text(json.dumps(coco))
    with pytest.raises(ValueError, match="Invalid canonical box"):
        validate_bundle(output)
    (output / coco["images"][0]["file_name"]).write_bytes(b"tampered")
    with pytest.raises(ValueError, match="checksum"):
        validate_bundle(output)


def test_jpeg_and_derived_label_validation(tmp_path):
    stream = io.BytesIO()
    Image.new("RGB", (100, 60), "white").save(stream, format="JPEG")
    path, config = fixture(tmp_path, extras={"train/images/b.jpg": stream.getvalue()})
    output = tmp_path / "bundle"
    assert import_zip(path, config, output)["canonical_images"] == 2
    assert validate_bundle(output)["images"] == 2
    label = next((output / "unreviewed-yolo").glob("*.txt"))
    label.write_text("0 0 0 0 0")
    with pytest.raises(ValueError, match="Derived YOLO"):
        validate_bundle(output)


def test_exact_duplicates_share_group_without_assigning_split(tmp_path):
    path, config = fixture(tmp_path, extras={"train/images/b.png": image_bytes()})
    output = tmp_path / "bundle"
    import_zip(path, config, output)
    pages = [json.loads(line) for line in (output / "manifest.jsonl").read_text().splitlines()]
    assert pages[0]["duplicate_group"] == pages[1]["duplicate_group"] == pages[0]["sha256"]
    assert all(page["group_id"] is None and page["split"] is None for page in pages)


def test_cli_import_and_validate(tmp_path):
    import subprocess
    import sys

    path, config = fixture(tmp_path)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    output = tmp_path / "bundle"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "sealsign",
            "data",
            "import",
            str(path),
            "--config",
            str(config_path),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout)["accepted_for_training"] is False
    result = subprocess.run(
        [sys.executable, "-m", "sealsign", "data", "validate", str(output)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout)["images"] == 1


def test_zip_symlink_rejected(tmp_path):
    path, config = fixture(tmp_path)
    info = zipfile.ZipInfo("link")
    info.create_system = 3
    info.external_attr = 0o120777 << 16
    with zipfile.ZipFile(path, "a") as archive:
        archive.writestr(info, "outside")
    config["sha256"] = sha256(path)
    with pytest.raises(ValueError, match="symlink"):
        import_zip(path, config, tmp_path / "bundle")


def test_duplicate_paths_rejected(tmp_path):
    path, config = fixture(tmp_path)
    with zipfile.ZipFile(path, "a") as archive, pytest.warns(UserWarning):
        archive.writestr("train/images/a.png", image_bytes())
    config["sha256"] = sha256(path)
    with pytest.raises(ValueError, match="Repeated"):
        import_zip(path, config, tmp_path / "bundle")


def test_ambiguous_label_association_rejected(tmp_path):
    path, config = fixture(tmp_path, extras={"train/images/a.jpg": image_bytes()})
    with pytest.raises(ValueError, match="Ambiguous"):
        import_zip(path, config, tmp_path / "bundle")
