"""Protect audit counts from repeated pagination and metadata version races."""

import importlib.util
import json
from io import BytesIO
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "kaggle_audit", Path(__file__).resolve().parents[1] / "scripts/audit_kaggle_metadata.py"
)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def test_image_counts_do_not_claim_unique_originals():
    files = [
        {"name": "train/images/page.rf.aaa.jpg", "totalBytes": 10},
        {"name": "valid/images/page.rf.bbb.jpg", "totalBytes": 10},
        {"name": "train/labels/page.rf.aaa.txt", "totalBytes": 5},
    ]
    result = audit.summarize_files(files)
    assert result["image_entries"] == 2
    assert result["distinct_image_name_prefixes_before_rf"] == 1
    assert result["images_by_upstream_split"] == {"train": 1, "valid": 1}
    assert result["original_pages_verified"] is False
    assert result["deduplication_performed"] is False


def test_duplicate_listing_paths_fail_closed():
    with pytest.raises(ValueError, match="Repeated file paths"):
        audit.summarize_files([{"name": "page.jpg", "totalBytes": 5}] * 2)


@pytest.mark.parametrize("version_after", [1, 2])
def test_collect_follows_pagination_and_rejects_version_changes(
    tmp_path, monkeypatch, version_after
):
    metadata = {
        "currentVersionNumber": 1,
        "lastUpdated": "fixed",
        "totalBytes": 10,
        "licenseName": "Unknown",
    }
    responses = iter(
        [
            metadata,
            {"datasetFiles": [{"name": "a.jpg", "totalBytes": 5}], "nextPageToken": "next"},
            {"datasetFiles": [{"name": "b.jpg", "totalBytes": 5}]},
            {**metadata, "currentVersionNumber": version_after},
        ]
    )
    urls = []

    def fetch(url, timeout):
        urls.append(url)
        return BytesIO(json.dumps(next(responses)).encode())

    monkeypatch.setattr(audit, "urlopen", fetch)
    if version_after != 1:
        with pytest.raises(ValueError, match="Dataset changed"):
            audit.collect("owner/dataset", tmp_path)
    else:
        result = audit.collect("owner/dataset", tmp_path)
        assert result["image_entries"] == 2
        assert result["listing_complete"] is True
        assert result["accepted_for_training"] is False
        assert "pageToken=next" in urls[2]
        assert all("pageToken" not in item["endpoint"] for item in result["evidence"])
