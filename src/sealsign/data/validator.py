"""Validate the generated canonical bundle without promoting its QC status."""

import json
import math
from pathlib import Path

from PIL import Image

from sealsign.data.geometry import to_yolo
from sealsign.data.importer import SCHEMA_VERSION, safe_path, sha256


def validate_bundle(directory):
    root = Path(directory).resolve()
    pages = [json.loads(line) for line in (root / "manifest.jsonl").read_text().splitlines()]
    coco = json.loads((root / "annotations.json").read_text())
    if coco["schema_version"] != SCHEMA_VERSION:
        raise ValueError("Unsupported schema")
    if coco["categories"] != [{"id": 0, "name": "stamp"}, {"id": 1, "name": "signature"}]:
        raise ValueError("Incorrect canonical categories")
    page_map = {page["page_id"]: page for page in pages}
    if len(page_map) != len(pages):
        raise ValueError("Duplicate page_id")
    images = {}
    for image in coco["images"]:
        if image["id"] in images:
            raise ValueError("Duplicate image ID")
        images[image["id"]] = image
        page = page_map[image["page_id"]]
        relative = str(safe_path(image["file_name"]))
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("Missing or escaped image")
        if relative != page["normalized_path"] or sha256(path) != page["normalized_sha256"]:
            raise ValueError("Image checksum or manifest path mismatch")
        with Image.open(path) as decoded:
            decoded.load()
            if decoded.size != (image["width"], image["height"]):
                raise ValueError("Image dimensions mismatch")
        if (page["width"], page["height"]) != (image["width"], image["height"]):
            raise ValueError("Manifest dimensions mismatch")
    normalized_pages = {p["page_id"] for p in pages if p["normalized_path"]}
    if normalized_pages != {image["page_id"] for image in images.values()}:
        raise ValueError("Orphan manifest image")
    seen = set()
    annotation_ids = set()
    for obj in coco["annotations"]:
        image = images[obj["image_id"]]
        if type(obj["category_id"]) is not int or obj["category_id"] not in {0, 1}:
            raise ValueError("Invalid canonical class")
        x, y, w, h = obj["bbox"]
        if (
            not all(math.isfinite(v) for v in (x, y, w, h))
            or x < 0
            or y < 0
            or w <= 0
            or h <= 0
            or x + w > image["width"] + 1e-7
            or y + h > image["height"] + 1e-7
        ):
            raise ValueError("Invalid canonical box")
        key = (obj["image_id"], obj["category_id"], *obj["bbox"])
        if key in seen or obj["id"] in annotation_ids:
            raise ValueError("Duplicate annotation")
        seen.add(key)
        annotation_ids.add(obj["id"])
    if len(images) != len(normalized_pages):
        raise ValueError("Repeated canonical page")
    for image in images.values():
        page = page_map[image["page_id"]]
        label_path = root / "unreviewed-yolo" / f"{page['page_id']}.txt"
        if page["annotation_status"] != "missing":
            objects = [obj for obj in coco["annotations"] if obj["image_id"] == image["id"]]
            if label_path.read_text() != to_yolo(objects, image["width"], image["height"]):
                raise ValueError("Derived YOLO differs from canonical annotations")
        elif label_path.exists():
            raise ValueError("Unexpected label for missing source annotation")
    return {
        "pages": len(pages),
        "images": len(images),
        "annotations": len(seen),
        "accepted_for_training": False,
    }
