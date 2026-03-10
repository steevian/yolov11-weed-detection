"""Phase 3 training: YOLO11-S with MobileNetV3 backbone."""

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
    parser = argparse.ArgumentParser(description="Phase3 trainer: YOLO11-S + MobileNetV3")
    parser.add_argument(
        "--data",
        type=Path,
        default=REPO_ROOT / "training" / "configs" / "data_3seasonweeddet10.yaml",
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=REPO_ROOT / "training" / "configs" / "yolo11s_mbv3.yaml",
    )
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--lr0", type=float, default=0.01)
    parser.add_argument("--optimizer", type=str, default="SGD")
    parser.add_argument("--patience", type=int, default=50)
    parser.add_argument("--save-period", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--project",
        type=Path,
        default=REPO_ROOT / "experiments" / "YOLOv11-S-MBV3",
    )
    parser.add_argument("--run-prefix", type=str, default="mbv3")
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

    from ultralytics import YOLO  # Local import to keep startup fast and controllable.

    set_reproducibility(args.seed)
    args.project.mkdir(parents=True, exist_ok=True)
    ctx = create_run_context(args.project, prefix=args.run_prefix)

    save_json(
        ctx.run_dir / "hyperparams.json",
        {
            "data": str(args.data.resolve()),
            "model": str(args.model.resolve()),
            "epochs": args.epochs,
            "batch": args.batch,
            "imgsz": args.imgsz,
            "lr0": args.lr0,
            "optimizer": args.optimizer,
            "patience": args.patience,
            "save_period": args.save_period,
            "seed": args.seed,
            "resume": args.resume,
            "backbone_init": "torchvision MobileNetV3 DEFAULT weights via TorchVision module",
        },
    )
    save_json(ctx.run_dir / "environment_snapshot.json", build_environment_snapshot())

    try:
        model = YOLO(str(args.model))
        train_results = model.train(
            data=str(args.data),
            epochs=args.epochs,
            batch=args.batch,
            imgsz=args.imgsz,
            lr0=args.lr0,
            optimizer=args.optimizer,
            patience=args.patience,
            save_period=args.save_period,
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
        print(f"[ERROR] phase3 training failed: {exc}")
        finalize_run_metadata(ctx, extra={"status": "failed", "error": str(exc)})
        return 2

    train_save_dir = Path(getattr(train_results, "save_dir", ctx.run_dir))
    results_csv = train_save_dir / "results.csv"
    metrics_csv = ctx.run_dir / "metrics_epoch.csv"
    normalize_results_csv(results_csv, metrics_csv)
    plot_metrics_curve(metrics_csv, ctx.run_dir / "plots" / "metrics_curve_1280x720.png")
    collect_confusion_matrix(train_save_dir, ctx.run_dir / "plots" / "confusion_matrix.png")

    finalize_run_metadata(ctx, extra={"status": "completed", "ultralytics_save_dir": str(train_save_dir.resolve())})
    print("[DONE] phase3_train_yolo11s_mbv3")
    return 0


if __name__ == "__main__":
    sys.exit(main())
