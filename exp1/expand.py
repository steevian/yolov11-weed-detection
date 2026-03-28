#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Optional expansion experiments for ECA model")
    parser.add_argument("--run", action="store_true", help="Execute train commands instead of only exporting plan")
    parser.add_argument("--python", type=str, default=sys.executable)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out-csv", type=Path, default=repo_root / "exp1" / "expand" / "expand_plan.csv")
    parser.add_argument("--result-csv", type=Path, default=repo_root / "exp1" / "expand" / "expand_results.csv")
    return parser.parse_args()


def build_plan() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    for ratio in ["7:1:2", "6:2:2", "5:2:3"]:
        rows.append({"group": "split_ratio", "name": ratio, "epochs": "200", "lr0": "0.01", "sample_ratio": "1.0"})

    for sample_ratio in ["1.0", "0.7", "0.5"]:
        rows.append({"group": "sample_size", "name": sample_ratio, "epochs": "200", "lr0": "0.01", "sample_ratio": sample_ratio})

    for lr in ["0.001", "0.005", "0.01"]:
        rows.append({"group": "learning_rate", "name": lr, "epochs": "100", "lr0": lr, "sample_ratio": "1.0"})

    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def run_one(py: str, row: dict[str, str]) -> dict[str, str]:
    repo_root = Path(__file__).resolve().parents[1]
    cmd = [
        py,
        str(repo_root / "exp1" / "train.py"),
        "--model",
        "eca",
        "--epochs",
        row["epochs"],
    ]

    # Keep training arguments mostly fixed. For LR sweep, override using env to avoid changing train.py contract.
    env = dict(**os.environ)
    env["EXP1_LR0_OVERRIDE"] = row["lr0"]
    env["EXP1_SEED"] = "42"

    proc = subprocess.run(cmd, cwd=str(repo_root), env=env, capture_output=True, text=True)
    return {
        "group": row["group"],
        "name": row["name"],
        "epochs": row["epochs"],
        "lr0": row["lr0"],
        "returncode": str(proc.returncode),
        "ok": "1" if proc.returncode == 0 else "0",
    }


def main() -> int:
    args = parse_args()
    plan = build_plan()
    write_csv(args.out_csv, plan)

    if not args.run:
        print(f"[DONE] plan exported: {args.out_csv}")
        return 0

    results: list[dict[str, str]] = []
    for row in plan:
        results.append(run_one(args.python, row))

    write_csv(args.result_csv, results)
    summary = {
        "total": len(results),
        "success": sum(1 for r in results if r["ok"] == "1"),
        "failed": sum(1 for r in results if r["ok"] != "1"),
    }
    (args.result_csv.parent / "expand_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[DONE] results exported: {args.result_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
