"""Select a detector by validation mAP and verify a private CPU-loadable bundle."""

import argparse
import csv
import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.finalize_s04 import digest, dump, read


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--experiments", nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    runs = args.runs.resolve(strict=True)
    os.environ.setdefault("YOLO_CONFIG_DIR", str(runs / "settings"))
    import numpy as np
    from ultralytics import YOLO
    from ultralytics.utils import SETTINGS

    SETTINGS.update({"sync": False})

    candidates = []
    datasets = []
    for experiment in args.experiments:
        if experiment not in {"E01", "E02", "E04"}:
            parser.error(f"{experiment} is not a full validation experiment")
        run = runs / experiment
        weights = run / "weights/best.pt"
        metrics = read(run / "validation/metrics.json")
        if (
            metrics["split"] != "val"
            or metrics["experiment"] != experiment
            or metrics["weights_sha256"] != digest(weights)
        ):
            raise ValueError(f"Validation evidence does not match {experiment}")
        datasets.append(read(run / "run-inputs.json")["dataset"])
        candidates.append((metrics["map50_95"], experiment, metrics, weights))
    if any(dataset != datasets[0] for dataset in datasets):
        raise ValueError("Experiments were trained on different frozen data")
    ordered = sorted(candidates, key=lambda item: (-item[0], item[1]))
    _, winner, metrics, weights = ordered[0]
    winner_run = runs / winner
    training = read(winner_run / "run-inputs.json")
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=output.parent) as temp:
        bundle = Path(temp) / "bundle"
        bundle.mkdir()
        checkpoint = bundle / "model.pt"
        shutil.copyfile(weights, checkpoint)
        shutil.copyfile(winner_run / "args.yaml", bundle / "training-args.yaml")
        shutil.copyfile(winner_run / "run-inputs.json", bundle / "training-environment.json")
        dependency_file = bundle / "requirements-installed.txt"
        dependency_file.write_text(
            "--extra-index-url https://download.pytorch.org/whl/cu128\n"
            + "".join(f"{name}=={version}\n" for name, version in training["packages"].items()),
            encoding="utf-8",
        )
        names = ["stamp", "signature"]
        model = YOLO(str(checkpoint))
        if model.names != dict(enumerate(names)):
            raise ValueError("Unexpected class mapping in packaged checkpoint")
        result = model.predict(
            np.full((256, 192, 3), 255, dtype=np.uint8),
            imgsz=metrics["settings"]["imgsz"],
            device="cpu",
            verbose=False,
        )
        if len(result) != 1 or result[0].orig_shape != (256, 192):
            raise ValueError("CPU inference returned invalid geometry")
        dump(
            bundle / "manifest.json",
            {
                "schema_version": "sealsign-model-v1",
                "experiment": winner,
                "backend": "ultralytics YOLO detect",
                "backend_version": training["packages"]["ultralytics"],
                "weights": "model.pt",
                "weights_sha256": digest(checkpoint),
                "class_names": names,
                "thresholds": [metrics["classes"][name]["threshold"] for name in names],
                "preprocessing": {
                    "imgsz": metrics["settings"]["imgsz"],
                    "orientation": "EXIF-normalized",
                    "resize": "YOLO letterbox",
                },
                "nms_iou": metrics["settings"]["iou"],
                "max_det": metrics["settings"]["max_det"],
                "dataset_checksums": datasets[0],
                "training_git_head": training["git_head"],
                "training_code_sha256": training["trainer_sha256"],
                "training_files_sha256": {
                    name: digest(bundle / name)
                    for name in (
                        "training-args.yaml",
                        "training-environment.json",
                        "requirements-installed.txt",
                    )
                },
                "validation": metrics,
                "cpu_smoke_passed": True,
            },
        )
        evaluations = []
        for score, experiment, validation, _ in ordered:
            source = read(runs / experiment / "run-inputs.json")
            result = read(runs / experiment / "run-result.json")
            evaluations.append(
                {
                    "experiment": experiment,
                    "git_head": source["git_head"],
                    "trainer_sha256": source["trainer_sha256"],
                    "manifest_sha256": source["dataset"]["manifest.jsonl"],
                    "annotations_sha256": source["dataset"]["annotations.json"],
                    "split_sha256": source["dataset"]["split.json"],
                    "config_sha256": source["config_sha256"],
                    "seed": source["parameters"]["seed"],
                    "model": "yolo11n",
                    "initial_weights_sha256": source["initial_weights_sha256"],
                    "weights_sha256": validation["weights_sha256"],
                    "gpu": source["gpu"],
                    "map50_val": validation["map50"],
                    "map50_95_val": score,
                    "wall_seconds": result["wall_seconds"],
                    "run_directory": experiment,
                }
            )
        with (bundle / "experiments.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(evaluations[0]))
            writer.writeheader()
            writer.writerows(evaluations)
        (bundle / "model-card.md").write_text(
            f"# SealSign YOLO11n — {winner}\n\n"
            "Детекция печатей и подписей на страницах документов.\n\n"
            f"Выбор по val mAP50–95. Получено {metrics['map50_95']:.4f} на "
            f"{metrics['pages']} страницах val. Пороги подобраны на val по F1 каждого "
            "класса при IoU 0,50.\n\n"
            "Корпус ограничен источниками Mapo80 и принятыми после QC страницами. "
            "Часть сходных документов может остаться необнаруженной. "
            "Проверка на CPU выполнена на синтетическом изображении. "
            "Права на публикацию исходных страниц не подтверждены.\n",
            encoding="utf-8",
        )
        bundle.rename(output)
    print(winner)


if __name__ == "__main__":
    main()
