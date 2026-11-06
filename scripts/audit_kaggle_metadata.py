"""Collect public Kaggle metadata; never treat file listings as reviewed pages."""

import argparse
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from urllib.parse import urlencode
from urllib.request import urlopen

BASE_URL = "https://www.kaggle.com/api/v1/datasets/"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}


def summarize_files(files):
    """Count entries, not originals; reject duplicate paths in paginated responses."""
    names = [entry["name"] for entry in files]
    if len(set(names)) != len(names):
        raise ValueError("Repeated file paths: pagination cannot establish a complete inventory")
    images = [name for name in names if PurePosixPath(name).suffix.lower() in IMAGE_SUFFIXES]
    splits = Counter()
    for name in images:
        parts = PurePosixPath(name).parts
        split = next((part for part in parts if part in {"train", "valid", "val", "test"}), None)
        splits[split or "unspecified"] += 1
    # Roboflow suffix removal is a name-based clue, never a deduplication proof.
    stems = [PurePosixPath(name).name.split(".rf.")[0] for name in images]
    return {
        "file_entries": len(files),
        "listed_bytes": sum(entry["totalBytes"] for entry in files),
        "image_entries": len(images),
        "images_by_upstream_split": dict(sorted(splits.items())),
        "images_by_directory": dict(
            sorted(Counter(str(PurePosixPath(name).parent) for name in images).items())
        ),
        "distinct_image_name_prefixes_before_rf": len(set(stems)),
        "original_pages_verified": False,
        "deduplication_performed": False,
    }


def collect(ref, raw_dir):
    if len(ref.split("/")) != 2 or any(not part for part in ref.split("/")):
        raise ValueError("Expected owner/dataset")
    target = raw_dir / ref.replace("/", "--")
    target.mkdir(parents=True, exist_ok=True)
    evidence = []

    def fetch(route, filename):
        url = BASE_URL + route
        with urlopen(url, timeout=30) as response:
            raw = response.read()
        data = json.loads(raw)
        if data.get("errorMessage"):
            raise ValueError(data["errorMessage"])
        (target / filename).write_bytes(raw)
        evidence.append(
            {
                "endpoint": url.split("?")[0],
                "raw_file": filename,
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
        return data

    before = fetch("view/" + ref, "view-before.json")
    files = []
    token = None
    seen_tokens = set()
    for page in range(100):
        query = {"pageSize": 200}
        if token:
            query["pageToken"] = token
        listing = fetch("list/" + ref + "?" + urlencode(query), f"files-{page:03}.json")
        files.extend(listing["datasetFiles"])
        token = listing.get("nextPageToken")
        if not token:
            break
        if token in seen_tokens:
            raise ValueError("Repeated pagination token")
        seen_tokens.add(token)
    else:
        raise ValueError("Pagination limit exceeded; inventory incomplete")
    after = fetch("view/" + ref, "view-after.json")
    for field in ("currentVersionNumber", "lastUpdated", "totalBytes"):
        if before[field] != after[field]:
            raise ValueError("Dataset changed during listing; rerun audit")
    return {
        "ref": ref,
        "metadata_url": BASE_URL + "view/" + ref,
        "version": before["currentVersionNumber"],
        "last_updated": before["lastUpdated"],
        "license_name_from_api": before["licenseName"],
        "metadata_total_bytes": before["totalBytes"],
        "listing_complete": True,
        "listing_version_note": "List endpoint is unversioned; view checked before and after",
        **summarize_files(files),
        "accepted_for_training": False,
        "evidence": evidence,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("refs", nargs="+")
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = {
        "observed_at_utc": datetime.now(UTC).isoformat(),
        "scope": "Public API metadata and complete listings; no image or label QC",
        "datasets": [collect(ref, args.raw_dir) for ref in args.refs],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for dataset in report["datasets"]:
        print(dataset["ref"], dataset["version"], dataset["image_entries"], "image entries")


if __name__ == "__main__":
    main()
