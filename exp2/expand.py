#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Batch launcher for exp2 compressed ablation set."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


DEFAULT_STAGEA_MODELS = ["a1_p2", "p2_simam_dwconv", "p2_simam_shuffle"]
DEFAULT_EXTENDED_MODELS = DEFAULT_STAGEA_MODELS + ["p2_simam_dwconv_p075ghost"]


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Run exp2 compressed ablation models in sequence")
    parser.add_argument("--python", type=str, default=sys.executable)
    parser.add_argument(
        "--preset",
        choices=["stagea", "extended", "custom"],
        default="stagea",
        help="Model preset. stagea runs the three primary stageA candidates; extended adds the aggressive control.",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=None,
        help="Custom model list. Overrides --preset when provided.",
    )
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


def resolve_models(args: argparse.Namespace) -> list[str]:
    if args.models:
        return list(args.models)
    if args.preset == "extended":
        return list(DEFAULT_EXTENDED_MODELS)
    return list(DEFAULT_STAGEA_MODELS)


def dump_manifest(repo_root: Path, payload: dict[str, object]) -> None:
    meta_dir = repo_root / "exp2" / "meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    manifest = meta_dir / "expand_manifest.json"
    manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    train_py = repo_root / "exp2" / "train.py"
    models = resolve_models(args)

    dump_manifest(
        repo_root,
        {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "preset": args.preset,
            "models": models,
            "python": args.python,
            "epochs": args.epochs,
            "batch": args.batch,
            "imgsz": args.imgsz,
            "workers": args.workers,
            "device": args.device,
            "data": str(Path(args.data).resolve()),
            "resume": bool(args.resume),
            "force_fresh": bool(args.force_fresh),
            "strict_fairness": bool(args.strict_fairness),
        },
    )

    for name in models:
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

    print(f"[DONE] exp2 batch finished with preset={args.preset} models={models}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
