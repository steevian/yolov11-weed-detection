"""Phase 4 sanity check: forward pass + params/FLOPs estimate."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Sanity check model forward and complexity")
    parser.add_argument(
        "--model",
        type=Path,
        default=repo_root / "training" / "configs" / "yolo11s_mbv3_eca.yaml",
    )
    parser.add_argument(
        "--ultralytics-root",
        type=Path,
        default=repo_root / "training" / "ultralytics_custom",
    )
    parser.add_argument("--imgsz", type=int, default=640)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.ultralytics_root.exists() and str(args.ultralytics_root.resolve()) not in sys.path:
        sys.path.insert(0, str(args.ultralytics_root.resolve()))

    from ultralytics import YOLO  # type: ignore

    model = YOLO(str(args.model))
    x = torch.randn(1, 3, args.imgsz, args.imgsz)

    with torch.no_grad():
        out = model.model(x)

    params = sum(p.numel() for p in model.model.parameters())
    trainable = sum(p.numel() for p in model.model.parameters() if p.requires_grad)

    flops_text = "N/A"
    try:
        from thop import profile

        flops, _ = profile(model.model, inputs=(x,), verbose=False)
        flops_text = f"{flops:.2f}"
    except Exception as exc:
        flops_text = f"failed: {exc}"

    print("[DONE] phase4_sanity_check_forward")
    print(f"model: {args.model}")
    print(f"output_type: {type(out)}")
    print(f"params_total: {params}")
    print(f"params_trainable: {trainable}")
    print(f"flops: {flops_text}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
