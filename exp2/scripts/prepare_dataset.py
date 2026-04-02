#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""exp2 dataset contract checker.

exp2 does not rebuild dataset; it reuses exp1 dataset to keep fairness.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Validate and reuse exp1 dataset for exp2")
    parser.add_argument("--data-yaml", type=Path, default=repo_root / "exp1" / "dataset" / "data.yaml")
    parser.add_argument("--out-json", type=Path, default=repo_root / "exp2" / "meta" / "dataset_contract.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.data_yaml.exists():
        print(f"[ERROR] Missing dataset yaml: {args.data_yaml}")
        return 1

    text = args.data_yaml.read_text(encoding="utf-8")
    payload = {
        "policy": "reuse-exp1-dataset",
        "data_yaml": str(args.data_yaml.resolve()),
        "note": "中文注释：exp2 直接复用 exp1 数据集，保证对比实验口径一致。",
        "preview": text.splitlines()[:20],
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[DONE] dataset contract saved: {args.out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
