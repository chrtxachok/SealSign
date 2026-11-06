"""Explicit YOLO geometry conversion in the raw image coordinate system."""

import math


def orient_point(x, y, width, height, orientation):
    return {
        1: (x, y),
        2: (width - x, y),
        3: (width - x, height - y),
        4: (x, height - y),
        5: (y, x),
        6: (height - y, x),
        7: (height - y, width - x),
        8: (y, width - x),
    }[orientation]


def parse_labels(text, kind, class_map, width, height, orientation=1):
    """Return instance boxes; reject malformed rows instead of silently clipping."""
    if kind not in {"bbox", "polygon"} or orientation not in range(1, 9):
        raise ValueError("Unsupported label format or EXIF orientation")
    result = []
    for line in text.splitlines():
        if not line.strip():
            continue
        tokens = line.split()
        if tokens[0] not in class_map:
            raise ValueError("Unmapped source class")
        category = class_map[tokens[0]]
        if type(category) is not int or category not in {0, 1}:
            raise ValueError("Canonical class must be 0 or 1")
        coords = [float(value) for value in tokens[1:]]
        if not all(math.isfinite(value) and 0 <= value <= 1 for value in coords):
            raise ValueError("Nonfinite or out-of-range coordinates")
        if kind == "bbox":
            if len(coords) != 4:
                raise ValueError("Expected cx cy w h")
            cx, cy, w, h = coords
            if w <= 0 or h <= 0:
                raise ValueError("Nonpositive box")
            points = [(cx - w / 2, cy - h / 2), (cx + w / 2, cy + h / 2)]
        else:
            if len(coords) < 6 or len(coords) % 2:
                raise ValueError("Expected at least three polygon vertices")
            points = list(zip(coords[::2], coords[1::2], strict=True))
        if any(x < -1e-9 or x > 1 + 1e-9 or y < -1e-9 or y > 1 + 1e-9 for x, y in points):
            raise ValueError("Box extends outside image")
        points = [(min(1.0, max(0.0, x)), min(1.0, max(0.0, y))) for x, y in points]
        points = [
            orient_point(x * width, y * height, width, height, orientation) for x, y in points
        ]
        xs, ys = zip(*points, strict=True)
        box = [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]
        if min(box[2:]) <= 0:
            raise ValueError("Degenerate polygon or box")
        obj = {"category_id": category, "bbox": box}
        if obj in result:
            raise ValueError("Duplicate instance box")
        result.append(obj)
    return result


def to_yolo(objects, width, height):
    lines = []
    for obj in objects:
        x, y, w, h = obj["bbox"]
        lines.append(
            f"{obj['category_id']} {(x + w / 2) / width:.10f} "
            f"{(y + h / 2) / height:.10f} {w / width:.10f} {h / height:.10f}"
        )
    return "\n".join(lines) + ("\n" if lines else "")
