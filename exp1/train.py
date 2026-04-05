#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""exp1 unified training entry.

Features:
1) --model baseline|mbv3|eca|mbv3_sp4eca auto-selects model yaml
2) Uses fixed hyperparameters for fair ablation training
3) Supports resilient resume from last.pt
4) Auto-evaluates best.pt on test split after training
5) Saves training/eval artifacts under exp1 for thesis usage
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
from ultralytics import YOLO

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from exp1.models.ca import CA
    from exp1.models.eca import ECA
except Exception:
    CA = None  # type: ignore
    ECA = None  # type: ignore

EXP1_ROOT = REPO_ROOT / "exp1"
RUNS_ROOT = EXP1_ROOT / "runs"
EVAL_ROOT = EXP1_ROOT / "eval"
META_ROOT = EXP1_ROOT / "meta"
LOG_ROOT = EXP1_ROOT / "logs"

# Fixed training contract from exp1 plan for fairness/reproducibility.
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="exp1 unified trainer")
    parser.add_argument("--model", choices=["baseline", "mbv3", "eca", "mbv3_sp4eca", "mbv3_ca"], required=True)
    parser.add_argument(
        "--data",
        type=str,
        default=str(EXP1_ROOT / "dataset" / "data.yaml"),
        help="Dataset yaml. Default is exp1/dataset/data.yaml",
    )
    parser.add_argument(
        "--project",
        type=str,
        default=str(RUNS_ROOT),
        help="Training output root. Default: exp1/runs",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        default=True,
        help="Resume from last.pt if exists (default true)",
    )
    parser.add_argument("--no-resume", action="store_false", dest="resume")
    parser.add_argument(
        "--force-fresh",
        action="store_true",
        help="Ignore last.pt and start a fresh run in same exp1/runs/{model} directory",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=FIXED_TRAIN_ARGS["workers"],
        help="Override workers if needed for stability (default 1)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=FIXED_TRAIN_ARGS["device"],
        help="Override device if needed (default 0)",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=FIXED_TRAIN_ARGS["batch"],
        help="Override batch if emergency only. Keep 6 for fairness.",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=FIXED_TRAIN_ARGS["epochs"],
        help="Override epochs if emergency only. Keep 200 for fairness.",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=FIXED_TRAIN_ARGS["imgsz"],
        help="Override imgsz if emergency only. Keep 640 for fairness.",
    )
    parser.add_argument(
        "--fps-iters",
        type=int,
        default=100,
        help="Iterations for FPS benchmark",
    )
    parser.add_argument(
        "--fps-warmup",
        type=int,
        default=10,
        help="Warmup iterations for FPS benchmark",
    )
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
    for d in [EXP1_ROOT, RUNS_ROOT, EVAL_ROOT, META_ROOT, LOG_ROOT]:
        d.mkdir(parents=True, exist_ok=True)


def resolve_model_source(model_name: str) -> str:
    exp1_cfg = EXP1_ROOT / "configs"
    train_cfg = REPO_ROOT / "training" / "configs"

    # Priority: exp1 configs -> historical full-run configs -> official baseline yaml name.
    if model_name == "baseline":
        exp1_baseline = exp1_cfg / "yolov11s.yaml"
        if exp1_baseline.exists():
            return str(exp1_baseline)
        exp1_baseline_alt = exp1_cfg / "yolo11s.yaml"
        if exp1_baseline_alt.exists():
            return str(exp1_baseline_alt)
        return "yolo11s.yaml"

    if model_name == "mbv3":
        cands = [
            exp1_cfg / "yolov11s_mbv3.yaml",
            train_cfg / "yolo11s_mbv3.yaml",
        ]
    elif model_name == "mbv3_ca":
        cands = [
            exp1_cfg / "yolov11s_mbv3_ca.yaml",
        ]
    elif model_name == "mbv3_sp4eca":
        cands = [
            exp1_cfg / "yolov11s_mbv3_sp4eca.yaml",
        ]
    else:
        cands = [
            exp1_cfg / "yolov11s_mbv3_eca.yaml",
            train_cfg / "yolo11s_mbv3_eca2.yaml",  # preferred according to full-run fairness memory
            train_cfg / "yolo11s_mbv3_eca.yaml",
        ]

    for c in cands:
        if c.exists():
            return str(c)

    raise FileNotFoundError(f"No config found for model={model_name}. Checked: {cands}")


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
    # Try ultralytics helper first, then thop as fallback.
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


def build_train_kwargs(args: argparse.Namespace, run_project: Path) -> dict[str, Any]:
    train_kwargs = dict(FIXED_TRAIN_ARGS)
    if args.model == "mbv3_sp4eca":
        # Single-variable control for this experiment variant.
        train_kwargs["close_mosaic"] = 15
        train_kwargs["cls_pw"] = 1.2
    if args.model == "mbv3_ca":
        # Required training deltas for MBV3+CA run: only close_mosaic and cls_pw.
        train_kwargs["close_mosaic"] = 20
        train_kwargs["cls_pw"] = 1.2

    train_kwargs["epochs"] = args.epochs
    train_kwargs["batch"] = args.batch
    train_kwargs["imgsz"] = args.imgsz
    train_kwargs["workers"] = args.workers
    train_kwargs["device"] = args.device
    lr_override = os.getenv("EXP1_LR0_OVERRIDE", "").strip()
    if lr_override:
        try:
            train_kwargs["lr0"] = float(lr_override)
        except Exception:
            pass

    train_kwargs.update(
        {
            "data": args.data,
            "project": str(run_project),
            "name": args.model,
            "exist_ok": True,
            "save": True,
            "save_period": 5,
            "verbose": True,
        }
    )
    return train_kwargs


def main() -> int:
    args = parse_args()
    ensure_dirs()
    set_reproducibility(42)

    start_ts = time.time()
    run_project = Path(args.project)
    run_dir = run_project / args.model
    weights_dir = run_dir / "weights"
    last_pt = weights_dir / "last.pt"
    best_pt = weights_dir / "best.pt"

    if not Path(args.data).exists():
        print(f"[ERROR] data yaml not found: {args.data}")
        return 1

    model_source = resolve_model_source(args.model)

    if args.model in {"mbv3_sp4eca", "mbv3_ca"}:
        # Keep Ultralytics runtime intact while permitting cls_pw in overrides.
        try:
            import ultralytics.cfg as ucfg

            _orig_check_dict_alignment = ucfg.check_dict_alignment

            def _check_dict_alignment_allow_cls_pw(base: dict, custom: dict, e: Exception | None = None) -> None:
                if isinstance(custom, dict) and "cls_pw" in custom:
                    custom = dict(custom)
                    custom.pop("cls_pw", None)
                _orig_check_dict_alignment(base, custom, e)

            ucfg.check_dict_alignment = _check_dict_alignment_allow_cls_pw
        except Exception:
            pass

    if ECA is not None:
        # Register custom module symbol for Ultralytics YAML parser.
        try:
            import ultralytics.nn.tasks as tasks

            setattr(tasks, "ECA", ECA)
        except Exception:
            pass

    if CA is not None:
        # Register custom module symbol for Ultralytics YAML parser.
        try:
            import ultralytics.nn.tasks as tasks

            setattr(tasks, "CA", CA)
        except Exception:
            pass

    # Resume strategy: if last.pt exists and not force-fresh, use full-state resume.
    use_resume = bool(args.resume and last_pt.exists() and not args.force_fresh)
    yolo_source = str(last_pt) if use_resume else model_source

    train_kwargs = build_train_kwargs(args, run_project)
    if use_resume:
        train_kwargs["resume"] = True

    run_meta = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model": args.model,
        "model_source": model_source,
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
        "paths": {
            "run_dir": str(run_dir),
            "results_csv": str(run_dir / "results.csv"),
            "best_pt": str(best_pt),
            "eval_json": str(EVAL_ROOT / f"{args.model}_test_results.json"),
        },
    }
    dump_json(META_ROOT / f"{args.model}_run_manifest.json", run_meta)

    print(f"[INFO] model={args.model}")
    print(f"[INFO] model_source={model_source}")
    print(f"[INFO] use_resume={use_resume}")
    print(f"[INFO] run_dir={run_dir}")

    trainer = YOLO(yolo_source)
    trainer.train(**train_kwargs)

    if not best_pt.exists():
        print(f"[ERROR] training finished but best.pt not found: {best_pt}")
        return 2

    # Unified test evaluation from best.pt after training.
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
        "model": args.model,
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
        },
    }

    eval_out = EVAL_ROOT / f"{args.model}_test_results.json"
    dump_json(eval_out, eval_payload)

    env_snapshot = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "python": sys.version,
        "torch": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }
    dump_json(META_ROOT / "environment_snapshot.json", env_snapshot)

    print("[DONE] training + test evaluation finished")
    print(f"[DONE] results_csv={run_dir / 'results.csv'}")
    print(f"[DONE] eval_json={eval_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
