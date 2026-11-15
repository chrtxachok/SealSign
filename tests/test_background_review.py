"""A false bridge must be splittable without losing or counting members twice."""

import copy
import csv
import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "background_review", Path(__file__).parents[1] / "scripts/validate_background_review.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.fixture
def example(tmp_path):
    audit = tmp_path / "audit"
    audit.mkdir()
    members = [("train.zip", "a"), ("val.zip", "b"), ("train.zip", "c")]
    (audit / "inventory.json").write_text(
        json.dumps([{"archive": a, "file": f} for a, f in members])
    )
    (audit / "report.json").write_text(
        json.dumps({"schema_version": "sealsign-background-candidates-v1"})
    )
    with (audit / "candidate-pairs.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["archive_a", "file_a", "archive_b", "file_b"])
        writer.writerow([*members[0], *members[1]])
        writer.writerow([*members[1], *members[2]])
    data = {
        "schema_version": "sealsign-background-review-v1",
        "reviewer": "Reviewer",
        "accepted_for_training": False,
        "source_sha256": {
            n: module.sha256(audit / n)
            for n in ["inventory.json", "report.json", "candidate-pairs.csv"]
        },
        "reviewed_components": [
            {
                "component_id": module.component_id(members),
                "background_groups": [
                    {"members": members[:2], "evidence": "Same document identifier and body."},
                    {"members": members[2:], "evidence": "Different recipient and document ID."},
                ],
            }
        ],
    }
    return audit, data, tmp_path / "review.json"


def test_false_bridge_is_split_and_original_count_not_claimed(example):
    audit, data, path = example
    path.write_text(json.dumps(data))
    result = module.validate(audit, path)
    assert result["reviewed_files"] == 3
    assert result["background_groups"] == 2
    assert result["additional_variants"] == 1
    assert result["different_background_candidate_edges"] == 1
    assert result["groups_crossing_upstream_archives"] == 1
    assert result["accepted_for_training"] is False
    assert result["global_original_count_established"] is False
    assert result["canonical_groups_or_split_modified"] is False


@pytest.mark.parametrize("defect", ["missing", "duplicate", "foreign", "component", "evidence"])
def test_invalid_partition_never_accepts(example, defect):
    audit, original, path = example
    data = copy.deepcopy(original)
    component = data["reviewed_components"][0]
    if defect == "missing":
        component["background_groups"].pop()
    elif defect == "duplicate":
        component["background_groups"][1]["members"] = [("train.zip", "a")]
    elif defect == "foreign":
        component["background_groups"][1]["members"] = [("train.zip", "unknown")]
    elif defect == "component":
        data["reviewed_components"].append(copy.deepcopy(component))
    else:
        component["background_groups"][0]["evidence"] = ""
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        module.validate(audit, path)


def test_source_tampering_is_rejected(example):
    audit, data, path = example
    path.write_text(json.dumps(data))
    (audit / "candidate-pairs.csv").write_text("changed")
    with pytest.raises(ValueError, match="hash"):
        module.validate(audit, path)
