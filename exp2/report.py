#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Generate exp2 markdown report")
    parser.add_argument("--exp1-eval-dir", type=Path, default=repo_root / "exp1" / "eval")
    parser.add_argument("--exp2-eval-dir", type=Path, default=repo_root / "exp2" / "eval")
    parser.add_argument("--out", type=Path, default=repo_root / "exp2" / "reports" / "exp2_report.md")
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


def m(d: dict[str, Any], key: str) -> Any:
    return ((d.get("metrics") or {}).get(key))


def main() -> int:
    args = parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)

    baseline = load_json(args.exp1_eval_dir / "baseline_test_results.json")
    mbv3 = load_json(args.exp1_eval_dir / "mbv3_test_results.json")
    p2_simam = load_json(args.exp2_eval_dir / "p2_simam_test_results.json")
    p2_simam_dw = load_json(args.exp2_eval_dir / "p2_simam_dwconv_test_results.json")
    p2_simam_sh = load_json(args.exp2_eval_dir / "p2_simam_shuffle_test_results.json")
    p2_simam_dw_p075g = load_json(args.exp2_eval_dir / "p2_simam_dwconv_p075ghost_test_results.json")

    rows = [
        ["baseline (exp1 reference)", fmt(m(baseline, "precision")), fmt(m(baseline, "recall")), fmt(m(baseline, "mAP50")), fmt(m(baseline, "mAP50-95")), fmt(m(baseline, "Params(M)"), 3), fmt(m(baseline, "FPS"), 2)],
        ["mbv3 (exp1 reference)", fmt(m(mbv3, "precision")), fmt(m(mbv3, "recall")), fmt(m(mbv3, "mAP50")), fmt(m(mbv3, "mAP50-95")), fmt(m(mbv3, "Params(M)"), 3), fmt(m(mbv3, "FPS"), 2)],
        ["p2_simam", fmt(m(p2_simam, "precision")), fmt(m(p2_simam, "recall")), fmt(m(p2_simam, "mAP50")), fmt(m(p2_simam, "mAP50-95")), fmt(m(p2_simam, "Params(M)"), 3), fmt(m(p2_simam, "FPS"), 2)],
        ["p2_simam_dwconv", fmt(m(p2_simam_dw, "precision")), fmt(m(p2_simam_dw, "recall")), fmt(m(p2_simam_dw, "mAP50")), fmt(m(p2_simam_dw, "mAP50-95")), fmt(m(p2_simam_dw, "Params(M)"), 3), fmt(m(p2_simam_dw, "FPS"), 2)],
        ["p2_simam_shuffle", fmt(m(p2_simam_sh, "precision")), fmt(m(p2_simam_sh, "recall")), fmt(m(p2_simam_sh, "mAP50")), fmt(m(p2_simam_sh, "mAP50-95")), fmt(m(p2_simam_sh, "Params(M)"), 3), fmt(m(p2_simam_sh, "FPS"), 2)],
        ["p2_simam_dwconv_p075ghost", fmt(m(p2_simam_dw_p075g, "precision")), fmt(m(p2_simam_dw_p075g, "recall")), fmt(m(p2_simam_dw_p075g, "mAP50")), fmt(m(p2_simam_dw_p075g, "mAP50-95")), fmt(m(p2_simam_dw_p075g, "Params(M)"), 3), fmt(m(p2_simam_dw_p075g, "FPS"), 2)],
    ]

    lines: list[str] = []
    lines.append("# exp2 消融实验汇总")
    lines.append("")
    lines.append("说明：baseline 与 mbv3 为 exp1 正式训练结果复用，不在 exp2 重复训练。")
    lines.append("")
    lines.extend(md_table(["Model", "Precision", "Recall", "mAP50", "mAP50-95", "Params(M)", "FPS"], rows))
    lines.append("")

    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[DONE] report generated: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
