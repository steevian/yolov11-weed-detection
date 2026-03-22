"""Evaluate four YOLO variants on test split with unified protocol."""

from __future__ import annotations

import argparse
import csv
import math
import sys
import time
from pathlib import Path

import numpy as np
import torch


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Evaluate YOLOv11-S/MBV3/ECA/ECA2 models")
    parser.add_argument("--data", type=Path, default=repo_root / "training" / "configs" / "data_3seasonweeddet10.yaml")
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--mbv3", type=Path, required=True)
    parser.add_argument("--eca", type=Path, required=True)
    parser.add_argument("--eca2", type=Path, required=True)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=1)
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--iters", type=int, default=100)
    parser.add_argument(
        "--out-csv",
        type=Path,
        default=repo_root / "experiments" / "summary" / "full200_validation_20260322" / "comparison_metrics_full200_4models.csv",
    )
    parser.add_argument(
        "--out-md",
        type=Path,
        default=repo_root / "experiments" / "summary" / "full200_validation_20260322" / "comparison_metrics_full200_4models.md",
    )
    parser.add_argument(
        "--ultralytics-root",
        type=Path,
        default=repo_root / "training" / "ultralytics_custom",
        help="Path containing custom ultralytics package root for custom modules like ECA",
    )
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


def measure_fps(model, imgsz: int, warmup: int, iters: int) -> float:
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


def measure_complexity(model, imgsz: int) -> tuple[float, float]:
    params = float(sum(p.numel() for p in model.model.parameters()))
    try:
        from thop import profile

        x = torch.randn(1, 3, imgsz, imgsz)
        flops, _ = profile(model.model.cpu(), inputs=(x,), verbose=False)
        return params, float(flops)
    except Exception:
        return params, float("nan")


def evaluate_one(
    name: str,
    weights: Path,
    data: Path,
    imgsz: int,
    batch: int,
    workers: int,
    warmup: int,
    iters: int,
    yolo_cls,
) -> dict[str, float | str]:
    model = yolo_cls(str(weights))
    res = model.val(data=str(data), split="test", imgsz=imgsz, batch=batch, workers=workers, verbose=False)

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


def fmt(value: float | str, digits: int = 4) -> str:
    if isinstance(value, str):
        return value
    if math.isnan(value) or math.isinf(value):
        return "N/A"
    return f"{value:.{digits}f}"


def write_markdown(path: Path, rows: list[dict[str, float | str]]) -> None:
    by_name = {str(r["model"]): r for r in rows}
    eca = by_name["YOLOv11-S-MBV3-ECA"]
    eca2 = by_name["YOLOv11-S-MBV3-ECA2"]

    d_map50 = float(eca2["map50"]) - float(eca["map50"])
    d_map5095 = float(eca2["map50_95"]) - float(eca["map50_95"])
    d_recall = float(eca2["recall"]) - float(eca["recall"])
    d_precision = float(eca2["precision"]) - float(eca["precision"])
    d_fps = float(eca2["fps"]) - float(eca["fps"])
    d_params = float(eca2["params"]) - float(eca["params"])
    d_flops = float(eca2["flops"]) - float(eca["flops"])

    rank_map = sorted(rows, key=lambda x: float(x["map50_95"]), reverse=True)
    rank_fps = sorted(rows, key=lambda x: float(x["fps"]), reverse=True)

    lines = [
        "# Full200 四模型统一测试评测",
        "",
        "| model | precision | recall | map50 | map50_95 | fps | params | flops |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    for r in rows:
        lines.append(
            "| {} | {} | {} | {} | {} | {} | {} | {} |".format(
                r["model"],
                fmt(float(r["precision"]), 4),
                fmt(float(r["recall"]), 4),
                fmt(float(r["map50"]), 4),
                fmt(float(r["map50_95"]), 4),
                fmt(float(r["fps"]), 2),
                fmt(float(r["params"]), 0),
                fmt(float(r["flops"]), 0),
            )
        )

    lines.extend(
        [
            "",
            "## ECA2 相对旧ECA差值",
            f"- precision: {fmt(d_precision, 4)}",
            f"- recall: {fmt(d_recall, 4)}",
            f"- map50: {fmt(d_map50, 4)}",
            f"- map50_95: {fmt(d_map5095, 4)}",
            f"- fps: {fmt(d_fps, 2)}",
            f"- params: {fmt(d_params, 0)}",
            f"- flops: {fmt(d_flops, 0)}",
            "",
            "## 排名",
            f"- map50_95 第一名: {rank_map[0]['model']} ({fmt(float(rank_map[0]['map50_95']), 4)})",
            f"- fps 第一名: {rank_fps[0]['model']} ({fmt(float(rank_fps[0]['fps']), 2)})",
        ]
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    if args.ultralytics_root.exists() and str(args.ultralytics_root.resolve()) not in sys.path:
        sys.path.insert(0, str(args.ultralytics_root.resolve()))

    from ultralytics import YOLO

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)

    rows = [
        evaluate_one("YOLOv11-S", args.baseline, args.data, args.imgsz, args.batch, args.workers, args.warmup, args.iters, YOLO),
        evaluate_one("YOLOv11-S-MBV3", args.mbv3, args.data, args.imgsz, args.batch, args.workers, args.warmup, args.iters, YOLO),
        evaluate_one("YOLOv11-S-MBV3-ECA", args.eca, args.data, args.imgsz, args.batch, args.workers, args.warmup, args.iters, YOLO),
        evaluate_one("YOLOv11-S-MBV3-ECA2", args.eca2, args.data, args.imgsz, args.batch, args.workers, args.warmup, args.iters, YOLO),
    ]

    with args.out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    write_markdown(args.out_md, rows)

    print("[DONE] phase5_evaluate_four_models")
    print(f"out_csv: {args.out_csv}")
    print(f"out_md: {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
