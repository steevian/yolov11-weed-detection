#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""exp2 unified training entry.

Key policy:
- baseline and mbv3 are reused from exp1 official runs (no retrain in exp2)
- exp2 only trains compressed ablation set
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
CUSTOM_UL_ROOT = REPO_ROOT / "training" / "ultralytics_custom"
if str(CUSTOM_UL_ROOT) not in sys.path:
    sys.path.insert(0, str(CUSTOM_UL_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ultralytics import YOLO
from exp2.models.simam import SimAM

EXP2_ROOT = REPO_ROOT / "exp2"
RUNS_ROOT = EXP2_ROOT / "runs"
EVAL_ROOT = EXP2_ROOT / "eval"
META_ROOT = EXP2_ROOT / "meta"
LOG_ROOT = EXP2_ROOT / "logs"

FIXED_TRAIN_ARGS: dict[str, Any] = {
    "epochs": 200,
    "batch": 6,
    "imgsz": 640,
    "optimizer": "SGD",
    "lr0": 0.01,
    "lrf": 0.01,
    "momentum": 0.937,
    "weight_decay": 0.0005,
    "warmup_epochs": 3.0,
    "warmup_momentum": 0.8,
    "warmup_bias_lr": 0.1,
    "patience": 50,
    "device": "0",
    "workers": 1,
    "seed": 42,
    "deterministic": True,
    "amp": True,
    "close_mosaic": 10,
    "hsv_h": 0.015,
    "hsv_s": 0.7,
    "hsv_v": 0.4,
    "degrees": 8.0,
    "translate": 0.1,
    "scale": 0.2,
    "shear": 0.0,
    "perspective": 0.0,
    "flipud": 0.1,
    "fliplr": 0.5,
    "mosaic": 1.0,
    "mixup": 0.0,
    "copy_paste": 0.0,
    "auto_augment": "randaugment",
    "erasing": 0.4,
}

FIXED_EVAL_ARGS: dict[str, Any] = {
    "iou": 0.7,
    "max_det": 300,
}

MODEL_TO_CONFIG = {
    "p2_simam": EXP2_ROOT / "configs" / "yolov11s_mbv3_p2_simam.yaml",
    "p2_simam_dwconv": EXP2_ROOT / "configs" / "yolov11s_mbv3_p2_simam_dwconv.yaml",
    "p2_simam_shuffle": EXP2_ROOT / "configs" / "yolov11s_mbv3_p2_simam_shuffle.yaml",
    "p2_simam_dwconv_p075ghost": EXP2_ROOT / "configs" / "yolov11s_mbv3_p2_simam_dwconv_p075ghost.yaml",
}

# 中文注释：支持用户使用更直观的完整命名，内部会映射到规范短名，避免重复目录与结果文件。
MODEL_ALIASES = {
    "mbv3_p2_simam": "p2_simam",
    "mbv3_p2_simam_dwconv": "p2_simam_dwconv",
    "mbv3_p2_simam_shuffle": "p2_simam_shuffle",
    "mbv3_p2_simam_dwconv_p075ghost": "p2_simam_dwconv_p075ghost",
}

MODEL_CHOICES = list(dict.fromkeys(list(MODEL_TO_CONFIG.keys()) + list(MODEL_ALIASES.keys()) + ["baseline", "mbv3"]))
FAIR_DATA_YAML = REPO_ROOT / "exp1" / "dataset" / "data.yaml"
FAIRNESS_LOCKED_ARGS: dict[str, Any] = {
    "epochs": FIXED_TRAIN_ARGS["epochs"],
    "batch": FIXED_TRAIN_ARGS["batch"],
    "imgsz": FIXED_TRAIN_ARGS["imgsz"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="exp2 compressed ablation trainer")
    parser.add_argument("--model", choices=MODEL_CHOICES, required=True)
    parser.add_argument(
        "--data",
        type=str,
        default=str(REPO_ROOT / "exp1" / "dataset" / "data.yaml"),
        help="Reuse exp1 data yaml for strict fairness",
    )
    parser.add_argument("--project", type=str, default=str(RUNS_ROOT))
    parser.add_argument("--resume", action="store_true", default=True)
    parser.add_argument("--no-resume", action="store_false", dest="resume")
    parser.add_argument("--force-fresh", action="store_true")
    parser.add_argument("--workers", type=int, default=FIXED_TRAIN_ARGS["workers"])
    parser.add_argument("--device", type=str, default=FIXED_TRAIN_ARGS["device"])
    parser.add_argument("--batch", type=int, default=FIXED_TRAIN_ARGS["batch"])
    parser.add_argument("--epochs", type=int, default=FIXED_TRAIN_ARGS["epochs"])
    parser.add_argument("--imgsz", type=int, default=FIXED_TRAIN_ARGS["imgsz"])
    parser.add_argument(
        "--strict-fairness",
        action="store_true",
        default=True,
        help="Fail fast when fairness-critical args differ from exp1 contract (default true)",
    )
    parser.add_argument("--no-strict-fairness", action="store_false", dest="strict_fairness")
    parser.add_argument("--fps-iters", type=int, default=100)
    parser.add_argument("--fps-warmup", type=int, default=10)
    return parser.parse_args()


def set_reproducibility(seed: int = 42) -> None:
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def ensure_dirs() -> None:
    for d in [EXP2_ROOT, RUNS_ROOT, EVAL_ROOT, META_ROOT, LOG_ROOT]:
        d.mkdir(parents=True, exist_ok=True)


def safe_float(value: Any) -> float | None:
    try:
        x = float(value)
        if math.isnan(x) or math.isinf(x):
            return None
        return x
    except Exception:
        return None


def extract_metric(metric_obj: Any, key: str) -> float | None:
    box = getattr(metric_obj, "box", None)
    if box is None:
        return None
    value = getattr(box, key, None)
    if value is None:
        return None
    if isinstance(value, (list, tuple, np.ndarray)):
        if len(value) == 0:
            return None
        return safe_float(np.mean(value))
    return safe_float(value)


def count_params_m(model: YOLO) -> float:
    n = sum(p.numel() for p in model.model.parameters())
    return float(n) / 1e6


def estimate_flops_g(model: YOLO, imgsz: int) -> float | None:
    try:
        from ultralytics.utils.torch_utils import get_flops

        flops = get_flops(model.model, imgsz)
        if flops is not None:
            return safe_float(flops / 1e9)
    except Exception:
        pass

    try:
        from thop import profile

        net = model.model
        device = next(net.parameters()).device
        x = torch.randn(1, 3, imgsz, imgsz, device=device)
        flops, _ = profile(net, inputs=(x,), verbose=False)
        return safe_float(flops / 1e9)
    except Exception:
        return None


def benchmark_fps(model: YOLO, imgsz: int, warmup: int, iters: int) -> float | None:
    try:
        net = model.model
        if torch.cuda.is_available():
            net = net.cuda()
            x = torch.randn(1, 3, imgsz, imgsz, device="cuda")
        else:
            x = torch.randn(1, 3, imgsz, imgsz)

        net.eval()
        with torch.no_grad():
            for _ in range(max(0, warmup)):
                _ = net(x)
            if torch.cuda.is_available():
                torch.cuda.synchronize()

            t0 = time.perf_counter()
            for _ in range(max(1, iters)):
                _ = net(x)
            if torch.cuda.is_available():
                torch.cuda.synchronize()
            t1 = time.perf_counter()

        dt = t1 - t0
        if dt <= 0:
            return None
        return float(max(1, iters) / dt)
    except Exception:
        return None


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def normalize_model_name(raw_model: str) -> str:
    return MODEL_ALIASES.get(raw_model, raw_model)


def validate_runtime_args(args: argparse.Namespace) -> list[str]:
    errors: list[str] = []

    if args.epochs <= 0:
        errors.append("epochs must be > 0")
    if args.batch <= 0:
        errors.append("batch must be > 0")
    if args.imgsz <= 0:
        errors.append("imgsz must be > 0")
    if args.workers < 0:
        errors.append("workers must be >= 0")

    if args.strict_fairness:
        data_path = Path(args.data).resolve()
        fair_data_path = FAIR_DATA_YAML.resolve()
        if data_path != fair_data_path:
            errors.append(f"strict fairness requires --data={fair_data_path}, got {data_path}")

        for key, expected in FAIRNESS_LOCKED_ARGS.items():
            got = getattr(args, key)
            if got != expected:
                errors.append(f"strict fairness requires --{key}={expected}, got {got}")

    return errors


def build_train_kwargs(args: argparse.Namespace, run_project: Path, model_name: str) -> dict[str, Any]:
    train_kwargs = dict(FIXED_TRAIN_ARGS)
    train_kwargs["epochs"] = args.epochs
    train_kwargs["batch"] = args.batch
    train_kwargs["imgsz"] = args.imgsz
    train_kwargs["workers"] = args.workers
    train_kwargs["device"] = args.device

    train_kwargs.update(
        {
            "data": args.data,
            "project": str(run_project),
            "name": model_name,
            "exist_ok": True,
            "save": True,
            "save_period": 5,
            "verbose": True,
        }
    )
    return train_kwargs


def main() -> int:
    args = parse_args()
    model_name = normalize_model_name(args.model)

    # 中文注释：baseline 和 mbv3 已在 exp1 正式完成，exp2 不允许重复训练。
    if model_name in {"baseline", "mbv3"}:
        print("[STOP] baseline/mbv3 are official exp1 references and must not be retrained in exp2.")
        print("[INFO] Use exp1/eval/*.json as references in exp2/report.py.")
        return 3

    validation_errors = validate_runtime_args(args)
    if validation_errors:
        print("[ERROR] argument validation failed:")
        for msg in validation_errors:
            print(f"  - {msg}")
        return 1

    ensure_dirs()
    set_reproducibility(42)

    if not Path(args.data).exists():
        print(f"[ERROR] data yaml not found: {args.data}")
        return 1

    model_source = MODEL_TO_CONFIG[model_name]
    if not model_source.exists():
        print(f"[ERROR] missing model yaml: {model_source}")
        return 1

    # Register SimAM into Ultralytics YAML parser globals.
    try:
        import ultralytics.nn.tasks as tasks

        setattr(tasks, "SimAM", SimAM)
    except Exception as e:
        print(f"[ERROR] failed to register SimAM: {e}")
        return 1

    start_ts = time.time()
    run_project = Path(args.project)
    run_dir = run_project / model_name
    weights_dir = run_dir / "weights"
    last_pt = weights_dir / "last.pt"
    best_pt = weights_dir / "best.pt"

    use_resume = bool(args.resume and last_pt.exists() and not args.force_fresh)
    yolo_source = str(last_pt) if use_resume else str(model_source)

    train_kwargs = build_train_kwargs(args, run_project, model_name)
    if use_resume:
        train_kwargs["resume"] = True

    run_meta = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "requested_model": args.model,
        "model": model_name,
        "model_source": str(model_source.resolve()),
        "train_entry_source": yolo_source,
        "use_resume": use_resume,
        "resume_checkpoint": str(last_pt) if use_resume else None,
        "data": str(Path(args.data).resolve()),
        "fixed_seed": 42,
        "reproducibility": {
            "deterministic": True,
            "cudnn_benchmark": False,
            "python_hash_seed": 42,
        },
        "train_args": train_kwargs,
        "eval_args": FIXED_EVAL_ARGS,
    }
    dump_json(META_ROOT / f"{model_name}_run_manifest.json", run_meta)

    trainer = YOLO(yolo_source)
    trainer.train(**train_kwargs)

    if not best_pt.exists():
        print(f"[ERROR] training finished but best.pt not found: {best_pt}")
        return 2

    evaluator = YOLO(str(best_pt))
    val_res = evaluator.val(
        data=args.data,
        split="test",
        imgsz=args.imgsz,
        batch=1,
        workers=0,
        iou=FIXED_EVAL_ARGS["iou"],
        max_det=FIXED_EVAL_ARGS["max_det"],
        verbose=False,
    )

    speed = getattr(val_res, "speed", {}) or {}
    infer_ms = safe_float(speed.get("inference")) if isinstance(speed, dict) else None
    fps_from_val = (1000.0 / infer_ms) if infer_ms and infer_ms > 0 else None
    fps_bench = benchmark_fps(evaluator, args.imgsz, args.fps_warmup, args.fps_iters)

    eval_payload = {
        "model": model_name,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "weights": str(best_pt.resolve()),
        "data": str(Path(args.data).resolve()),
        "metrics": {
            "precision": extract_metric(val_res, "mp"),
            "recall": extract_metric(val_res, "mr"),
            "mAP50": extract_metric(val_res, "map50"),
            "mAP50-95": extract_metric(val_res, "map"),
            "Params(M)": count_params_m(evaluator),
            "FLOPs(G)": estimate_flops_g(evaluator, args.imgsz),
            "FPS": fps_bench if fps_bench is not None else fps_from_val,
        },
        "aux": {
            "fps_from_val_speed": fps_from_val,
            "fps_benchmark": fps_bench,
            "val_speed_ms": speed,
            "runtime_seconds_total": safe_float(time.time() - start_ts),
            "results_csv": str((run_dir / "results.csv").resolve()),
        },
        "fairness_contract": {
            "train_fixed_args": FIXED_TRAIN_ARGS,
            "eval_fixed_args": FIXED_EVAL_ARGS,
            "seed": 42,
            "deterministic": True,
            "dataset_policy": "reuse exp1 dataset and references",
        },
    }

    eval_out = EVAL_ROOT / f"{model_name}_test_results.json"
    dump_json(eval_out, eval_payload)

    env_snapshot = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "python": sys.version,
        "torch": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }
    dump_json(META_ROOT / "environment_snapshot.json", env_snapshot)

    print("[DONE] exp2 training + test evaluation finished")
    print(f"[DONE] eval_json={eval_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
