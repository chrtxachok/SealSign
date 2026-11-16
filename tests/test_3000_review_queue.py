"""Ensure review selection keeps protected and unresolved groups out."""

import json
import subprocess
import sys
from pathlib import Path


def test_queue_excludes_transitively_related_test_pages_and_held(tmp_path):
    files = [f"images/train/stamp_detection_jsam_{c}.jpg" for c in "abcdef"]

    def write(name, obj):
        path = tmp_path / name
        path.write_text(json.dumps(obj))
        return path

    inventory = write("inventory.json", [{"archive": "train.zip", "file": f} for f in files])
    queue = write(
        "queue.json",
        {
            "groups": [
                {
                    "group_id": "reviewed",
                    "members": [["train.zip", files[0]], ["train.zip", files[1]]],
                },
                {"group_id": "held", "members": [["train.zip", files[3]]]},
            ]
        },
    )
    review = write("review.json", {"reviewed_components": [{"component_id": "reviewed"}]})
    links = write("links.json", {"links": []})
    split = write("split.json", {"splits": {"test": [["page-a"]]}})
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(
        "\n".join(
            json.dumps({"page_id": f"page-{c}", "original_split": "train", "relative_path": file})
            for c, file in zip("abc", files, strict=False)
        )
        + "\n"
    )
    batch = write("batch.json", {"groups": [{"page_ids": ["page-b", "page-c"]}]})
    output = tmp_path / "output.json"
    script = Path(__file__).parents[1] / "scripts/prepare_3000_review_queue.py"
    args = {
        "inventory": inventory,
        "queue": queue,
        "review": review,
        "links": links,
        "teaching-split": split,
        "teaching-manifest": manifest,
        "batch-groups": batch,
        "output": output,
        "count": 2,
    }
    command = [sys.executable, str(script)]
    for key, value in args.items():
        command.extend([f"--{key}", str(value)])
    subprocess.run(command, check=True, capture_output=True, text=True)
    result = json.loads(output.read_text())
    assert {x["file"] for x in result["selected"]} == set(files[4:])
    assert result["accepted_for_training"] is False
    assert all(x["signature_status"] == "unreviewed" for x in result["selected"])
