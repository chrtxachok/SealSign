"""Work batching must not repeat the pilot or lose remaining source pages."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "batch_plan", Path(__file__).parents[1] / "scripts/prepare_annotation_batch.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_plan_is_disjoint_complete_and_reproducible():
    names = [f"page-{i:04d}" for i in range(283)]
    excluded = names[:50]
    result = module.plan(names, excluded)
    assert result == module.plan(list(reversed(names)), excluded)
    flat = [n for batch in result for n in batch]
    assert len(flat) == len(set(flat)) == 233
    assert not set(flat) & set(excluded)
    assert set(flat) == set(names) - set(excluded)
    assert list(map(len, result)) == [100, 100, 33]


def test_plan_rejects_unknown_pilot_page():
    with pytest.raises(ValueError):
        module.plan(["one"], ["absent"])
