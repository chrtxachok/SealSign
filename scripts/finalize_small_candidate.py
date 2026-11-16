"""Exclude all triaged pages and freeze an experimental grouped candidate."""

import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("triage", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.candidate.read_bytes()
    triage_raw = args.triage.read_bytes()
    candidate, triage = json.loads(raw), json.loads(triage_raw)
    selected = set(candidate["selected_page_ids"])
    held = {issue["page_id"] for issue in triage["possible_issues"]}
    if not held or not held <= selected:
        raise ValueError("Triage pages absent from candidate")
    if set(triage["overview_positions_inspected"]) != set(range(1, len(selected) + 1)):
        raise ValueError("Overview incomplete")
    groups = [[page for page in group if page not in held] for group in candidate["groups"]]
    candidate["groups"] = [group for group in groups if group]
    candidate["selected_page_ids"] = sorted(selected - held)
    candidate["parent_candidate_sha256"] = hashlib.sha256(raw).hexdigest()
    candidate["exclusion_triage_sha256"] = hashlib.sha256(triage_raw).hexdigest()
    candidate["exclusion_count"] = len(held)
    candidate["needs_full_qc_and_provenance"] = True
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as output:
        json.dump(candidate, output, indent=2)
        output.write("\n")


if __name__ == "__main__":
    main()
