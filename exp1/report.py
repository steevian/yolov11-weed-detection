#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Generate exp1 markdown report")
    parser.add_argument("--eval-dir", type=Path, default=repo_root / "exp1" / "eval")
    parser.add_argument("--expand-csv", type=Path, default=repo_root / "exp1" / "expand" / "expand_results.csv")
    parser.add_argument("--out", type=Path, default=repo_root / "exp1" / "reports" / "exp1_report.md")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def fmt(v: Any, digits: int = 4) -> str:
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    if v is None:
        return "N/A"
    return str(v)


def md_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for r in rows:
        lines.append("| " + " | ".join(r) + " |")
    return lines


def load_expand_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    args = parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)

    baseline = load_json(args.eval_dir / "baseline_test_results.json")
    mbv3 = load_json(args.eval_dir / "mbv3_test_results.json")
    eca = load_json(args.eval_dir / "eca_test_results.json")

    def m(d: dict[str, Any], key: str) -> Any:
        return (((d.get("metrics") or {}).get(key)))

    ablation_rows = [
        ["baseline", fmt(m(baseline, "precision")), fmt(m(baseline, "recall")), fmt(m(baseline, "mAP50")), fmt(m(baseline, "mAP50-95")), fmt(m(baseline, "FPS"), 2)],
        ["mbv3", fmt(m(mbv3, "precision")), fmt(m(mbv3, "recall")), fmt(m(mbv3, "mAP50")), fmt(m(mbv3, "mAP50-95")), fmt(m(mbv3, "FPS"), 2)],
        ["eca", fmt(m(eca, "precision")), fmt(m(eca, "recall")), fmt(m(eca, "mAP50")), fmt(m(eca, "mAP50-95")), fmt(m(eca, "FPS"), 2)],
    ]

    light_rows = [
        ["baseline", fmt(m(baseline, "Params(M)"), 3), fmt(m(baseline, "FLOPs(G)"), 3), fmt(m(baseline, "FPS"), 2)],
        ["mbv3", fmt(m(mbv3, "Params(M)"), 3), fmt(m(mbv3, "FLOPs(G)"), 3), fmt(m(mbv3, "FPS"), 2)],
        ["eca", fmt(m(eca, "Params(M)"), 3), fmt(m(eca, "FLOPs(G)"), 3), fmt(m(eca, "FPS"), 2)],
    ]

    expand_rows_raw = load_expand_rows(args.expand_csv)
    expand_rows = [[r.get("group", ""), r.get("name", ""), r.get("epochs", ""), r.get("lr0", ""), r.get("ok", "")] for r in expand_rows_raw]

    lines: list[str] = []
    lines.append("# exp1 实验汇总报告")
    lines.append("")
    lines.append("## 消融实验对比表")
    lines.extend(md_table(["Model", "Precision", "Recall", "mAP50", "mAP50-95", "FPS"], ablation_rows))
    lines.append("")
    lines.append("## 轻量化指标表")
    lines.extend(md_table(["Model", "Params(M)", "FLOPs(G)", "FPS"], light_rows))
    lines.append("")
    lines.append("## 扩充实验对比表")
    if expand_rows:
        lines.extend(md_table(["Group", "Name", "Epochs", "LR0", "OK"], expand_rows))
    else:
        lines.append("暂无扩充实验结果。")
    lines.append("")

    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[DONE] report generated: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
