"""Run the frozen detector in the coordinates of a normalized page."""

import hashlib
import json
import math
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageOps, UnidentifiedImageError

LABELS = ("stamp", "signature")
MAX_BYTES = 20 * 1024 * 1024
MAX_PIXELS = 16_000_000


class ImageInputError(ValueError):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def decode_page(data: bytes) -> Image.Image:
    if len(data) > MAX_BYTES:
        raise ImageInputError(413, "Файл больше 20 МиБ.")
    if not data:
        raise ImageInputError(422, "Файл пуст.")
    try:
        with Image.open(BytesIO(data)) as source:
            if source.format not in {"JPEG", "PNG"}:
                raise ImageInputError(415, "Загрузите изображение JPEG или PNG.")
            if source.width * source.height > MAX_PIXELS:
                raise ImageInputError(413, "Изображение больше 16 мегапикселей.")
            if getattr(source, "n_frames", 1) != 1:
                raise ImageInputError(415, "Загрузите изображение с одним кадром.")
            page = ImageOps.exif_transpose(source)
            if "A" in page.getbands() or "transparency" in page.info:
                rgba = page.convert("RGBA")
                page = Image.alpha_composite(Image.new("RGBA", rgba.size, "white"), rgba)
            rgb = page.convert("RGB")
            rgb.info.clear()
            return rgb
    except Image.DecompressionBombError as exc:
        raise ImageInputError(413, "Изображение больше 16 мегапикселей.") from exc
    except (UnidentifiedImageError, OSError, SyntaxError) as exc:
        raise ImageInputError(422, "Не удалось прочитать изображение. Проверьте файл.") from exc


class Detector:
    def __init__(self, bundle: Path, device: str):
        manifest = json.loads((bundle / "manifest.json").read_bytes())
        if (
            manifest["schema_version"] != "sealsign-model-v1"
            or manifest["class_names"] != list(LABELS)
            or manifest["backend"] != "ultralytics YOLO detect"
        ):
            raise ValueError("Несовместимый пакет модели SealSign.")
        filename = manifest["weights"]
        if Path(filename).name != filename or Path(filename).suffix.lower() != ".pt":
            raise ValueError("В manifest ожидается имя локального файла весов .pt.")
        weights = (bundle / filename).resolve(strict=True)
        if weights.parent != bundle.resolve():
            raise ValueError("Файл весов должен находиться в каталоге модели.")
        with weights.open("rb") as stream:
            checksum = hashlib.file_digest(stream, "sha256").hexdigest()
        if checksum != manifest["weights_sha256"]:
            raise ValueError("Контрольная сумма весов не совпадает с manifest.")
        thresholds = manifest["thresholds"]
        if len(thresholds) != len(LABELS) or not all(0 < value <= 1 for value in thresholds):
            raise ValueError("Некорректные пороги классов в manifest.")

        from ultralytics import YOLO, __version__
        from ultralytics.utils import SETTINGS

        if __version__ != manifest["backend_version"]:
            raise ValueError(f"Для этой модели нужен Ultralytics {manifest['backend_version']}.")
        SETTINGS.update({"sync": False})
        self.model = YOLO(str(weights))
        if self.model.task != "detect" or self.model.names != dict(enumerate(LABELS)):
            raise ValueError("Классы или тип модели не совпадают с manifest.")
        self.version = f"YOLO11n {manifest['experiment']} · {checksum[:12]}"
        self.thresholds = thresholds
        self.options = {
            "device": device,
            "imgsz": manifest["preprocessing"]["imgsz"],
            "conf": min(thresholds),
            "iou": manifest["nms_iou"],
            "max_det": manifest["max_det"],
            "agnostic_nms": False,
            "verbose": False,
        }

    def predict(self, page: Image.Image) -> dict:
        result = self.model.predict(page, **self.options)[0]
        if result.orig_shape != (page.height, page.width):
            raise ValueError("Размер исходной страницы не совпадает с результатом модели.")
        detections = []
        for x1, y1, x2, y2, confidence, category in result.boxes.data.cpu().tolist():
            class_id = int(category)
            if category != class_id or not 0 <= class_id < len(LABELS):
                raise ValueError("Модель вернула неизвестный класс.")
            if not all(math.isfinite(value) for value in (x1, y1, x2, y2, confidence)):
                raise ValueError("Модель вернула нечисловые параметры рамки.")
            if confidence < self.thresholds[class_id]:
                continue
            left, top = max(0.0, x1), max(0.0, y1)
            right, bottom = min(page.width, x2), min(page.height, y2)
            if left < right and top < bottom:
                detections.append(
                    {
                        "class_id": class_id,
                        "label": LABELS[class_id],
                        "confidence": confidence,
                        "bbox_xyxy": [left, top, right, bottom],
                    }
                )
        return {
            "schema_version": "1.0",
            "request_id": uuid4().hex,
            "model_version": self.version,
            "image": {"width": page.width, "height": page.height},
            "detections": detections,
            "timing_ms": {
                name: result.speed[name] for name in ("preprocess", "inference", "postprocess")
            },
        }
