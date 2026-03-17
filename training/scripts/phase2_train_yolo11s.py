"""Phase 2 baseline training script for YOLOv11-S.

Design goals:
1) Fair comparison: key training params are aligned with phase3/phase4.
2) Full-state resume: continue from last.pt with optimizer/lr/epoch state.
3) Data preservation: always emit train.log, env.txt, run_summary.json.

功能简介（中文）：
1) 执行 Phase2 基线 200 轮训练；
2) 支持完整断点续训与异常分类；
3) 自动保存可复现实验资产并写入追踪日志。
"""

from __future__ import annotations

import argparse
import random
import sys
import time
import traceback
from pathlib import Path
from typing import TextIO

import numpy as np
import torch
from ultralytics import YOLO

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from training.lib.experiment_logger import (  # noqa: E402
    ExperimentContext,
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
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=None,
        help="Checkpoint for resume mode. If omitted, auto-pick latest last.pt under project.",
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
        default=REPO_ROOT / "experiments" / "YOLOv11-S",
        help="Ultralytics project output root",
    )
    parser.add_argument(
        "--run-prefix",
        type=str,
        default="baseline_full200_fresh",
        help="Run prefix, final run_id is <prefix>_<timestamp>",
    )
    parser.add_argument(
        "--gpu-failure-exit-code",
        type=int,
        default=12,
        help="Dedicated exit code for CUDA/bad-allocation failures so watchdog can apply longer cooldown",
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


class _Tee:
    def __init__(self, file_obj: TextIO, original_stream: TextIO):
        self._file = file_obj
        self._original = original_stream

    def write(self, data: str) -> int:
        self._file.write(data)
        self._file.flush()
        return self._original.write(data)

    def flush(self) -> None:
        self._file.flush()
        self._original.flush()


def _append_markdown_event(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    payload = [f"## {ts} | {title}", ""] + [f"- {line}" for line in lines] + [""]
    with path.open("a", encoding="utf-8") as f:
        f.write("\n".join(payload))


def _update_firstmemory(firstmemory_path: Path, run_id: str, status: str) -> None:
    marker = "## 12. Phase2自动更新追踪"
    firstmemory_path.parent.mkdir(parents=True, exist_ok=True)
    if not firstmemory_path.exists():
        firstmemory_path.write_text("# 项目基础记忆（memory）\n\n", encoding="utf-8")
    text = firstmemory_path.read_text(encoding="utf-8")
    line = f"- {time.strftime('%Y-%m-%d %H:%M:%S')} | run_id={run_id} | status={status}"
    if marker not in text:
        text = text.rstrip() + "\n\n" + marker + "\n" + line + "\n"
    else:
        text = text.rstrip() + "\n" + line + "\n"
    firstmemory_path.write_text(text, encoding="utf-8")


def _resolve_resume_checkpoint(project: Path, explicit: Path | None) -> Path | None:
    if explicit is not None:
        return explicit if explicit.exists() else None
    ckpts = sorted(project.glob("*/weights/last.pt"), key=lambda p: p.stat().st_mtime, reverse=True)
    return ckpts[0] if ckpts else None


def main() -> int:
    args = parse_args()
    # Normalize cache mode once to avoid config drift between fresh/resume runs.
    cache_mode_raw = str(args.cache).strip().lower()
    if cache_mode_raw in {"false", "none", "0", "off"}:
        cache_mode: str | bool = False
    elif cache_mode_raw in {"ram", "disk"}:
        cache_mode = cache_mode_raw
    else:
        cache_mode = "disk"

    if not args.data.exists():
        print(f"[ERROR] data yaml not found: {args.data}")
        return 1

    set_reproducibility(args.seed)

    args.project.mkdir(parents=True, exist_ok=True)
    resume_ckpt: Path | None = None
    if args.resume:
        # Resume must reuse the original run directory to keep metrics/checkpoints in one lineage.
        resume_ckpt = _resolve_resume_checkpoint(args.project, args.checkpoint)
        if resume_ckpt is None:
            print("[ERROR] resume requested but no valid checkpoint found.")
            return 3
        resume_run_dir = resume_ckpt.parent.parent
        ctx = ExperimentContext(run_id=resume_run_dir.name, run_dir=resume_run_dir, started_at=time.time())
        train_source = str(resume_ckpt)
    else:
        ctx = create_run_context(args.project, prefix=args.run_prefix)
        train_source = args.weights

    docs_dir = REPO_ROOT / "docs"
    trianlog_path = docs_dir / "trianlog.md"
    firstmemory_path = docs_dir / "firstmemory.md"

    log_file = ctx.run_dir / "train.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_fp = log_file.open("a", encoding="utf-8")
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = _Tee(log_fp, original_stdout)
    sys.stderr = _Tee(log_fp, original_stderr)

    hyperparams = {
        "data": str(args.data.resolve()),
        "weights": args.weights,
        "checkpoint": str(resume_ckpt.resolve()) if resume_ckpt else None,
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
        "augment": {
            "fliplr": 0.5,
            "flipud": 0.1,
            "degrees": 8.0,
            "scale": 0.2,
            "translate": 0.1,
        },
    }
    # Persist experiment contract and environment snapshot for post-mortem reproducibility.
    save_json(ctx.run_dir / "hyperparams.json", hyperparams)
    env_snapshot = build_environment_snapshot()
    save_json(ctx.run_dir / "environment_snapshot.json", env_snapshot)
    (ctx.run_dir / "env.txt").write_text(
        "\n".join([
            f"python={env_snapshot.get('python', 'N/A')}",
            f"platform={env_snapshot.get('platform', 'N/A')}",
            f"processor={env_snapshot.get('processor', 'N/A')}",
            f"device={args.device}",
            f"amp={args.amp}",
            f"cache={cache_mode}",
            f"workers={args.workers}",
        ]),
        encoding="utf-8",
    )

    _append_markdown_event(
        trianlog_path,
        "Phase2启动",
        [
            f"run_id={ctx.run_id}",
            f"resume={args.resume}",
            f"checkpoint={str(resume_ckpt) if resume_ckpt else 'N/A'}",
            f"epochs={args.epochs}, batch={args.batch}, workers={args.workers}, cache={cache_mode}, amp={args.amp}",
        ],
    )

    print(f"[INFO] run_id={ctx.run_id}")
    print(f"[INFO] run_dir={ctx.run_dir}")

    # Keep these kwargs explicitly aligned with phase3/phase4 for fair comparison.
    train_kwargs = {
        "data": str(args.data),
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
        "project": str(args.project),
        "name": ctx.run_id,
        "exist_ok": True,
        "fliplr": hyperparams["augment"]["fliplr"],
        "flipud": hyperparams["augment"]["flipud"],
        "degrees": hyperparams["augment"]["degrees"],
        "scale": hyperparams["augment"]["scale"],
        "translate": hyperparams["augment"]["translate"],
    }

    try:
        model = YOLO(train_source)
        train_results = model.train(**train_kwargs)
    except KeyboardInterrupt:
        message = "Training interrupted by user/terminal."
        print(f"[WARN] {message}")
        _append_markdown_event(trianlog_path, "Phase2中断", [f"run_id={ctx.run_id}", message])
        finalize_run_metadata(ctx, extra={"status": "interrupted", "error": message})
        _update_firstmemory(firstmemory_path, ctx.run_id, "interrupted")
        return 130
    except Exception as exc:
        tb = traceback.format_exc(limit=20)
        print("[ERROR] Training failed.")
        print(f"detail: {exc}")
        err_text = str(exc).lower()
        is_gpu_memory_like = (
            "bad allocation" in err_text
            or "out of memory" in err_text
            or "cuda error" in err_text
            or "cublas" in err_text
        )
        status = "failed_gpu_memory" if is_gpu_memory_like else "failed"
        err_kind = "gpu_memory_like" if is_gpu_memory_like else "generic"
        _append_markdown_event(
            trianlog_path,
            "Phase2异常",
            [f"run_id={ctx.run_id}", f"error={exc}", f"error_kind={err_kind}", "traceback:", tb],
        )
        finalize_run_metadata(ctx, extra={"status": status, "error": str(exc), "error_kind": err_kind})
        _update_firstmemory(firstmemory_path, ctx.run_id, status)
        return args.gpu_failure_exit_code if is_gpu_memory_like else 2
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        log_fp.close()

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
            "train_log": str(log_file.resolve()),
        },
    )
    _append_markdown_event(
        trianlog_path,
        "Phase2完成",
        [
            f"run_id={ctx.run_id}",
            f"results_csv={results_csv if results_csv.exists() else 'N/A'}",
            f"train_log={log_file}",
        ],
    )
    _update_firstmemory(firstmemory_path, ctx.run_id, "completed")
    print("[DONE] phase2_train_yolo11s")
    print(f"summary: {ctx.run_dir / 'run_summary.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
