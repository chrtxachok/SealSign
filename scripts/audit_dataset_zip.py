"""Inspect a local ZIP without extraction; counts never certify reviewed originals."""

import argparse
import hashlib
import json
import stat
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}


def audit(path):
    components = {}
    evidence = []
    seen_paths = set()
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        if sum(entry.file_size for entry in entries) > 20 * 1024**3:
            raise ValueError("Uncompressed archive exceeds audit budget")
        for entry in entries:
            name = PurePosixPath(entry.filename)
            if (
                name.is_absolute()
                or ".." in name.parts
                or "\\" in entry.filename
                or stat.S_ISLNK(entry.external_attr >> 16)
                or entry.filename in seen_paths
            ):
                raise ValueError("Unsafe or repeated archive path")
            seen_paths.add(entry.filename)
            if entry.is_dir():
                continue
            component = name.parts[0] if len(name.parts) > 1 else "root"
            counts = components.setdefault(
                component,
                {
                    "images": 0,
                    "image_hashes": Counter(),
                    "hash_splits": {},
                    "label_files": 0,
                    "label_rows_by_source_class": Counter(),
                    "label_row_token_counts": Counter(),
                    "empty_labels": 0,
                },
            )
            # Reading every member verifies ZIP CRC, including non-image files.
            digest = hashlib.sha256()
            payload = bytearray()
            with archive.open(entry) as stream:
                while chunk := stream.read(1024 * 1024):
                    digest.update(chunk)
                    if name.suffix.lower() in {".txt", ".yaml", ".yml", ".md"}:
                        if len(payload) + len(chunk) > 4 * 1024**2:
                            raise ValueError("Text member exceeds audit budget")
                        payload.extend(chunk)
            if name.suffix.lower() in IMAGE_SUFFIXES:
                counts["images"] += 1
                counts["image_hashes"][digest.hexdigest()] += 1
                split = next(
                    (part for part in name.parts if part in {"train", "valid", "val", "test"}),
                    "unspecified",
                )
                counts["hash_splits"].setdefault(digest.hexdigest(), set()).add(split)
            if "labels" in name.parts and name.suffix == ".txt":
                counts["label_files"] += 1
                rows = payload.decode("utf-8").splitlines()
                rows = [row.split() for row in rows if row.strip()]
                counts["empty_labels"] += not rows
                for row in rows:
                    counts["label_rows_by_source_class"][row[0]] += 1
                    counts["label_row_token_counts"][str(len(row))] += 1
            if name.suffix.lower() in {".yaml", ".yml", ".md"} or "license" in name.name.lower():
                evidence.append(
                    {"path": entry.filename, "bytes": entry.file_size, "sha256": digest.hexdigest()}
                )
    all_hashes = Counter()
    for counts in components.values():
        hashes = counts.pop("image_hashes")
        counts["exact_duplicate_hash_groups_crossing_upstream_splits"] = sum(
            len(splits) > 1 for splits in counts.pop("hash_splits").values()
        )
        all_hashes.update(hashes)
        counts["distinct_image_sha256"] = len(hashes)
        counts["extra_exact_copies"] = sum(hashes.values()) - len(hashes)
    with path.open("rb") as stream:
        archive_hash = hashlib.file_digest(stream, "sha256").hexdigest()
    return {
        "archive": path.name,
        "bytes": path.stat().st_size,
        "sha256": archive_hash,
        "zip_crc_all_members_verified": True,
        "components": components,
        "distinct_image_sha256_global": len(all_hashes),
        "text_evidence": evidence,
        "original_pages_verified": False,
        "images_decoded": False,
        "visual_qc_performed": False,
        "accepted_for_training": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = audit(args.archive)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
