"""Train the configured SealSign detector on a frozen dataset or resume a run."""

import argparse
import importlib.metadata as metadata
import json
import os
import platform
import random
import subprocess
import sys
from pathlib import Path
from time import perf_counter

from scripts.finalize_s04 import digest, dump, read


def smoke_data(dataset, path, seed):
    rows = [
        json.loads(line)
        for line in (dataset / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    labels = read(dataset / "annotations.json")["pages"]
    positives = [
        p
        for p in rows
        if p["split"] == "train"
        and {a["category_id"] for a in labels[str(p["queue_index"])]} == {0, 1}
    ]
    if len(positives) < 16:
        raise ValueError("E00 requires 16 train pages with both classes")
    pages = random.Random(seed).sample(positives, 16)
    listing = path / "overfit-pages.txt"
    listing.write_text(
        "".join(
            (dataset / "images/train" / f"{p['page_id']}.png").as_posix() + "\n" for p in pages
        ),
        encoding="utf-8",
    )
    yaml = path / "overfit.yaml"
    yaml.write_text(
        "train: overfit-pages.txt\nval: overfit-pages.txt\nnames: [stamp, signature]\n",
        encoding="utf-8",
    )
    return yaml


def run_training(model, run, device, train_args, resumed_from=None):
    import torch

    start = perf_counter()
    if device != "cpu":
        torch.cuda.reset_peak_memory_stats(device)
    model.train(**train_args)
    dump(
        run / "run-result.json",
        {
            "wall_seconds": perf_counter() - start,
            "resume_checkpoint_sha256": resumed_from,
            "peak_torch_allocated_bytes": torch.cuda.max_memory_allocated(device)
            if device != "cpu"
            else None,
            "weights_sha256": {
                name: digest(run / "weights" / name) for name in ("best.pt", "last.pt")
            },
        },
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment", choices=("E00", "E01", "E02", "E04"))
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--resume", type=Path)
    args = parser.parse_args()
    config = read(args.config)
    params = {**config["common"], **config["experiments"][args.experiment]}
    for name in ("imgsz", "batch", "epochs"):
        if type(params.get(name)) is not int or params[name] <= 0:
            parser.error(f"{name} must be a positive integer")
    for name in ("device", "seed", "optimizer", "lr0"):
        if params.get(name) is None:
            parser.error(f"{name} is required")
    dataset = args.dataset.resolve()
    freeze = read(dataset / "qc-report.json")
    for name, sha256 in freeze["output_sha256"].items():
        if digest(dataset / name) != sha256:
            raise ValueError(f"Changed frozen input {name}")
    runs = args.runs.resolve()
    run = runs / args.experiment
    cache = runs / "settings"
    cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("YOLO_CONFIG_DIR", str(cache))

    import torch
    from ultralytics import YOLO
    from ultralytics.utils import SETTINGS
    from ultralytics.utils.downloads import attempt_download_asset

    SETTINGS.update({"sync": False, "weights_dir": str(runs / "pretrained")})
    if params["device"] != "cpu" and not torch.cuda.is_available():
        raise RuntimeError("PyTorch CUDA is unavailable")
    if args.resume:
        state = read(run / "run-inputs.json")
        if (
            state["config_sha256"] != digest(args.config)
            or state["dataset"] != freeze["output_sha256"]
        ):
            raise ValueError("Resume configuration or data differs from the original run")
        checkpoint = args.resume.resolve(strict=True)
        if checkpoint != run / "weights/last.pt":
            raise ValueError("Resume requires this experiment’s last.pt")
        run_training(
            YOLO(str(checkpoint)), run, params["device"], {"resume": True}, digest(checkpoint)
        )
        return
    run.mkdir(parents=True, exist_ok=False)
    source = runs / "pretrained" / Path(config["initial_weights"]).name
    source.parent.mkdir(exist_ok=True)
    weights = Path(attempt_download_asset(source))
    weight_hash = digest(weights)
    if weight_hash != config["initial_weights_sha256"]:
        raise ValueError("Pretrained weights differ from the configured SHA-256")
    data = (
        smoke_data(dataset, run, params["seed"])
        if args.experiment == "E00"
        else dataset / "dataset.yaml"
    )
    if not data.is_file():
        raise FileNotFoundError(data)
    dump(
        run / "run-inputs.json",
        {
            "command": sys.argv,
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "trainer_sha256": digest(Path(__file__)),
            "config_sha256": digest(args.config),
            "dataset": freeze["output_sha256"],
            "training_yaml_sha256": digest(data),
            "initial_weights_sha256": weight_hash,
            "parameters": params,
            "python": sys.version,
            "platform": platform.platform(),
            "cuda": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(params["device"])
            if params["device"] != "cpu"
            else None,
            "gpu_total_bytes": torch.cuda.get_device_properties(params["device"]).total_memory
            if params["device"] != "cpu"
            else None,
            "packages": dict(
                sorted((p.metadata["Name"], p.version) for p in metadata.distributions())
            ),
        },
    )
    run_training(
        YOLO(str(weights)),
        run,
        params["device"],
        {
            "data": str(data),
            "project": str(runs),
            "name": args.experiment,
            "exist_ok": True,
            **params,
        },
    )


if __name__ == "__main__":
    main()
