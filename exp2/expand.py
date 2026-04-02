#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Batch launcher for exp2 compressed ablation set."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


DEFAULT_MODELS = ["p2_simam", "p2_simam_dwconv", "p2_simam_shuffle", "p2_simam_dwconv_p075ghost"]


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Run exp2 compressed ablation models in sequence")
    parser.add_argument("--python", type=str, default=sys.executable)
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--batch", type=int, default=6)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--device", type=str, default="0")
    parser.add_argument("--data", type=str, default=str(repo_root / "exp1" / "dataset" / "data.yaml"))
    parser.add_argument("--resume", action="store_true", default=True)
    parser.add_argument("--no-resume", action="store_false", dest="resume")
    parser.add_argument("--force-fresh", action="store_true")
    parser.add_argument("--strict-fairness", action="store_true", default=True)
    parser.add_argument("--no-strict-fairness", action="store_false", dest="strict_fairness")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    train_py = repo_root / "exp2" / "train.py"

    for name in args.models:
        # 中文注释：串行执行，避免显存与日志互相干扰。
        cmd = [
            args.python,
            str(train_py),
            "--model",
            name,
            "--data",
            str(args.data),
            "--epochs",
            str(args.epochs),
            "--batch",
            str(args.batch),
            "--imgsz",
            str(args.imgsz),
            "--workers",
            str(args.workers),
            "--device",
            str(args.device),
        ]
        if args.force_fresh:
            cmd.append("--force-fresh")
        if not args.resume:
            cmd.append("--no-resume")
        if not args.strict_fairness:
            cmd.append("--no-strict-fairness")
        print(f"[RUN] {' '.join(cmd)}")
        proc = subprocess.run(cmd, cwd=str(repo_root))
        if proc.returncode != 0:
            print(f"[ERROR] model={name} failed with code={proc.returncode}")
            return proc.returncode

    print("[DONE] exp2 batch finished")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
