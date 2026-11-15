"""Count bright-green pixel candidates; visual inspection is still required."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops


def audit(bundle, output):
    if output.exists():
        raise ValueError("Output already exists")
    bundle = bundle.resolve()
    manifest = bundle / "manifest.jsonl"
    pages = [json.loads(line) for line in manifest.read_text().splitlines()]
    selected = [
        page
        for page in pages
        if page.get("normalized_path") and page.get("source_images_root", "").startswith("stamps/")
    ]
    if not selected:
        raise ValueError("No stamp-source images found")
    rows = []
    for page in selected:
        path = (bundle / page["normalized_path"]).resolve()
        if not path.is_relative_to(bundle):
            raise ValueError("Image escapes bundle")
        with path.open("rb") as f:
            digest = hashlib.file_digest(f, "sha256").hexdigest()
        if digest != page["normalized_sha256"]:
            raise ValueError("Image checksum mismatch")
        with Image.open(path) as image:
            red, green, blue = image.convert("RGB").split()
            mask = ImageChops.multiply(
                ImageChops.multiply(
                    red.point(lambda x: 255 if x <= 40 else 0),
                    green.point(lambda x: 255 if x >= 200 else 0),
                ),
                blue.point(lambda x: 255 if x <= 40 else 0),
            )
            count = mask.histogram()[255]
        rows.append(
            {"page_id": page["page_id"], "bright_green_pixels": count, "candidate": count >= 30}
        )
    with manifest.open("rb") as f:
        manifest_hash = hashlib.file_digest(f, "sha256").hexdigest()
    result = {
        "schema_version": "sealsign-green-pixel-audit-v1",
        "scope": "normalized decoded stamps component; excluded pages omitted",
        "images": len(rows),
        "candidates": sum(row["candidate"] for row in rows),
        "rgb_rule": "R<=40 and G>=200 and B<=40",
        "minimum_pixels": 30,
        "manifest_sha256": manifest_hash,
        "candidate_is_not_verified_annotation": True,
        "accepted_for_training": False,
    }
    output.mkdir(parents=True)
    with (output / "candidates.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["page_id", "bright_green_pixels", "candidate"])
        writer.writeheader()
        writer.writerows(rows)
    (output / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.bundle, args.output)))


if __name__ == "__main__":
    main()
