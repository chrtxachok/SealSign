import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import upper_bound_backgrounds as bound  # noqa: E402


def test_upper_bound_counts_only_independent_links(tmp_path, monkeypatch):
    def write(name, value):
        path = tmp_path / name
        path.write_text(json.dumps(value))
        return path

    monkeypatch.setattr(
        bound,
        "validate",
        lambda *_: {
            "reviewed_components": 3,
            "additional_variants": 2,
            "remaining_candidate_components": 1,
        },
    )
    monkeypatch.setattr(bound, "sha256", lambda _: "hash")
    write("inventory.json", [{}, {}, {}, {}, {}, {}])
    write("report.json", {"images": 6})
    review = write(
        "review.json",
        {"reviewed_components": [{"component_id": i, "background_groups": [{}]} for i in "abc"]},
    )
    queue = write(
        "queue.json", {"candidate_csv_sha256": "hash", "groups": [{"group_id": i} for i in "abc"]}
    )

    def link(a, b):
        return {
            "positions": ["abc".index(a) + 1, "abc".index(b) + 1],
            "component_ids": [a, b],
            "status": "visually_same_document",
            "canonical_groups_modified": False,
        }

    links = write("links.json", {"links": [link("a", "b"), link("b", "c"), link("a", "c")]})
    result = bound.calculate(tmp_path, review, queue, links)
    assert result["independent_cross_component_links"] == 2
    assert result["upper_bound_originals"] == 2
    links.write_text(json.dumps({"links": [link("a", "b") | {"positions": [1, 3]}]}))
    with pytest.raises(ValueError, match="Link not tied"):
        bound.calculate(tmp_path, review, queue, links)
