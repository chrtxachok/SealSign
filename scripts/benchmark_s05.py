"""Measure single-page inference on a seeded sample of the validation split."""

import argparse
import os
import random
import statistics
from pathlib import Path
from time import perf_counter

from scripts.finalize_s04 import digest, dump, read


def percentile(values):
    return {
        "median": statistics.median(values),
        "p95": statistics.quantiles(values, n=100, method="inclusive")[94],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--device", choices=("0", "cpu"), default="0")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    settings = read(args.bundle / "manifest.json")
    weights = args.bundle / settings["weights"]
    if digest(weights) != settings["weights_sha256"]:
        raise ValueError("Invalid model bundle weights")
    pages = sorted((args.dataset / "images/val").glob("*.png"))
    if len(pages) < 105:
        raise ValueError("Benchmark needs 100 validation pages and five for warmup")
    sample = random.Random(42).sample(pages, 105)
    os.environ.setdefault("YOLO_CONFIG_DIR", str(args.output.resolve().parent / "settings"))

    import torch
    from ultralytics import YOLO
    from ultralytics.utils import SETTINGS

    SETTINGS.update({"sync": False})
    model = YOLO(str(weights))
    cuda = args.device != "cpu"
    options = {
        "device": args.device,
        "batch": 1,
        "imgsz": settings["preprocessing"]["imgsz"],
        "conf": min(settings["thresholds"]),
        "iou": settings["nms_iou"],
        "max_det": settings["max_det"],
        "verbose": False,
    }
    elapsed = []
    retained = 0
    stages = {name: [] for name in ("preprocess", "inference", "postprocess")}
    for i, page in enumerate(sample):
        if cuda:
            torch.cuda.synchronize()
        start = perf_counter()
        result = model.predict(str(page.resolve()), **options)[0]
        detections = sum(
            score >= settings["thresholds"][int(cls)]
            for cls, score in zip(
                result.boxes.cls.tolist(), result.boxes.conf.tolist(), strict=True
            )
        )
        if cuda:
            torch.cuda.synchronize()
        wall_ms = (perf_counter() - start) * 1000
        if i >= 5:
            elapsed.append(wall_ms)
            retained += detections
            for name in stages:
                stages[name].append(result.speed[name])
    dump(
        args.output,
        {
            "experiment": settings["experiment"],
            "weights_sha256": digest(weights),
            "images": len(elapsed),
            "warmup": 5,
            "batch": 1,
            "seed": 42,
            "device": torch.cuda.get_device_name() if cuda else "cpu",
            "includes_file_io": True,
            "retained_detections": retained,
            "milliseconds": {
                "end_to_end": percentile(elapsed),
                **{name: percentile(values) for name, values in stages.items()},
            },
        },
    )


if __name__ == "__main__":
    main()
