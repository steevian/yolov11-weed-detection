"""Phase 2 baseline training script for YOLOv11-S.

This script writes all outputs under experiments/YOLOv11-S/<run_id>/
and keeps extra metadata for thesis reproducibility.
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

import numpy as np
import torch
from ultralytics import YOLO

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
    parser = argparse.ArgumentParser(description="Phase2 baseline trainer for YOLOv11-S")
    parser.add_argument(
        "--data",
        type=Path,
        default=REPO_ROOT / "training" / "configs" / "data_3seasonweeddet10.yaml",
    )
    parser.add_argument("--weights", type=str, default="yolo11s.pt")
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
        default=REPO_ROOT / "experiments" / "YOLOv11-S",
        help="Ultralytics project output root",
    )
    parser.add_argument(
        "--run-prefix",
        type=str,
        default="baseline",
        help="Run prefix, final run_id is <prefix>_<timestamp>",
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
    if not args.data.exists():
        print(f"[ERROR] data yaml not found: {args.data}")
        return 1

    set_reproducibility(args.seed)

    args.project.mkdir(parents=True, exist_ok=True)
    ctx = create_run_context(args.project, prefix=args.run_prefix)

    hyperparams = {
        "data": str(args.data.resolve()),
        "weights": args.weights,
        "epochs": args.epochs,
        "batch": args.batch,
        "imgsz": args.imgsz,
        "lr0": args.lr0,
        "optimizer": args.optimizer,
        "patience": args.patience,
        "save_period": args.save_period,
        "seed": args.seed,
        "resume": args.resume,
        "augment": {
            "fliplr": 0.5,
            "flipud": 0.1,
            "degrees": 8.0,
            "scale": 0.2,
            "translate": 0.1,
            # Gaussian noise is best injected via Albumentations pipeline in later phases.
        },
    }
    save_json(ctx.run_dir / "hyperparams.json", hyperparams)
    save_json(ctx.run_dir / "environment_snapshot.json", build_environment_snapshot())

    print(f"[INFO] run_id={ctx.run_id}")
    print(f"[INFO] run_dir={ctx.run_dir}")

    try:
        model = YOLO(args.weights)
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
            fliplr=hyperparams["augment"]["fliplr"],
            flipud=hyperparams["augment"]["flipud"],
            degrees=hyperparams["augment"]["degrees"],
            scale=hyperparams["augment"]["scale"],
            translate=hyperparams["augment"]["translate"],
        )
    except Exception as exc:
        print("[ERROR] Training failed.")
        print("Hint: retry with --resume after fixing the root cause.")
        print(f"detail: {exc}")
        finalize_run_metadata(ctx, extra={"status": "failed", "error": str(exc)})
        return 2

    train_save_dir = Path(getattr(train_results, "save_dir", ctx.run_dir))
    results_csv = train_save_dir / "results.csv"
    metrics_csv = ctx.run_dir / "metrics_epoch.csv"
    normalize_results_csv(results_csv, metrics_csv)
    plot_metrics_curve(metrics_csv, ctx.run_dir / "plots" / "metrics_curve_1280x720.png")
    collect_confusion_matrix(train_save_dir, ctx.run_dir / "plots" / "confusion_matrix.png")

    finalize_run_metadata(
        ctx,
        extra={
            "status": "completed",
            "ultralytics_save_dir": str(train_save_dir.resolve()),
            "results_csv": str(results_csv.resolve()) if results_csv.exists() else "N/A",
        },
    )
    print("[DONE] phase2_train_yolo11s")
    print(f"summary: {ctx.run_dir / 'run_summary.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
