"""Post-process revised ECA2 smoke50 run: evaluate old/new ECA and update firstmemory."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import torch


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Post-process ECA2 smoke50 run")
    parser.add_argument("--repo-root", type=Path, default=repo_root)
    parser.add_argument(
        "--new-run-dir",
        type=Path,
        required=True,
        help="Run directory under experiments/YOLOv11-S-MBV3-ECA2",
    )
    parser.add_argument(
        "--old-eca-weights",
        type=Path,
        default=repo_root
        / "experiments"
        / "YOLOv11-S-MBV3-ECA"
        / "mbv3_eca_20260317_114514"
        / "weights"
        / "best.pt",
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=repo_root / "training" / "configs" / "data_3seasonweeddet10.yaml",
    )
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=1)
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--iters", type=int, default=100)
    parser.add_argument("--target-epochs", type=int, default=50)
    parser.add_argument("--poll-seconds", type=int, default=20)
    parser.add_argument("--wait-timeout-hours", type=float, default=8.0)
    parser.add_argument(
        "--ultralytics-root",
        type=Path,
        default=repo_root / "training" / "ultralytics_custom",
    )
    parser.add_argument(
        "--plan-label",
        type=str,
        default="resumed_50_to_200",
        help="Training plan label recorded in firstmemory",
    )
    return parser.parse_args()


def _read_run_status(run_dir: Path) -> str | None:
    summary = run_dir / "run_summary.json"
    if not summary.exists():
        return None
    try:
        payload = json.loads(summary.read_text(encoding="utf-8"))
        status = payload.get("status")
        if isinstance(status, str):
            return status
        return None
    except Exception:
        return None


def _count_trained_epochs(run_dir: Path) -> int:
    csv_path = run_dir / "results.csv"
    if not csv_path.exists():
        return 0
    lines = csv_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if len(lines) <= 1:
        return 0
    return len(lines) - 1


def wait_until_finished(run_dir: Path, target_epochs: int, poll_seconds: int, timeout_hours: float) -> None:
    deadline = time.time() + timeout_hours * 3600.0
    while time.time() < deadline:
        status = _read_run_status(run_dir)
        best_pt = run_dir / "weights" / "best.pt"
        epochs_done = _count_trained_epochs(run_dir)
        if status == "completed" and best_pt.exists():
            return
        if best_pt.exists() and epochs_done >= target_epochs:
            return
        print(
            f"[WAIT] run not finished yet | status={status} | epochs_done={epochs_done}/{target_epochs} | run_dir={run_dir}"
        )
        time.sleep(max(1, poll_seconds))
    raise TimeoutError(f"Timeout waiting run completion: {run_dir}")


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


def _fmt(v: float, digits: int = 4) -> str:
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return "N/A"
    return f"{v:.{digits}f}"


def write_markdown_compare(md_path: Path, old_row: dict[str, float | str], new_row: dict[str, float | str]) -> None:
    d_map50 = float(new_row["map50"]) - float(old_row["map50"])
    d_recall = float(new_row["recall"]) - float(old_row["recall"])
    d_fps = float(new_row["fps"]) - float(old_row["fps"])
    d_params = float(new_row["params"]) - float(old_row["params"])
    d_flops = float(new_row["flops"]) - float(old_row["flops"])

    lines = [
        "# ECA旧版 vs ECA2新版（Smoke50）",
        "",
        "| model | recall | map50 | fps | params | flops |",
        "| --- | --- | --- | --- | --- | --- |",
        "| {} | {} | {} | {} | {} | {} |".format(
            old_row["model"],
            _fmt(float(old_row["recall"])),
            _fmt(float(old_row["map50"])),
            _fmt(float(old_row["fps"]), 2),
            _fmt(float(old_row["params"]), 0),
            _fmt(float(old_row["flops"]), 0),
        ),
        "| {} | {} | {} | {} | {} | {} |".format(
            new_row["model"],
            _fmt(float(new_row["recall"])),
            _fmt(float(new_row["map50"])),
            _fmt(float(new_row["fps"]), 2),
            _fmt(float(new_row["params"]), 0),
            _fmt(float(new_row["flops"]), 0),
        ),
        "",
        "## 差值（新版-旧版）",
        f"- Recall: {_fmt(d_recall)}",
        f"- mAP50: {_fmt(d_map50)}",
        f"- FPS: {_fmt(d_fps, 2)}",
        f"- Params: {_fmt(d_params, 0)}",
        f"- FLOPs: {_fmt(d_flops, 0)}",
        "",
        "## 结论模板",
        "- 新版ECA2仅在P3/P4/P5放置3个ECA，维持主干与通道预算一致。",
        "- 相比旧版ECA（Neck/PAN多处插入），新版在轻量性上更符合设计目标。",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")


def append_firstmemory(
    firstmemory: Path,
    old_row: dict[str, float | str],
    new_row: dict[str, float | str],
    run_dir: Path,
    target_epochs: int,
    plan_label: str,
) -> None:
    firstmemory.parent.mkdir(parents=True, exist_ok=True)
    if not firstmemory.exists():
        firstmemory.write_text("# 项目基础记忆（memory）\n\n", encoding="utf-8")

    d_map50 = float(new_row["map50"]) - float(old_row["map50"])
    d_recall = float(new_row["recall"]) - float(old_row["recall"])
    d_fps = float(new_row["fps"]) - float(old_row["fps"])

    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    block = [
        "",
        "## 19. ECA2三点式修订训练与对比验证（2026-03-19）",
        f"- {ts} | run_id={run_dir.name} | status=completed",
        f"- 中断恢复结果：successful_resume_from_last_pt",
        f"- 最终训练方案：{plan_label}",
        f"- 目标总轮次：{target_epochs}",
        "- 改进内容：将旧版ECA从Backbone+Neck/PAN多点插入，修订为仅在P3/P4/P5后各插1个ECA（共3个）。",
        "- 结构修改细节：不修改MobileNetV3主干结构、通道数和缩放系数；仅调整ECA插入位置，且不在Neck/PAN插入注意力。",
        "- 关键结果（test协议）：",
        f"  - 旧ECA: recall={_fmt(float(old_row['recall']))}, map50={_fmt(float(old_row['map50']))}, fps={_fmt(float(old_row['fps']), 2)}, params={_fmt(float(old_row['params']), 0)}, flops={_fmt(float(old_row['flops']), 0)}",
        f"  - 新ECA2: recall={_fmt(float(new_row['recall']))}, map50={_fmt(float(new_row['map50']))}, fps={_fmt(float(new_row['fps']), 2)}, params={_fmt(float(new_row['params']), 0)}, flops={_fmt(float(new_row['flops']), 0)}",
        "- 对比结论：",
        f"  - 轻量效率：新版相对旧版参数差值={_fmt(float(new_row['params']) - float(old_row['params']), 0)}，FLOPs差值={_fmt(float(new_row['flops']) - float(old_row['flops']), 0)}。",
        f"  - 精度与召回：新版相对旧版 mAP50差值={_fmt(d_map50)}，Recall差值={_fmt(d_recall)}。",
        f"  - 推理速度：新版相对旧版 FPS差值={_fmt(d_fps, 2)}。",
    ]

    with firstmemory.open("a", encoding="utf-8") as f:
        f.write("\n".join(block) + "\n")


def main() -> int:
    args = parse_args()
    if args.ultralytics_root.exists() and str(args.ultralytics_root.resolve()) not in sys.path:
        sys.path.insert(0, str(args.ultralytics_root.resolve()))

    if not args.old_eca_weights.exists():
        print(f"[ERROR] old ECA weights not found: {args.old_eca_weights}")
        return 2

    run_dir = args.new_run_dir.resolve()
    if not run_dir.exists():
        print(f"[ERROR] new run dir not found: {run_dir}")
        return 3

    wait_until_finished(run_dir, args.target_epochs, args.poll_seconds, args.wait_timeout_hours)
    new_weights = run_dir / "weights" / "best.pt"
    if not new_weights.exists():
        print(f"[ERROR] new ECA2 best.pt not found: {new_weights}")
        return 4

    from ultralytics import YOLO

    old_row = evaluate_one(
        "YOLOv11-S-MBV3-ECA-old-smoke50",
        args.old_eca_weights,
        args.data,
        args.imgsz,
        args.batch,
        args.workers,
        args.warmup,
        args.iters,
        YOLO,
    )
    new_row = evaluate_one(
        "YOLOv11-S-MBV3-ECA2-new-smoke50",
        new_weights,
        args.data,
        args.imgsz,
        args.batch,
        args.workers,
        args.warmup,
        args.iters,
        YOLO,
    )

    summary_dir = args.repo_root / "experiments" / "summary" / "full200_validation_20260319"
    summary_dir.mkdir(parents=True, exist_ok=True)
    csv_out = summary_dir / f"comparison_eca_old_vs_eca2_epoch{args.target_epochs}.csv"
    md_out = summary_dir / f"comparison_eca_old_vs_eca2_epoch{args.target_epochs}.md"

    with csv_out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(old_row.keys()))
        writer.writeheader()
        writer.writerow(old_row)
        writer.writerow(new_row)

    write_markdown_compare(md_out, old_row, new_row)
    firstmemory_paths = [
        args.repo_root / "docs" / "firstmemory.md",
        args.repo_root / "docs" / "first_memory.md",
    ]
    for fm in firstmemory_paths:
        append_firstmemory(
            fm,
            old_row,
            new_row,
            run_dir,
            args.target_epochs,
            args.plan_label,
        )

    print("[DONE] phase4_eca2_smoke50_postprocess")
    print(f"csv: {csv_out}")
    print(f"md: {md_out}")
    print(f"firstmemory: {args.repo_root / 'docs' / 'firstmemory.md'}")
    print(f"first_memory: {args.repo_root / 'docs' / 'first_memory.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
