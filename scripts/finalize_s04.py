"""Freeze the expanded, reviewed corpus and export its grouped YOLO split."""

import argparse
import hashlib
import io
import json
from collections import Counter, defaultdict
from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from PIL import Image, ImageOps

from scripts.audit_s04_leakage import ARCHIVES, HOLDOUT_MANIFEST, HOLDOUT_SPLIT, MERGED, REVIEW
from scripts.prepare_provisional_split import assign_groups
from scripts.validate_s04_disputes import load_dispute_decisions, validate_bbox, validate_class


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def connect_groups(pages, audit, reviews, checksums):
    parents = {index: index for index in pages}
    expected = {(p["a"], p["b"]): p for p in audit["pairs"]}
    if len(expected) != len(audit["pairs"]):
        raise ValueError("Repeated leakage candidate")
    seen = set()
    counts = Counter()

    def root(index):
        while index != parents[index]:
            index = parents[index]
        return index

    for path in reviews:
        evidence = read(path)
        if (
            evidence["schema_version"] != "sealsign-leakage-review-v1"
            or evidence["merged_sha256"] != checksums[MERGED.name]
        ):
            raise ValueError(f"Invalid leakage reviews in {path}")
        for pair in evidence["pairs"]:
            a, b = pair["a"], pair["b"]
            key = (a, b)
            decision = pair["decision"]
            if (
                key in seen
                or a not in pages
                or b not in pages
                or a >= b
                or not pair["reason"].strip()
            ):
                raise ValueError(f"Invalid visual pair {key}")
            seen.add(key)
            counts[decision] += 1
            if decision in {"same_page", "same_document", "possible_same_document"}:
                ra, rb = sorted((root(a), root(b)))
                parents[rb] = ra
            elif decision != "different_document" or (
                key in expected
                and (expected[key]["same_source_bytes"] or expected[key]["same_rgb_pixels"])
            ):
                raise ValueError(f"Invalid leakage decision for {key}")
    if not expected.keys() <= seen:
        raise ValueError("Leakage candidates lack visual decisions or intersect teaching test")
    return {i: root(i) for i in pages}, counts


def finalize(output):
    decisions, qc = load_dispute_decisions(MERGED, REVIEW)
    if qc["not_yet_adjudicated_pages"]:
        raise ValueError("Some disputed pages still await adjudication")
    merged = read(MERGED)
    queue_file = REVIEW / "queue.json"
    audit_file = REVIEW / "additional-leakage-candidates-v1.json"
    reviews = [
        REVIEW / "additional-leakage-reviewed-v1.json",
        *sorted(REVIEW.glob("additional-leakage-review-supplement-v*.json")),
    ]
    checksums = {
        p.name: digest(p)
        for p in [MERGED, queue_file, HOLDOUT_SPLIT, HOLDOUT_MANIFEST, audit_file, *reviews]
    }
    audit = read(audit_file)
    if (
        audit["input_sha256"]
        != {p.name: checksums[p.name] for p in (MERGED, HOLDOUT_SPLIT, HOLDOUT_MANIFEST)}
        or merged["queue_sha256"] != checksums[queue_file.name]
        or merged["teaching_split_sha256"] != checksums[HOLDOUT_SPLIT.name]
    ):
        raise ValueError("Queue, test or audit input mismatch")
    pages = {row["queue_index"]: row for row in merged["pages"]}
    queue = read(queue_file)["selected"]
    if len(queue) != len(pages) or [(p["archive"], p["file"]) for p in pages.values()] != [
        (p["archive"], p["file"]) for p in queue
    ]:
        raise ValueError("Merged pages differ from the source queue")
    holdout_ids = {p for group in read(HOLDOUT_SPLIT)["splits"]["test"] for p in group}
    holdout = {
        p["page_id"]: p["sha256"]
        for p in map(json.loads, HOLDOUT_MANIFEST.read_text(encoding="utf-8").splitlines())
        if p["page_id"] in holdout_ids
    }
    digests = {p["sha256"] for p in pages.values()}
    if (
        holdout.keys() != holdout_ids
        or len(holdout) != audit["teaching_test_pages"]
        or len(pages) != audit["candidate_pages"]
        or len(digests) != len(pages)
        or digests.intersection(holdout.values())
    ):
        raise ValueError("Unexpected duplicate or teaching-test coverage")
    groups, pair_counts = connect_groups(pages, audit, reviews, checksums)

    accepted_groups = defaultdict(list)
    manifest = []
    labels = {}
    for index, page in pages.items():
        record = {
            "page_id": f"s04-{index:04d}",
            "queue_index": index,
            "split": None,
            "group_id": groups[index],
            "annotation_version": "s04-expanded-v1",
            **{k: page[k] for k in ("archive", "file", "sha256", "width", "height")},
            "review_status": page["review_status"],
        }
        manifest.append(record)
        review = decisions.get(index, {})
        unresolved = [r for r in review.get("regions", []) if r["decision"] == "unresolved"]
        if unresolved:
            record["exclusion_reason"] = "unresolved_regions"
            record["unresolved_regions"] = unresolved
            continue
        if page["review_status"] not in {"reviewed", "reviewed_empty", "disputed"}:
            raise ValueError(f"Unreviewed status for {index}: {page['review_status']}")
        annotations = list(page["annotations"])
        if (
            page["review_status"] == "reviewed_empty"
            and annotations
            or page["review_status"] == "reviewed"
            and not annotations
        ):
            raise ValueError(f"Annotation status mismatch for {index}")
        annotations.extend(
            {"category_id": r["category_id"], "bbox": r.get("replacement_bbox", r["bbox"])}
            for r in review.get("regions", [])
            if r["decision"] == "accept"
        )
        annotations.extend(review.get("additional_annotations", []))
        result = {}
        for annotation in annotations:
            category, bbox = annotation["category_id"], annotation["bbox"]
            validate_class(category)
            validate_bbox(bbox, page["width"], page["height"])
            result[(category, *bbox)] = {"category_id": category, "bbox": bbox}
        labels[index] = list(result.values())
        record["review_status"] = "positive" if result else "negative"
        accepted_groups[groups[index]].append(index)
    if len(pages) - len(labels) != qc["still_unresolved_pages"]:
        raise ValueError("Unexpected number of excluded pages")
    split = assign_groups(
        {"groups": list(accepted_groups.values()), "selected_page_ids": list(labels)}
    )
    for part, parts in split.items():
        for group in parts:
            for index in group:
                manifest[index - 1]["split"] = part

    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=output.parent) as temp:
        bundle = Path(temp) / "bundle"
        bundle.mkdir()
        summary = export(bundle, manifest, labels, split)
        (bundle / "manifest.jsonl").write_text(
            "".join(json.dumps(p, ensure_ascii=False) + "\n" for p in manifest), encoding="utf-8"
        )
        dump(bundle / "annotations.json", {"classes": merged["classes"], "pages": labels})
        dump(
            bundle / "split.json",
            {"seed": 42, "splits": split, "teaching_test_ids": sorted(holdout_ids)},
        )
        dump(
            bundle / "qc-report.json",
            {
                "qc": qc,
                "inputs_sha256": checksums,
                "visual_pairs": pair_counts,
                "splits": summary,
                "output_sha256": {
                    name: digest(bundle / name)
                    for name in ("manifest.jsonl", "annotations.json", "split.json")
                },
            },
        )
        bundle.rename(output)
    print(json.dumps(summary, indent=2))


def export(bundle, manifest, labels, split, *, archives_dir=ARCHIVES, newline=None):
    summary = {}
    for part in split:
        (bundle / "images" / part).mkdir(parents=True)
        (bundle / "labels" / part).mkdir(parents=True)
        summary[part] = Counter(pages=0, negatives=0, stamp=0, signature=0, groups=len(split[part]))
    with ExitStack() as stack:
        archives = {
            name: stack.enter_context(ZipFile(archives_dir / name))
            for name in ("train.zip", "val.zip", "test.zip")
        }
        for p in manifest:
            part = p["split"]
            if part is None:
                continue
            raw = archives[p["archive"]].read(p["file"])
            if hashlib.sha256(raw).hexdigest() != p["sha256"]:
                raise ValueError(f"Image checksum mismatch at {p['page_id']}")
            width, height = p["width"], p["height"]
            image_file = bundle / "images" / part / f"{p['page_id']}.png"
            with Image.open(io.BytesIO(raw)) as original:
                image = ImageOps.exif_transpose(original).convert("RGB")
                if image.size != (width, height):
                    raise ValueError(f"Image geometry mismatch at {p['page_id']}")
                image.save(image_file, compress_level=1)
            p["export_sha256"] = digest(image_file)
            summary[part]["pages"] += 1
            annotations = labels[p["queue_index"]]
            summary[part]["negatives"] += not annotations
            lines = []
            for annotation in annotations:
                category = annotation["category_id"]
                x, y, w, h = annotation["bbox"]
                summary[part][("stamp", "signature")[category]] += 1
                values = ((x + w / 2) / width, (y + h / 2) / height, w / width, h / height)
                lines.append(f"{category} " + " ".join(f"{value:.10f}" for value in values))
            label_file = bundle / "labels" / part / f"{p['page_id']}.txt"
            label_file.write_text(
                "".join(line + "\n" for line in lines), encoding="ascii", newline=newline
            )
            p["label_sha256"] = digest(label_file)
    (bundle / "dataset.yaml").write_text(
        "train: images/train\nval: images/val\ntest: images/test\nnames: [stamp, signature]\n",
        encoding="ascii",
        newline=newline,
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    finalize(parser.parse_args().output)
