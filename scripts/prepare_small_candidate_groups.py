"""Prepare conservative candidate groups; this never accepts pages for training."""

import argparse
import collections
import hashlib
import json
from pathlib import Path

from sealsign.data.validator import validate_bundle

b = Path("artifacts/annotation-batches/batch-001-agent-v6")
validate_bundle(b)
pages = [json.loads(x) for x in (b / "manifest.jsonl").read_text().splitlines()]
coco = json.loads((b / "annotations.json").read_text())
by_id = {x["id"]: x["page_id"] for x in coco["images"]}
objects = collections.defaultdict(collections.Counter)
for x in coco["annotations"]:
    objects[by_id[x["image_id"]]][str(x["category_id"])] += 1
selected = [
    p
    for p in pages
    if p.get("first_review", {}).get("status") == "first_review"
    and any(
        Path(p["relative_path"]).name.startswith(s)
        for s in ("stamp_detection_jsam_", "yolo_stamp_classify_", "stamp_detectation_marcos_")
    )
]
print(
    "selected",
    len(selected),
    "classes",
    sum(objects[p["page_id"]]["0"] for p in selected),
    sum(objects[p["page_id"]]["1"] for p in selected),
    "empty",
    sum(not objects[p["page_id"]] for p in selected),
)
q = json.loads(Path("artifacts/data-qc/background-group-review-v1/queue.json").read_text())[
    "groups"
]
index = {tuple(m): g["group_id"] for g in q for m in g["members"]}
sel_ids = {p["page_id"] for p in selected}
if len(sel_ids) != len(selected) or any(
    not p.get("first_review", {}).get("stamp_checked")
    or not p.get("first_review", {}).get("signature_checked")
    or p.get("exclusion_reason")
    or p.get("original_split") != "train"
    for p in selected
):
    raise ValueError("Invalid or repeated selected page")
held = {208, 303, 371, 380, 395, 397, 403, 424, 427, 464, 488, 510, 556}
held_ids = {q[position - 1]["group_id"] for position in held}
if any(index.get(("train.zip", page["relative_path"])) in held_ids for page in selected):
    raise ValueError("Selected page belongs to held candidate component")
parent = {p["page_id"]: p["page_id"] for p in selected}


def root(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


def union(a, b):
    a, b = root(a), root(b)
    if a != b:
        parent[b] = a


components = collections.defaultdict(list)
for p in selected:
    component = index.get(("train.zip", p["relative_path"]))
    if component:
        components[component].append(p["page_id"])
for members in components.values():
    for m in members[1:]:
        union(members[0], m)
links = json.loads(
    Path("artifacts/data-qc/background-group-review-v1/cross-component-links-v6.json").read_text()
)["links"]
component_parent = {g["group_id"]: g["group_id"] for g in q}


def component_root(node):
    while component_parent[node] != node:
        node = component_parent[node]
    return node


for link in links:
    if link.get("status") != "visually_same_document":
        raise ValueError("Unverified component link")
    left, right = map(component_root, link["component_ids"])
    if left != right:
        component_parent[right] = left
linked_members = collections.defaultdict(list)
for component, members in components.items():
    linked_members[component_root(component)].extend(members)
for members in linked_members.values():
    for member in members[1:]:
        union(members[0], member)
for group in json.loads(Path("artifacts/data-qc/batch001-agent/group-review-v6.json").read_text())[
    "groups"
]:
    members = [x for x in group["page_ids"] if x in sel_ids]
    for m in members[1:]:
        union(members[0], m)
groups = collections.defaultdict(list)
for p in selected:
    groups[root(p["page_id"])].append(p["page_id"])
print(
    "conservative groups",
    len(groups),
    "size dist",
    dict(collections.Counter(map(len, groups.values()))),
)
print(
    "classes by page",
    dict(collections.Counter(tuple(sorted(objects[p["page_id"]])) for p in selected)),
)
out = {
    "schema_version": "sealsign-candidate-groups-v1",
    "source_manifest_sha256": hashlib.sha256((b / "manifest.jsonl").read_bytes()).hexdigest(),
    "source_annotations_sha256": hashlib.sha256((b / "annotations.json").read_bytes()).hexdigest(),
    "queue_sha256": hashlib.sha256(
        Path("artifacts/data-qc/background-group-review-v1/queue.json").read_bytes()
    ).hexdigest(),
    "links_sha256": hashlib.sha256(
        Path(
            "artifacts/data-qc/background-group-review-v1/cross-component-links-v6.json"
        ).read_bytes()
    ).hexdigest(),
    "batch_group_review_sha256": hashlib.sha256(
        Path("artifacts/data-qc/batch001-agent/group-review-v6.json").read_bytes()
    ).hexdigest(),
    "selected_page_ids": sorted(sel_ids),
    "groups": [sorted(v) for v in groups.values()],
    "accepted_for_training": False,
    "group_split_assigned": False,
    "needs_full_qc_and_provenance": True,
}
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
p = parser.parse_args().output
p.mkdir(parents=True, exist_ok=False)
(p / "candidate-groups.json").write_text(json.dumps(out, indent=2) + "\n")
