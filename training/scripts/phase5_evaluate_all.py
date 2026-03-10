"""Phase 5: evaluate three models with unified protocol."""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

import numpy as np
import torch
from ultralytics import YOLO


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Evaluate baseline/mbv3/mbv3+eca models")
    parser.add_argument("--data", type=Path, default=repo_root / "training" / "configs" / "data_3seasonweeddet10.yaml")
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--mbv3", type=Path, required=True)
    parser.add_argument("--mbv3-eca", type=Path, required=True)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--iters", type=int, default=100)
    parser.add_argument("--out-csv", type=Path, default=repo_root / "experiments" / "summary" / "comparison_metrics.csv")
    return parser.parse_args()


def get_metric(res, key: str, default: float = float("nan")) -> float:
    value = getattr(res.box, key, None)
    if value is None:
        return default
    if isinstance(value, (list, tuple, np.ndarray)):
        return float(np.mean(value))
    try:
        return float(value)
    except Exception:
        return default


def measure_fps(model: YOLO, imgsz: int, warmup: int, iters: int) -> float:
    x = torch.randn(1, 3, imgsz, imgsz)
    if torch.cuda.is_available():
        x = x.cuda()
        model.model.cuda()

    with torch.no_grad():
        for _ in range(warmup):
            _ = model.model(x)
        if torch.cuda.is_available():
            torch.cuda.synchronize()

        t0 = time.perf_counter()
        for _ in range(iters):
            _ = model.model(x)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        t1 = time.perf_counter()
    return iters / (t1 - t0)


def measure_complexity(model: YOLO, imgsz: int) -> tuple[float, float]:
    params = float(sum(p.numel() for p in model.model.parameters()))
    try:
        from thop import profile

        x = torch.randn(1, 3, imgsz, imgsz)
        flops, _ = profile(model.model.cpu(), inputs=(x,), verbose=False)
        return params, float(flops)
    except Exception:
        return params, float("nan")


def evaluate_one(name: str, weights: Path, data: Path, imgsz: int, warmup: int, iters: int) -> dict[str, float | str]:
    model = YOLO(str(weights))
    res = model.val(data=str(data), split="test", imgsz=imgsz, batch=1, verbose=False)

    params, flops = measure_complexity(model, imgsz)
    fps = measure_fps(model, imgsz, warmup=warmup, iters=iters)

    return {
        "model": name,
        "weights": str(weights),
        "precision": get_metric(res, "mp"),
        "recall": get_metric(res, "mr"),
        "map50": get_metric(res, "map50"),
        "map50_95": get_metric(res, "map"),
        "fps": fps,
        "params": params,
        "flops": flops,
    }


def main() -> int:
    args = parse_args()
    args.out_csv.parent.mkdir(parents=True, exist_ok=True)

    rows = [
        evaluate_one("YOLOv11-S", args.baseline, args.data, args.imgsz, args.warmup, args.iters),
        evaluate_one("YOLOv11-S-MBV3", args.mbv3, args.data, args.imgsz, args.warmup, args.iters),
        evaluate_one("YOLOv11-S-MBV3-ECA", args.mbv3_eca, args.data, args.imgsz, args.warmup, args.iters),
    ]

    with args.out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("[DONE] phase5_evaluate_all")
    print(f"out_csv: {args.out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
