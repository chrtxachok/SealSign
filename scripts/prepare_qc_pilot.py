"""Prepare a private, reproducible pilot for independent human review."""

import argparse
import csv
import hashlib
import json
import random
import shutil
from pathlib import Path, PurePosixPath

from PIL import Image, ImageDraw


def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def prepare(bundle, output, count, seed):
    bundle, output = Path(bundle), Path(output)
    if output.exists():
        raise ValueError("Output already exists")
    if count < 1:
        raise ValueError("Count must be positive")
    pages = [json.loads(line) for line in (bundle / "manifest.jsonl").read_text().splitlines()]
    coco = json.loads((bundle / "annotations.json").read_text())
    images = {image["page_id"]: image for image in coco["images"]}
    objects = {}
    for obj in coco["annotations"]:
        objects.setdefault(obj["image_id"], []).append(obj)
    # Historic test pages remain untouched during pilot and rule selection.
    eligible = [
        p
        for p in pages
        if p.get("original_split") == "train"
        and p.get("normalized_path")
        and not p.get("exclusion_reason")
        and p.get("review_status") == "unreviewed"
        and p["page_id"] in images
    ]
    eligible.sort(key=lambda p: p["page_id"])
    random.Random(seed).shuffle(eligible)
    selected, hashes, names = [], set(), set()
    for page in eligible:
        name = PurePosixPath(page["relative_path"]).name.split(".rf.")[0]
        if page["sha256"] in hashes or name in names:
            continue
        selected.append(page)
        hashes.add(page["sha256"])
        names.add(name)
        if len(selected) == count:
            break
    if len(selected) != count:
        raise ValueError("Not enough eligible distinct candidates")
    output.mkdir(parents=True)
    (output / "pages").mkdir()
    (output / "annotated").mkdir()
    rows = []
    try:
        for index, page in enumerate(selected, start=1):
            image = images[page["page_id"]]
            source = (bundle / image["file_name"]).resolve()
            if (
                not source.is_relative_to(bundle.resolve())
                or digest(source) != page["normalized_sha256"]
            ):
                raise ValueError("Image path or checksum mismatch")
            identifier = f"{index:03d}"
            shutil.copyfile(source, output / "pages" / f"{identifier}.png")
            with Image.open(source) as original:
                annotated = original.convert("RGB")
            draw = ImageDraw.Draw(annotated)
            for obj in objects.get(image["id"], []):
                x, y, w, h = obj["bbox"]
                draw.rectangle(
                    (x, y, x + w, y + h),
                    outline="red" if obj["category_id"] == 0 else "blue",
                    width=3,
                )
            annotated.save(output / "annotated" / f"{identifier}.png")
            rows.append(
                {
                    "sample": identifier,
                    "page_id": page["page_id"],
                    "stamp_reviewed": "",
                    "signature_reviewed": "",
                    "review_status": "",
                    "disputed": "",
                    "notes": "",
                }
            )
        with (output / "review-template.csv").open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        (output / "README.txt").write_text(
            "Сначала просмотрите pages/. Затем сравните с annotated/: "
            "красный — печать, синий — подпись.\n"
            "Сделайте личную копию review-template.csv. В полях stamp_reviewed и "
            "signature_reviewed укажите yes, no или uncertain по наличию объекта.\n"
            "В disputed и notes запишите сомнения и обнаруженные пропуски. "
            "После просмотра укажите reviewed или disputed в review_status.\n"
            "Пустые поля означают, что страница не проверена. "
            "Не публикуйте эти документы.\n",
            encoding="utf-8",
        )
        metadata = {
            "seed": seed,
            "count": count,
            "original_split": "train",
            "manifest_sha256": digest(bundle / "manifest.jsonl"),
            "annotations_sha256": digest(bundle / "annotations.json"),
            "page_ids": [row["page_id"] for row in rows],
            "reviewed": False,
            "accepted_for_training": False,
        }
        (output / "pilot.json").write_text(json.dumps(metadata, indent=2) + "\n")
    except Exception:
        shutil.rmtree(output)
        raise
    return {"selected": len(rows), "reviewed": False, "accepted_for_training": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    print(json.dumps(prepare(args.bundle, args.output, args.count, args.seed)))


if __name__ == "__main__":
    main()
