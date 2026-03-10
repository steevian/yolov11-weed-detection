"""Phase 5: export 20 stratified visualization samples (2 per class)."""

from __future__ import annotations

import argparse
import random
from collections import defaultdict
from pathlib import Path

from ultralytics import YOLO


CLASS_NAMES = [
    "Carpetweed",
    "Eclipta",
    "Goosegrass",
    "Lambsquarters",
    "Morningglory",
    "Ragweed",
    "Palmer Amaranth",
    "Purslane",
    "Spotted spurge",
    "Waterhemp",
]


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Export stratified prediction samples")
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=repo_root / "datasets" / "processed_3seasonweeddet10",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--per-class", type=int, default=2)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=repo_root / "experiments" / "summary" / "samples",
    )
    return parser.parse_args()


def parse_primary_label(label_file: Path) -> int | None:
    if not label_file.exists():
        return None
    first = None
    with label_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            try:
                cid = int(parts[0])
            except Exception:
                continue
            first = cid
            break
    return first


def main() -> int:
    args = parse_args()
    random.seed(args.seed)

    test_img_dir = args.dataset_root / "images" / "test"
    test_lbl_dir = args.dataset_root / "labels" / "test"
    args.out_dir.mkdir(parents=True, exist_ok=True)

    bucket: dict[int, list[Path]] = defaultdict(list)
    for img in sorted(test_img_dir.glob("*")):
        if img.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
            continue
        cid = parse_primary_label(test_lbl_dir / f"{img.stem}.txt")
        if cid is None or cid < 0 or cid >= len(CLASS_NAMES):
            continue
        bucket[cid].append(img)

    selected: list[tuple[int, Path]] = []
    for cid in range(len(CLASS_NAMES)):
        imgs = bucket.get(cid, [])
        random.shuffle(imgs)
        selected.extend((cid, p) for p in imgs[: args.per_class])

    model = YOLO(str(args.weights))
    for cid, img_path in selected:
        results = model.predict(source=str(img_path), imgsz=args.imgsz, conf=0.25, verbose=False)
        if not results:
            continue
        plotted = results[0].plot()
        out_name = f"class{cid}_{CLASS_NAMES[cid].replace(' ', '_')}_{img_path.name}"
        out_path = args.out_dir / out_name
        import cv2

        cv2.imwrite(str(out_path), plotted)

    print("[DONE] phase5_export_samples")
    print(f"out_dir: {args.out_dir}")
    print(f"exported: {len(selected)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
