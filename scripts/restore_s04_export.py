"""Rebuild the frozen YOLO dataset from ZIP images and private final annotations."""

import argparse
import json
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.finalize_s04 import digest, export, read
from scripts.validate_s04_disputes import validate_bbox, validate_class

FROZEN_FILES = ("manifest.jsonl", "annotations.json", "split.json")


def restore(metadata: Path, archives: Path, output: Path) -> None:
    if output.exists():
        raise FileExistsError(output)
    report = read(metadata / "qc-report.json")
    for name in FROZEN_FILES:
        if digest(metadata / name) != report["output_sha256"][name]:
            raise ValueError(f"Frozen metadata checksum mismatch: {name}")
    annotations = read(metadata / "annotations.json")
    if annotations["classes"] != {"0": "stamp", "1": "signature"}:
        raise ValueError("Unexpected class mapping")
    labels = {int(index): boxes for index, boxes in annotations["pages"].items()}
    split = read(metadata / "split.json")["splits"]
    if set(split) != {"train", "val", "test"}:
        raise ValueError("Expected train, val and test")
    manifest = [
        json.loads(line)
        for line in (metadata / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    by_index = {page["queue_index"]: page for page in manifest}
    assignment = {
        index: part for part, groups in split.items() for group in groups for index in group
    }
    if (
        len(by_index) != len(manifest)
        or sum(len(group) for groups in split.values() for group in groups) != len(assignment)
        or assignment != {i: page["split"] for i, page in by_index.items() if page["split"]}
        or set(labels) != set(assignment)
    ):
        raise ValueError("Frozen split, manifest and annotations disagree")

    expected = {}
    for groups in split.values():
        for group in groups:
            if len({by_index[i]["group_id"] for i in group}) != 1:
                raise ValueError("Invalid document group")
    for index, boxes in labels.items():
        page = by_index[index]
        if page["page_id"] != f"s04-{index:04d}":
            raise ValueError("Invalid frozen page identifier")
        for box in boxes:
            validate_class(box["category_id"])
            validate_bbox(box["bbox"], page["width"], page["height"])
        expected[index] = (page["export_sha256"], page["label_sha256"])
    yaml = (metadata / "dataset.yaml").read_bytes()
    newline = "\r\n" if b"\r\n" in yaml else "\n"

    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=output.parent) as temp:
        folder = Path(temp) / "dataset"
        summary = export(folder, manifest, labels, split, archives_dir=archives, newline=newline)
        if summary != report["splits"]:
            raise ValueError("Restored corpus statistics differ from the frozen corpus")
        for index, (image_hash, label_hash) in expected.items():
            page = by_index[index]
            if (page["export_sha256"], page["label_sha256"]) != (image_hash, label_hash):
                raise ValueError(f"Restored image or label checksum mismatch: {page['page_id']}")
        if (folder / "dataset.yaml").read_bytes() != yaml:
            raise ValueError("Restored YOLO configuration differs from the frozen corpus")
        for name in (*FROZEN_FILES, "qc-report.json"):
            shutil.copyfile(metadata / name, folder / name)
        folder.rename(output)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--archives", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    restore(args.metadata, args.archives, args.output)
