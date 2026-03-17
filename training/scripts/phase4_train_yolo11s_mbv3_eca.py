"""Phase 4 training: YOLO11-S + MobileNetV3 + ECA.

Requires custom ultralytics package copy with ECA module registration.
Use phase0_prepare_ultralytics_custom.py then patch registration manually.

功能简介（中文）：
1) 在 MBV3 结构上叠加 ECA 注意力模块进行训练；
2) 保持与 Phase2/Phase3 一致的核心参数口径，便于公平对比；
3) 自动保存关键实验产物与汇总信息。
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from training.lib.experiment_logger import (  # noqa: E402
    build_environment_snapshot,
    create_run_context,
    finalize_run_metadata,
    normalize_results_csv,
    save_json,
)
from training.lib.plotter import collect_confusion_matrix, plot_metrics_curve  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase4 trainer: YOLO11-S + MBV3 + ECA")
    parser.add_argument(
        "--data",
        type=Path,
        default=REPO_ROOT / "training" / "configs" / "data_3seasonweeddet10.yaml",
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=REPO_ROOT / "training" / "configs" / "yolo11s_mbv3_eca.yaml",
    )
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--batch", type=int, default=6)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument(
        "--cache",
        type=str,
        default="disk",
        help="Ultralytics cache mode: False/none, ram, or disk",
    )
    parser.add_argument("--lr0", type=float, default=0.01)
    parser.add_argument("--optimizer", type=str, default="SGD")
    parser.add_argument("--patience", type=int, default=50)
    parser.add_argument("--save-period", type=int, default=5)
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--device", type=str, default="0")
    parser.add_argument("--amp", action="store_true", default=True)
    parser.add_argument("--no-amp", action="store_false", dest="amp")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--project",
        type=Path,
        default=REPO_ROOT / "experiments" / "YOLOv11-S-MBV3-ECA",
    )
    parser.add_argument("--run-prefix", type=str, default="mbv3_eca")
    parser.add_argument(
        "--ultralytics-root",
        type=Path,
        default=REPO_ROOT / "training" / "ultralytics_custom",
        help="Directory that contains custom ultralytics package root",
    )
    return parser.parse_args()


def set_reproducibility(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def main() -> int:
    args = parse_args()
    if not args.data.exists() or not args.model.exists():
        print("[ERROR] Missing data/model yaml.")
        return 1

    # Keep cache parsing behavior consistent with phase2/phase3.
    cache_mode_raw = str(args.cache).strip().lower()
    if cache_mode_raw in {"false", "none", "0", "off"}:
        cache_mode: str | bool = False
    elif cache_mode_raw in {"ram", "disk"}:
        cache_mode = cache_mode_raw
    else:
        cache_mode = "disk"

    if args.ultralytics_root.exists() and str(args.ultralytics_root.resolve()) not in sys.path:
        # Ensure custom ECA-enabled ultralytics package has priority during import.
        sys.path.insert(0, str(args.ultralytics_root.resolve()))

    from ultralytics import YOLO  # type: ignore

    set_reproducibility(args.seed)
    args.project.mkdir(parents=True, exist_ok=True)
    ctx = create_run_context(args.project, prefix=args.run_prefix)

    # Save hyperparameters and host environment for reproducibility audits.
    save_json(
        ctx.run_dir / "hyperparams.json",
        {
            "data": str(args.data.resolve()),
            "model": str(args.model.resolve()),
            "epochs": args.epochs,
            "batch": args.batch,
            "imgsz": args.imgsz,
            "cache": cache_mode,
            "lr0": args.lr0,
            "optimizer": args.optimizer,
            "patience": args.patience,
            "save_period": args.save_period,
            "workers": args.workers,
            "device": args.device,
            "amp": args.amp,
            "seed": args.seed,
            "resume": args.resume,
            "ultralytics_root": str(args.ultralytics_root.resolve()),
        },
    )
    save_json(ctx.run_dir / "environment_snapshot.json", build_environment_snapshot())

    try:
        # Train with the same core optimization/data args as phase2 to keep comparisons fair.
        model = YOLO(str(args.model))
        train_results = model.train(
            data=str(args.data),
            epochs=args.epochs,
            batch=args.batch,
            imgsz=args.imgsz,
            cache=cache_mode,
            lr0=args.lr0,
            optimizer=args.optimizer,
            patience=args.patience,
            save_period=args.save_period,
            workers=args.workers,
            device=args.device,
            amp=args.amp,
            seed=args.seed,
            resume=args.resume,
            project=str(args.project),
            name=ctx.run_id,
            exist_ok=True,
            fliplr=0.5,
            flipud=0.1,
            degrees=8.0,
            scale=0.2,
            translate=0.1,
        )
    except Exception as exc:
        print(f"[ERROR] phase4 training failed: {exc}")
        print("Hint: ensure ECA is registered in training/ultralytics_custom/ultralytics/nn modules + tasks imports.")
        finalize_run_metadata(ctx, extra={"status": "failed", "error": str(exc)})
        return 2

    train_save_dir = Path(getattr(train_results, "save_dir", ctx.run_dir))
    results_csv = train_save_dir / "results.csv"
    metrics_csv = ctx.run_dir / "metrics_epoch.csv"
    normalize_results_csv(results_csv, metrics_csv)
    plot_metrics_curve(metrics_csv, ctx.run_dir / "plots" / "metrics_curve_1280x720.png")
    collect_confusion_matrix(train_save_dir, ctx.run_dir / "plots" / "confusion_matrix.png")

    finalize_run_metadata(ctx, extra={"status": "completed", "ultralytics_save_dir": str(train_save_dir.resolve())})
    print("[DONE] phase4_train_yolo11s_mbv3_eca")
    return 0


if __name__ == "__main__":
    sys.exit(main())
