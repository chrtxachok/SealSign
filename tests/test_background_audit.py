"""Background candidates must reject blank space and preserve unreviewed status."""

import importlib.util
import io
import zipfile
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

spec = importlib.util.spec_from_file_location(
    "background_audit", Path(__file__).parents[1] / "scripts/audit_backgrounds.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def document(offset=0):
    im = Image.new("RGB", (256, 256), "white")
    draw = ImageDraw.Draw(im)
    for y in range(8, 250, 12):
        for x in range(6, 245, 19):
            width = 5 + (x + y) % 9
            draw.rectangle((x, y + offset, x + width, y + offset + 3), fill="black")
    return im


def test_same_background_with_different_imprints_is_a_candidate():
    a, b = document(), document()
    ImageDraw.Draw(a).ellipse((15, 15, 60, 60), outline="blue", width=6)
    ImageDraw.Draw(b).rectangle((180, 175, 225, 220), outline="red", width=6)
    fa = module.fingerprint(a, [{"bbox": [15, 15, 45, 45]}])
    fb = module.fingerprint(b, [{"bbox": [180, 175, 45, 45]}])
    pairs, _, _ = module.candidates([fa, fb])
    assert len(pairs) == 1
    assert pairs[0][:2] == (0, 1)
    assert module.compare(fa, fb)[0] is True


def test_blank_and_sparse_pages_do_not_establish_identity():
    blank = module.fingerprint(Image.new("RGB", (256, 256), "white"), [])
    assert module.candidates([blank, blank])[0] == []
    assert module.compare(blank, blank)[0] is False
    sparse = Image.new("RGB", (256, 256), "white")
    ImageDraw.Draw(sparse).line((5, 5, 200, 5), fill="black")
    f = module.fingerprint(sparse, [])
    assert module.compare(f, f)[0] is False


def test_different_text_cannot_match_only_through_white_background():
    a = module.fingerprint(document(), [])
    b = module.fingerprint(document(offset=6), [])
    assert module.compare(a, b)[0] is False


def test_excessive_mask_cannot_manufacture_a_match():
    f = module.fingerprint(document(), [{"bbox": [0, 0, 250, 250]}])
    assert module.compare(f, f)[0] is False


def test_zip_audit_retains_all_candidates_without_acceptance(tmp_path):
    raw = io.BytesIO()
    document().save(raw, format="PNG")
    archives = []
    for split in ["train", "val"]:
        archive = tmp_path / f"{split}.zip"
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr(f"images/{split}/a.png", raw.getvalue())
            z.writestr(f"labels/{split}/a.txt", "")
        archives.append(archive)
    output = tmp_path / "audit"
    report = module.audit(archives, output)
    assert report["candidate_pairs"] == report["cross_archive_candidate_pairs"] == 1
    assert report["accepted_for_training"] is False
    assert report["independent_originals_proven"] is False
    assert "unreviewed" in (output / "candidate-pairs.csv").read_text()
    with pytest.raises(ValueError, match="exists"):
        module.audit(archives, output)


def test_unsafe_zip_or_missing_labels_never_leaves_an_output(tmp_path):
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("../escape.png", b"x")
    with pytest.raises(ValueError):
        module.audit([archive], tmp_path / "out")
    assert not (tmp_path / "out").exists()
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("images/train/a.png", b"x")
    with pytest.raises(ValueError, match="label"):
        module.audit([archive], tmp_path / "out")
    assert not (tmp_path / "out").exists()
