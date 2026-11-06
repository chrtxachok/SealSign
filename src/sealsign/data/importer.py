"""Research-only ZIP import. Every page remains unreviewed until separate QC."""

import hashlib
import io
import json
import re
import stat
import tempfile
import warnings
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath

from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError

from sealsign.data.geometry import parse_labels, to_yolo

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}
SCHEMA_VERSION = "sealsign-data-v1"


def safe_path(value):
    path = PurePosixPath(value)
    if (
        not value
        or path.is_absolute()
        or ".." in path.parts
        or "\\" in value
        or ":" in value
        or str(path) != value.rstrip("/")
    ):
        raise ValueError("Unsafe or noncanonical relative path")
    return path


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def validate_sources(config):
    if not re.fullmatch(r"[a-zA-Z0-9_.-]+", config["archive_id"]):
        raise ValueError("Invalid archive_id")
    if not re.fullmatch(r"[0-9a-f]{64}", config["sha256"]):
        raise ValueError("Expected archive SHA-256")
    if not config["sources"]:
        raise ValueError("Empty sources")
    for source in config["sources"]:
        safe_path(source["images"])
        if source.get("labels") is not None:
            safe_path(source["labels"])
        if source["format"] not in {"bbox", "polygon"}:
            raise ValueError("Unsupported format")
        mapping = source["class_map"]
        if not mapping or any(
            not key.isdecimal() or type(value) is not int or value not in {0, 1}
            for key, value in mapping.items()
        ):
            raise ValueError("Explicit source class mapping is required")


def zip_inventory(archive):
    entries = archive.infolist()
    if sum(entry.file_size for entry in entries) > 20 * 1024**3:
        raise ValueError("ZIP exceeds uncompressed budget")
    seen = set()
    for entry in entries:
        safe_path(entry.filename)
        if entry.filename in seen or stat.S_ISLNK(entry.external_attr >> 16):
            raise ValueError("Repeated path or symlink in ZIP")
        seen.add(entry.filename)
    return {entry.filename: entry for entry in entries if not entry.is_dir()}


def read_member(archive, entry, limit):
    if entry.file_size > limit:
        raise ValueError("Member exceeds size budget")
    return archive.read(entry)  # zipfile verifies CRC, no archive paths are extracted.


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def import_zip(archive_path, config, output, preview_limit=12):
    """Create a new bundle atomically; retain failed pages in the inventory."""
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise ValueError("Output already exists")
    if not 0 <= preview_limit <= 200:
        raise ValueError("Preview limit must be 0..200")
    validate_sources(config)
    archive_hash = sha256(archive_path)
    if archive_hash != config["sha256"]:
        raise ValueError("Archive SHA-256 mismatch")
    output.parent.mkdir(parents=True, exist_ok=True)
    with (
        zipfile.ZipFile(archive_path) as archive,
        tempfile.TemporaryDirectory(dir=output.parent, prefix=".sealsign-import-") as temporary,
    ):
        entries = zip_inventory(archive)
        assignments = {}
        expected_labels = set()
        for source in config["sources"]:
            root = source["images"] + "/"
            images = sorted(
                name
                for name in entries
                if name.startswith(root) and PurePosixPath(name).suffix.lower() in IMAGE_SUFFIXES
            )
            if not images:
                raise ValueError("Source contains no images")
            for name in images:
                if name in assignments:
                    raise ValueError("Overlapping source image roots")
                relative = PurePosixPath(name).relative_to(source["images"])
                label = (
                    str(PurePosixPath(source["labels"]) / relative.with_suffix(".txt"))
                    if source.get("labels")
                    else None
                )
                if label in expected_labels:
                    raise ValueError("Ambiguous image-to-label association")
                if label:
                    expected_labels.add(label)
                assignments[name] = (source, label)
        orphan_labels = sum(
            name.startswith(source["labels"] + "/")
            and name.endswith(".txt")
            and name not in expected_labels
            for source in config["sources"]
            if source.get("labels")
            for name in entries
        )
        if orphan_labels:
            raise ValueError("Orphan labels in configured source")
        target = Path(temporary) / "bundle"
        for folder in ("images", "unreviewed-yolo", "previews"):
            (target / folder).mkdir(parents=True)
        pages, coco_images, annotations = [], [], []
        previews = 0
        for name, (source, label) in sorted(assignments.items()):
            page_id = hashlib.sha256(f"{config['archive_id']}\0{name}".encode()).hexdigest()
            page = {
                "page_id": page_id,
                "archive_id": config["archive_id"],
                "relative_path": name,
                "source_document_id": None,
                "group_id": None,
                "sha256": None,
                "width": None,
                "height": None,
                "decode_status": "not_attempted",
                "duplicate_group": None,
                "review_status": "unreviewed",
                "annotation_version": SCHEMA_VERSION,
                "split": None,
                "original_split": source.get("original_split"),
                "exclusion_reason": None,
                "source_images_root": source["images"],
                "source_label_path": label,
                "class_map": source["class_map"],
                "source_format": source["format"],
                "annotation_status": "missing",
                "normalized_path": None,
            }
            pages.append(page)
            try:
                raw = read_member(archive, entries[name], 64 * 1024**2)
                page["sha256"] = hashlib.sha256(raw).hexdigest()
                with warnings.catch_warnings():
                    warnings.simplefilter("error", Image.DecompressionBombWarning)
                    with Image.open(io.BytesIO(raw)) as image:
                        if (
                            image.width * image.height > 50_000_000
                            or getattr(image, "n_frames", 1) != 1
                        ):
                            raise ValueError("Image exceeds pixel budget or is multipage")
                        image.load()
                        orientation = image.getexif().get(274, 1)
                        if orientation not in range(1, 9):
                            raise ValueError("Invalid EXIF orientation")
                        raw_width, raw_height = image.size
                        normalized = ImageOps.exif_transpose(image).convert("RGB")
                page.update(
                    width=normalized.width,
                    height=normalized.height,
                    decode_status="ok",
                    source_width=raw_width,
                    source_height=raw_height,
                    source_exif_orientation=orientation,
                )
            except (
                OSError,
                ValueError,
                UnidentifiedImageError,
                Image.DecompressionBombError,
                Image.DecompressionBombWarning,
            ) as exc:
                page.update(decode_status="error", exclusion_reason=type(exc).__name__)
                continue
            objects = []
            try:
                if label in entries:
                    text = read_member(archive, entries[label], 4 * 1024**2).decode("utf-8")
                    objects = parse_labels(
                        text,
                        source["format"],
                        source["class_map"],
                        raw_width,
                        raw_height,
                        orientation,
                    )
                    page["annotation_status"] = "present" if objects else "empty_unreviewed"
            except (ValueError, UnicodeError) as exc:
                page.update(annotation_status="invalid", exclusion_reason=str(exc))
                continue
            image_id = len(coco_images) + 1
            image_path = f"images/{page_id}.png"
            normalized.save(target / image_path)
            page.update(normalized_path=image_path, normalized_sha256=sha256(target / image_path))
            coco_images.append(
                {
                    "id": image_id,
                    "page_id": page_id,
                    "file_name": image_path,
                    "width": normalized.width,
                    "height": normalized.height,
                }
            )
            for obj in objects:
                x, y, w, h = obj["bbox"]
                annotations.append(
                    {
                        **obj,
                        "id": len(annotations) + 1,
                        "image_id": image_id,
                        "area": w * h,
                        "iscrowd": 0,
                    }
                )
            if label in entries:
                (target / "unreviewed-yolo" / f"{page_id}.txt").write_text(
                    to_yolo(objects, normalized.width, normalized.height), encoding="utf-8"
                )
            if previews < preview_limit:
                draw = ImageDraw.Draw(normalized)
                for obj in objects:
                    x, y, w, h = obj["bbox"]
                    color = "red" if obj["category_id"] == 0 else "blue"
                    draw.rectangle((x, y, x + w, y + h), outline=color, width=2)
                normalized.thumbnail((1200, 1200))
                normalized.save(target / "previews" / f"{page_id}.png")
                previews += 1
        counts = Counter(page["sha256"] for page in pages if page["sha256"])
        for page in pages:
            if counts[page["sha256"]] > 1:
                page["duplicate_group"] = page["sha256"]
        write_json(
            target / "annotations.json",
            {
                "schema_version": SCHEMA_VERSION,
                "images": coco_images,
                "annotations": annotations,
                "categories": [{"id": 0, "name": "stamp"}, {"id": 1, "name": "signature"}],
            },
        )
        (target / "manifest.jsonl").write_text(
            "".join(json.dumps(page, ensure_ascii=False) + "\n" for page in pages), encoding="utf-8"
        )
        write_json(target / "import-config.json", config)
        report = {
            "schema_version": SCHEMA_VERSION,
            "archive_sha256": archive_hash,
            "config_sha256": sha256(target / "import-config.json"),
            "input_images": len(pages),
            "canonical_images": len(coco_images),
            "excluded_images": sum(p["exclusion_reason"] is not None for p in pages),
            "annotation_status_counts": dict(Counter(p["annotation_status"] for p in pages)),
            "objects_by_class": dict(Counter(str(a["category_id"]) for a in annotations)),
            "accepted_for_training": False,
            "review_status": "unreviewed",
        }
        write_json(target / "report.json", report)
        target.rename(output)
    return report
