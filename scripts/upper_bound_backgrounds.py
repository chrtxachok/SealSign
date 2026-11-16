"""Calculate a conservative image-original upper bound from reviewed identities."""

import argparse
import json
from pathlib import Path

from validate_background_review import validate

from sealsign.data.importer import sha256


def calculate(audit, review_path, queue_path, links_path):
    result = validate(audit, review_path)
    review = json.loads(review_path.read_text())
    queue = json.loads(queue_path.read_text())
    links = json.loads(links_path.read_text())
    if queue.get("candidate_csv_sha256") != sha256(audit / "candidate-pairs.csv"):
        raise ValueError("Queue candidate hash mismatch")
    groups = queue["groups"]
    reviewed = {item["component_id"]: item for item in review["reviewed_components"]}
    parent = {key: key for key, item in reviewed.items() if len(item["background_groups"]) == 1}

    def root(node):
        while parent[node] != node:
            node = parent[node]
        return node

    independent_links = 0
    for link in links["links"]:
        positions, ids = link["positions"], link["component_ids"]
        if (
            len(positions) != 2
            or len(ids) != 2
            or link.get("status") != "visually_same_document"
            or link.get("canonical_groups_modified") is not False
        ):
            raise ValueError("Invalid link")
        for position, identifier in zip(positions, ids, strict=True):
            if not isinstance(position, int) or not 1 <= position <= len(groups):
                raise ValueError("Invalid queue position")
            if groups[position - 1]["group_id"] != identifier or identifier not in parent:
                raise ValueError("Link not tied to a reviewed single-background component")
        a, b = map(root, ids)
        if a != b:
            parent[b] = a
            independent_links += 1

    inventory = json.loads((audit / "inventory.json").read_text())
    report = json.loads((audit / "report.json").read_text())
    if len(inventory) != report["images"]:
        raise ValueError("Inventory count mismatch")
    return {
        "schema_version": "sealsign-background-upper-bound-v1",
        "review_sha256": sha256(review_path),
        "links_sha256": sha256(links_path),
        "inventory_sha256": sha256(audit / "inventory.json"),
        "images": len(inventory),
        "reviewed_components": result["reviewed_components"],
        "within_component_additional_variants": result["additional_variants"],
        "independent_cross_component_links": independent_links,
        "upper_bound_originals": len(inventory) - result["additional_variants"] - independent_links,
        "held_components": result["remaining_candidate_components"],
        "interpretation": (
            "Upper bound for these archived images conditional on visual identity decisions; "
            "not a verified original count or accepted training set."
        ),
        "accepted_for_training": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit", type=Path)
    parser.add_argument("review", type=Path)
    parser.add_argument("queue", type=Path)
    parser.add_argument("links", type=Path)
    args = parser.parse_args()
    print(json.dumps(calculate(args.audit, args.review, args.queue, args.links), indent=2))


if __name__ == "__main__":
    main()
