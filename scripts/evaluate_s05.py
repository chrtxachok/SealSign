"""Measure AP and operating-point metrics. Fit operating thresholds on val only."""

import argparse
import os
from pathlib import Path

from scripts.finalize_s04 import digest, dump, read


def match_predictions(result, labels, match_iou):
    import numpy as np
    import torch
    from ultralytics.utils.metrics import box_iou

    height, width = result.orig_shape
    truth = np.loadtxt(labels, ndmin=2, dtype=float) if labels.stat().st_size else np.empty((0, 5))
    centers = truth[:, 1:3] * [width, height]
    half_sizes = truth[:, 3:5] * [width / 2, height / 2]
    coords = np.concatenate((centers - half_sizes, centers + half_sizes), axis=1)
    boxes = result.boxes.cpu()
    overlap = box_iou(boxes.xyxy, torch.as_tensor(coords, dtype=torch.float32)).numpy()
    classes = boxes.cls.numpy().astype(int)
    scores = boxes.conf.numpy()
    matched = set()
    hits = []
    for prediction in np.argsort(-scores, kind="stable"):
        category = classes[prediction]
        eligible = [
            i for i, label in enumerate(truth[:, 0]) if label == category and i not in matched
        ]
        best = max(eligible, key=lambda i: overlap[prediction, i], default=None)
        hit = best is not None and overlap[prediction, best] >= match_iou
        if hit:
            matched.add(best)
        hits.append((int(category), float(scores[prediction]), bool(hit)))
    return hits, np.bincount(truth[:, 0].astype(int), minlength=2).tolist()


def metrics(scores, support, threshold):
    tp = sum(hit for score, hit in scores if score >= threshold)
    predicted = sum(score >= threshold for score, _ in scores)
    fp, fn = predicted - tp, support - tp
    return {
        "threshold": threshold,
        "support": support,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": tp / predicted if predicted else 0.0,
        "recall": tp / support if support else 0.0,
        "f1": 2 * tp / (support + predicted) if support + predicted else 0.0,
    }


def select_threshold(scores, support):
    if not support:
        raise ValueError("Validation has no ground truth for a class")
    scores = sorted(scores, reverse=True)
    best = (-1.0, 0.99)
    tp = 0
    for i, (score, hit) in enumerate(scores, start=1):
        tp += hit
        if i == len(scores) or score > scores[i][0]:
            best = max(best, (2 * tp / (i + support), score))
    return best[1]


def summarize_pages(page_results, by_class):
    errors = []
    for page_id, hits, counts in page_results:
        classes = {}
        for category, (name, row) in enumerate(by_class.items()):
            detections = [(score, hit) for cls, score, hit in hits if cls == category]
            operating = metrics(detections, counts[category], row["threshold"])
            classes[name] = {k: operating[k] for k in ("tp", "fp", "fn")}
        errors.append({"page_id": page_id, "classes": classes})
    for name, row in by_class.items():
        positives = [
            p["classes"][name]
            for p in errors
            if p["classes"][name]["tp"] or p["classes"][name]["fn"]
        ]
        row["positive_pages"] = len(positives)
        row["page_presence_recall"] = (
            sum(bool(p["tp"] or p["fp"]) for p in positives) / len(positives) if positives else None
        )
        row["pages_with_false_positives"] = sum(p["classes"][name]["fp"] > 0 for p in errors)
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True, help="Path to dataset.yaml")
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--split", choices=("val", "test"), required=True)
    parser.add_argument("--thresholds-from", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if (args.split == "test") != (args.thresholds_from is not None):
        parser.error("Testing requires frozen thresholds selected on val")
    config = read(args.config)
    params = {**config["common"], **config["experiments"][args.experiment]}
    policy = config["evaluation"]
    data = args.data.resolve(strict=True)
    weights = args.weights.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    os.environ.setdefault("YOLO_CONFIG_DIR", str(output.parent / "settings"))

    from ultralytics import YOLO
    from ultralytics.data.utils import check_det_dataset
    from ultralytics.utils import SETTINGS

    SETTINGS.update({"sync": False})
    model = YOLO(str(weights))
    names = ["stamp", "signature"]
    if model.names != dict(enumerate(names)):
        raise ValueError("Model class mapping differs from SealSign")
    det = check_det_dataset(str(data), autodownload=False)
    if det["names"] != model.names:
        raise ValueError("Dataset class mapping differs from the model")
    settings = {k: params[k] for k in ("imgsz", "device", "batch")}
    settings.update(conf=policy["ap_conf"], iou=policy["iou"], max_det=policy["max_det"])
    weight_hash = digest(weights)
    fixed = read(args.thresholds_from) if args.thresholds_from else None
    if fixed and (
        fixed["split"] != "val"
        or fixed["weights_sha256"] != weight_hash
        or fixed["settings"] != settings
        or fixed["match_iou"] != policy["match_iou"]
    ):
        raise ValueError("Frozen thresholds do not match the model and evaluation policy")
    ap = model.val(
        data=str(data),
        split=args.split,
        workers=0,
        project=str(output),
        name="ap",
        plots=False,
        **settings,
    )
    path = Path(det[args.split])
    scores = [[], []]
    support = [0, 0]
    page_results = []
    for result in model.predict(source=str(path), stream=True, verbose=False, **settings):
        image = Path(result.path)
        label = image.parents[2] / "labels" / image.parent.name / image.with_suffix(".txt").name
        hits, counts = match_predictions(result, label, policy["match_iou"])
        for category, score, hit in hits:
            scores[category].append((score, hit))
        support = [a + b for a, b in zip(support, counts, strict=True)]
        page_results.append((image.stem, hits, counts))
    pages = len(page_results)
    if not pages:
        raise ValueError("No pages were processed")
    by_class = {}
    for i, name in enumerate(names):
        threshold = (
            fixed["classes"][name]["threshold"]
            if fixed
            else select_threshold(scores[i], support[i])
        )
        by_class[name] = metrics(scores[i], support[i], threshold)
        by_class[name]["fp_per_page"] = by_class[name]["fp"] / pages
    for class_id, ap_row in zip(
        ap.box.ap_class_index.tolist(), ap.box.all_ap.tolist(), strict=True
    ):
        row = by_class[names[class_id]]
        row["ap50"] = ap_row[0]
        row["ap50_95"] = sum(ap_row) / len(ap_row)
    dump(output / "page-errors.json", summarize_pages(page_results, by_class))
    dump(
        output / "metrics.json",
        {
            "experiment": args.experiment,
            "split": args.split,
            "pages": pages,
            "weights_sha256": weight_hash,
            "settings": settings,
            "match_iou": policy["match_iou"],
            "dataset_yaml_sha256": digest(data),
            "thresholds_source": "validation maximum F1",
            "map50": float(ap.box.map50),
            "map50_95": float(ap.box.map),
            "classes": by_class,
            "speed_ms_per_page": ap.speed,
        },
    )


if __name__ == "__main__":
    main()
