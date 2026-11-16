"""Export the frozen teaching split to a private YOLO directory."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from sealsign.data.importer import sha256
from sealsign.data.validator import validate_bundle


def export(bundle, candidate_file, split_file, output):
    validate_bundle(bundle)
    candidate_raw = candidate_file.read_bytes()
    candidate = json.loads(candidate_raw)
    split = json.loads(split_file.read_bytes())
    if split["candidate_sha256"] != hashlib.sha256(candidate_raw).hexdigest():
        raise ValueError("Split does not match candidate")
    for name in ("manifest.jsonl", "annotations.json"):
        if sha256(bundle / name) != candidate[f"source_{name.split('.')[0]}_sha256"]:
            raise ValueError(f"Bundle {name} does not match candidate")
    if set(split["splits"]) != {"train", "val", "test"}:
        raise ValueError("Invalid splits")
    groups = [tuple(sorted(g)) for part in split["splits"].values() for g in part]
    if sorted(groups) != sorted(tuple(sorted(g)) for g in candidate["groups"]):
        raise ValueError("Split groups differ from candidate")
    pages = {
        p["page_id"]: p
        for p in map(json.loads, (bundle / "manifest.jsonl").read_text().splitlines())
    }
    output.mkdir(parents=True, exist_ok=False)
    result = {}
    for part, assigned_groups in split["splits"].items():
        (output / "images" / part).mkdir(parents=True)
        (output / "labels" / part).mkdir(parents=True)
        count = 0
        for page_id in (p for group in assigned_groups for p in group):
            page = pages[page_id]
            image = bundle / page["normalized_path"]
            label = bundle / "unreviewed-yolo" / f"{page_id}.txt"
            shutil.copyfile(image, output / "images" / part / f"{page_id}{image.suffix}")
            shutil.copyfile(label, output / "labels" / part / f"{page_id}.txt")
            count += 1
        result[part] = count
    (output / "export-summary.json").write_text(
        json.dumps(
            {
                "schema_version": "sealsign-teaching-export-v1",
                "candidate_sha256": hashlib.sha256(candidate_raw).hexdigest(),
                "split_sha256": sha256(split_file),
                "pages": result,
                "status": "teaching_experiment_with_documented_limitations",
            },
            indent=2,
        )
        + "\n"
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--split", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(export(args.bundle, args.candidate, args.split, args.output))


if __name__ == "__main__":
    main()
