"""Prepare reproducible annotation work batches; these are not model splits."""

import argparse
import importlib.util
import json
import random
import tempfile
import zipfile
from pathlib import Path

from sealsign.data.importer import import_zip, sha256, zip_inventory

REVISION = "998243bde1262ccb57ca28ddd6868b05fd1ddf49"
TRAIN_HASH = "07016aa6df14b4b4fab6bfa896469003160f932677bae86e8f91712f6cbdef0c"


def plan(names, excluded, size=100, seed=42):
    if not 1 <= size <= 100 or len(names) != len(set(names)) or not set(excluded) <= set(names):
        raise ValueError("Invalid names, excluded pages or batch size")
    pending = sorted(set(names) - set(excluded))
    random.Random(seed).shuffle(pending)
    return [pending[start : start + size] for start in range(0, len(pending), size)]


def _prepare(archive_path, pilot_provenance, output, batch=1):
    if output.exists():
        raise ValueError("Output exists")
    if sha256(archive_path) != TRAIN_HASH:
        raise ValueError("Source ZIP checksum mismatch")
    provenance = json.loads(pilot_provenance.read_text())
    if provenance["parent_sha256"] != TRAIN_HASH or provenance["revision"] != REVISION:
        raise ValueError("Pilot provenance mismatch")
    with zipfile.ZipFile(archive_path) as archive:
        inventory = zip_inventory(archive)
        names = sorted(
            n
            for n in inventory
            if n.startswith("images/train/") and n.endswith((".jpg", ".jpeg", ".png"))
        )
        batches = plan(names, provenance["selected"])
        if not 1 <= batch <= len(batches):
            raise ValueError("Unknown batch")
        selected = batches[batch - 1]
        output.mkdir(parents=True)
        (output / "plan.json").write_text(
            json.dumps(
                {
                    "revision": REVISION,
                    "source_sha256": TRAIN_HASH,
                    "seed": 42,
                    "batch_size": 100,
                    "excluded_pilot": provenance["selected"],
                    "batches": batches,
                    "note": "Annotation workloads, not train/val/test assignments",
                },
                indent=2,
            )
            + "\n"
        )
        with zipfile.ZipFile(output / "source.zip", "w") as target:
            for name in selected:
                label = name.replace("images/train/", "labels/train/").rsplit(".", 1)[0] + ".txt"
                for member in [name, label]:
                    limit = 64 * 1024**2 if member == name else 4 * 1024**2
                    if inventory[member].file_size > limit:
                        raise ValueError("Member budget exceeded")
                    info = zipfile.ZipInfo(member, date_time=(2026, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    target.writestr(info, archive.read(member))
    config = {
        "archive_id": f"mapo80-998243-train-work-{batch:03d}",
        "sha256": sha256(output / "source.zip"),
        "sources": [
            {
                "images": "images/train",
                "labels": "labels/train",
                "format": "bbox",
                "class_map": {"0": 0},
                "original_split": "train",
            }
        ],
    }
    (output / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    imported = import_zip(output / "source.zip", config, output / "bundle", preview_limit=0)
    spec = importlib.util.spec_from_file_location(
        "editor_builder", Path(__file__).with_name("build_annotation_editor.py")
    )
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    builder.build(output / "bundle", output / "editor.html")
    summary = {
        "batch": batch,
        "pages": len(selected),
        "total_batches": len(batches),
        "remaining_pages": sum(map(len, batches)),
        "pilot_excluded": len(provenance["selected"]),
        "source_revision": REVISION,
        "source_sha256": TRAIN_HASH,
        "objects": imported["objects_by_class"],
        "accepted_for_training": False,
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def prepare(archive_path, pilot_provenance, output, batch=1):
    if output.exists():
        raise ValueError("Output exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent, prefix=".batch-") as temp:
        target = Path(temp) / "work"
        result = _prepare(archive_path, pilot_provenance, target, batch)
        target.rename(output)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("archive", type=Path)
    p.add_argument("pilot_provenance", type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--batch", type=int, default=1)
    a = p.parse_args()
    print(json.dumps(prepare(a.archive, a.pilot_provenance, a.output, a.batch)))


if __name__ == "__main__":
    main()
