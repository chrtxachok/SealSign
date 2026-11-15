"""Validate complete visual partitions of candidate components, without accepting data."""

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from sealsign.data.importer import sha256


def component_id(members):
    return hashlib.sha256(json.dumps(sorted(members), separators=(",", ":")).encode()).hexdigest()


def load_graph(audit):
    inventory = json.loads((audit / "inventory.json").read_text())
    keys = {(r["archive"], r["file"]) for r in inventory}
    if len(keys) != len(inventory):
        raise ValueError("Duplicate inventory identity")
    parent = {}

    def root(key):
        parent.setdefault(key, key)
        while parent[key] != key:
            parent[key] = parent[parent[key]]
            key = parent[key]
        return key

    pairs = []
    with (audit / "candidate-pairs.csv").open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            a, b = (row["archive_a"], row["file_a"]), (row["archive_b"], row["file_b"])
            if a not in keys or b not in keys or a == b:
                raise ValueError("Unknown or self candidate edge")
            ra, rb = root(a), root(b)
            if ra != rb:
                parent[rb] = ra
            pairs.append((a, b))
    grouped = defaultdict(set)
    for key in parent:
        grouped[root(key)].add(key)
    return {component_id(v): v for v in grouped.values()}, pairs


def validate(audit, review):
    data = json.loads(review.read_text())
    if (
        data.get("schema_version") != "sealsign-background-review-v1"
        or data.get("accepted_for_training") is not False
        or not isinstance(data.get("reviewer"), str)
        or not data["reviewer"].strip()
    ):
        raise ValueError("Invalid review schema or reviewer")
    for name in ["report.json", "inventory.json", "candidate-pairs.csv"]:
        if data.get("source_sha256", {}).get(name) != sha256(audit / name):
            raise ValueError("Audit source hash mismatch")
    report = json.loads((audit / "report.json").read_text())
    if report.get("schema_version") != "sealsign-background-candidates-v1":
        raise ValueError("Wrong audit schema")
    components, pairs = load_graph(audit)
    seen, assignments, counts = set(), {}, Counter()
    for item in data["reviewed_components"]:
        identifier = item["component_id"]
        if identifier not in components or identifier in seen:
            raise ValueError("Unknown or repeated component")
        seen.add(identifier)
        covered = set()
        for group_index, group in enumerate(item["background_groups"]):
            if not isinstance(group.get("evidence"), str) or not group["evidence"].strip():
                raise ValueError("Missing visual evidence")
            members = [tuple(m) for m in group["members"]]
            if not members or len(set(members)) != len(members):
                raise ValueError("Empty or repeated group membership")
            for member in members:
                if member not in components[identifier] or member in covered:
                    raise ValueError("Foreign or multiply assigned member")
                covered.add(member)
                assignments[member] = (identifier, group_index)
            counts["background_groups"] += 1
            counts["additional_variants"] += len(members) - 1
            counts["groups_crossing_upstream_archives"] += len({m[0] for m in members}) > 1
        if covered != components[identifier]:
            raise ValueError("Component is not fully partitioned")
    for a, b in pairs:
        if a in assignments and b in assignments:
            counts["reviewed_candidate_edges"] += 1
            counts["different_background_candidate_edges"] += assignments[a] != assignments[b]
    return {
        "reviewed_components": len(seen),
        "remaining_candidate_components": len(components) - len(seen),
        "reviewed_files": len(assignments),
        **counts,
        "review_sha256": sha256(review),
        "accepted_for_training": False,
        "global_original_count_established": False,
        "canonical_groups_or_split_modified": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit", type=Path)
    parser.add_argument("review", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.audit, args.review)))


if __name__ == "__main__":
    main()
