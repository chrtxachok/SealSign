"""Prepare a private review queue, not training labels, from mapo80 inventory."""

import argparse
import collections
import hashlib
import json
import random
from pathlib import Path

from sealsign.data.importer import sha256

PREFIXES = (
    "stamp_detection_jsam_",
    "yolo_stamp_classify_",
    "stamp_detectation_marcos_",
    "neg_funsd_",
    "neg_rvl_cdip_",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--links", type=Path, required=True)
    parser.add_argument("--teaching-split", type=Path, required=True)
    parser.add_argument("--teaching-manifest", type=Path, required=True)
    parser.add_argument("--batch-groups", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--count", type=int, default=3000)
    args = parser.parse_args()
    inventory = json.loads(args.inventory.read_text())
    queue = json.loads(args.queue.read_text())["groups"]
    reviewed = {
        x["component_id"] for x in json.loads(args.review.read_text())["reviewed_components"]
    }
    links = json.loads(args.links.read_text())["links"]
    all_files = {(x["archive"], x["file"]) for x in inventory}
    if len(all_files) != len(inventory):
        raise ValueError("Duplicate inventory member")
    parent = {p: p for p in all_files}

    def root(x):
        while parent[x] != x:
            x = parent[x]
        return x

    def union(a, b):
        a, b = root(a), root(b)
        if a != b:
            parent[b] = a

    component_files = {}
    used = set()
    held_members = set()
    for group in queue:
        members = list(map(tuple, group["members"]))
        if not members or any(p not in all_files or p in used for p in members):
            raise ValueError("Invalid or repeated component member")
        used.update(members)
        component_files[group["group_id"]] = members
        for member in members[1:]:
            union(members[0], member)
        if group["group_id"] not in reviewed:
            held_members.update(members)
    for link in links:
        if link["status"] != "visually_same_document":
            raise ValueError("Unreviewed link")
        a, b = link["component_ids"]
        union(component_files[a][0], component_files[b][0])
    test_split = json.loads(args.teaching_split.read_text())["splits"]["test"]
    test_ids = {p for group in test_split for p in group}
    manifest = {
        p["page_id"]: p for p in map(json.loads, args.teaching_manifest.read_text().splitlines())
    }
    if not test_ids <= set(manifest):
        raise ValueError("Teaching test page missing")

    def file_for(page):
        entry = manifest[page]
        return (f"{entry['original_split']}.zip", entry["relative_path"])

    test_files = {file_for(p) for p in test_ids}
    if not test_files <= all_files:
        raise ValueError("Teaching test not in inventory")
    for group in json.loads(args.batch_groups.read_text())["groups"]:
        pages = group["page_ids"]
        if any(page not in manifest or file_for(page) not in all_files for page in pages):
            raise ValueError("Batch group page missing")
        members = [file_for(page) for page in pages]
        for member in members[1:]:
            union(members[0], member)
    held_groups = {root(p) for p in held_members | test_files}
    components = collections.defaultdict(list)
    for pair in all_files:
        components[root(pair)].append(pair)
    eligible = []
    for group_id, members in components.items():
        if group_id in held_groups:
            continue
        choices = sorted(p for p in members if Path(p[1]).name.startswith(PREFIXES))
        if choices:
            eligible.append(choices[0])
    eligible.sort()
    if args.count <= 0 or len(eligible) < args.count:
        raise ValueError(f"Only {len(eligible)} eligible candidates")
    random.Random(42).shuffle(eligible)
    selected = eligible[: args.count]
    result = {
        "schema_version": "sealsign-3000-review-queue-v1",
        "seed": 42,
        "input_sha256": {
            k: sha256(getattr(args, k))
            for k in (
                "inventory",
                "queue",
                "review",
                "links",
                "teaching_split",
                "teaching_manifest",
                "batch_groups",
            )
        },
        "eligible_conservative_groups": len(eligible),
        "selected": [
            {
                "archive": a,
                "file": f,
                "stamp_status": "source_unreviewed",
                "signature_status": "unreviewed",
            }
            for a, f in selected
        ],
        "accepted_for_training": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print(
        json.dumps(
            {
                "eligible": len(eligible),
                "selected": len(selected),
                "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
            }
        )
    )


if __name__ == "__main__":
    main()
