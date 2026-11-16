"""Tests for group leakage and malformed provisional inputs."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "prepare_provisional_split", Path(__file__).parents[1] / "scripts/prepare_provisional_split.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_split_is_deterministic_and_keeps_groups_intact():
    candidate = {
        "groups": [["a", "b"], ["c"], ["d"], ["e"]],
        "selected_page_ids": ["a", "b", "c", "d", "e"],
    }
    result = module.assign_groups(candidate)
    assert result == module.assign_groups(candidate)
    assert sorted(x for groups in result.values() for group in groups for x in group) == list(
        "abcde"
    )
    assert any(["a", "b"] in groups for groups in result.values())
    assert all(result.values())


@pytest.mark.parametrize(
    "groups,selected",
    [
        ([["a"], ["a"], ["b"]], ["a", "b"]),
        ([["a"], ["b"], ["c"]], ["a", "b", "d"]),
        ([["a", "a"], ["b"], ["c"]], ["a", "b", "c"]),
        ([["a"], ["b"], []], ["a", "b"]),
    ],
)
def test_rejects_bad_memberships(groups, selected):
    with pytest.raises(ValueError):
        module.assign_groups({"groups": groups, "selected_page_ids": selected})
