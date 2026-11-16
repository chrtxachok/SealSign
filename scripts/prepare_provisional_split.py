"""Create a reproducible provisional split from reviewed candidate groups.

This assignment is exploratory: it does not certify annotations or source rights.
"""

import argparse
import hashlib
import json
import random
from pathlib import Path


def assign_groups(candidate, seed=42):
    """Partition whole groups, rejecting malformed and repeated page IDs."""
    groups = candidate["groups"]
    selected = candidate["selected_page_ids"]
    if not groups or any(not g or len(g) != len(set(g)) for g in groups):
        raise ValueError("Empty group or repeated page in group")
    flat = [page for group in groups for page in group]
    if len(flat) != len(set(flat)) or len(selected) != len(set(selected)):
        raise ValueError("Page appears more than once")
    if set(flat) != set(selected):
        raise ValueError("Group members do not match selected pages")
    if len(groups) < 3:
        raise ValueError("At least three groups are required")
    ordered = sorted(sorted(group) for group in groups)
    random.Random(seed).shuffle(ordered)
    n_test = max(1, round(len(ordered) * 0.15))
    n_val = max(1, round(len(ordered) * 0.15))
    return {
        "test": ordered[:n_test],
        "val": ordered[n_test : n_test + n_val],
        "train": ordered[n_test + n_val :],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    raw = args.candidate.read_bytes()
    candidate = json.loads(raw)
    if candidate.get("schema_version") != "sealsign-candidate-groups-v1":
        raise ValueError("Unsupported candidate schema")
    if candidate.get("accepted_for_training") or candidate.get("group_split_assigned"):
        raise ValueError("Expected an unaccepted candidate without an assigned split")
    manifest_raw = args.manifest.read_bytes()
    if hashlib.sha256(manifest_raw).hexdigest() != candidate["source_manifest_sha256"]:
        raise ValueError("Manifest does not match candidate")
    assignment = assign_groups(candidate, args.seed)
    pages = {p["page_id"]: p for p in map(json.loads, manifest_raw.splitlines())}
    seen_hashes = {}
    for split, groups in assignment.items():
        for page in (p for g in groups for p in g):
            for key in ("sha256", "normalized_sha256"):
                digest = pages[page][key]
                if digest in seen_hashes and seen_hashes[digest] != split:
                    raise ValueError("Exact duplicate images cross splits")
                seen_hashes[digest] = split
    output = {
        "schema_version": "sealsign-provisional-group-split-v1",
        "candidate_sha256": hashlib.sha256(raw).hexdigest(),
        "seed": args.seed,
        "assignment_unit": "candidate group",
        "status": "exploratory_not_accepted_for_training",
        "splits": assignment,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as f:
        json.dump(output, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
