from io import BytesIO
from types import SimpleNamespace

import pytest
from PIL import Image

from sealsign.inference import Detector, ImageInputError, decode_page


def test_page_is_normalized_for_preview_and_detection():
    source = Image.new("RGB", (100, 50), "white")
    source.getexif()[274] = 6
    encoded = BytesIO()
    source.save(encoded, format="JPEG", exif=source.getexif())

    page = decode_page(encoded.getvalue())

    assert page.size == (50, 100)
    assert page.mode == "RGB"
    assert not page.getexif()


def test_input_error_codes():
    with pytest.raises(ImageInputError) as corrupt:
        decode_page(b"not an image")
    assert corrupt.value.status == 422
    encoded = BytesIO()
    Image.new("RGB", (20, 10)).save(encoded, format="GIF")
    with pytest.raises(ImageInputError) as unsupported:
        decode_page(encoded.getvalue())
    assert unsupported.value.status == 415


def test_prediction_keeps_overlapping_classes_and_applies_class_thresholds():
    page = Image.new("RGB", (100, 200))
    boxes = [
        [-2, 15, 105, 204, 0.9, 0],
        [2, 15, 99, 190, 0.45, 1],
        [2, 15, 99, 190, 0.45, 0],
        [0, 0, 0, 4, 0.99, 1],
    ]
    tensor = SimpleNamespace(cpu=lambda: SimpleNamespace(tolist=lambda: boxes))
    result = SimpleNamespace(
        boxes=SimpleNamespace(data=tensor),
        orig_shape=(200, 100),
        speed={"preprocess": 1.0, "inference": 2.0, "postprocess": 1.0},
    )
    detector = Detector.__new__(Detector)
    detector.model = SimpleNamespace(predict=lambda *args, **kwargs: [result])
    detector.options = {}
    detector.version = "test model"
    detector.thresholds = [0.46, 0.42]

    prediction = detector.predict(page)

    assert prediction["image"] == {"width": 100, "height": 200}
    assert [box["label"] for box in prediction["detections"]] == ["stamp", "signature"]
    assert prediction["detections"][0]["bbox_xyxy"] == [0, 15, 100, 200]
