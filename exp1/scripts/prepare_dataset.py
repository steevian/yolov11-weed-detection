#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import random
import shutil
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


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
CLASS_TO_ID = {n: i for i, n in enumerate(CLASS_NAMES)}
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def _normalize_key(name: str) -> str:
    return "".join(ch.lower() for ch in name if ch.isalnum())


# Map common label aliases in XML to official class names.
ALIAS_TO_OFFICIAL: dict[str, str] = {
    _normalize_key("Carpetweed"): "Carpetweed",
    _normalize_key("Eclipta"): "Eclipta",
    _normalize_key("Goosegrass"): "Goosegrass",
    _normalize_key("Lambsquarters"): "Lambsquarters",
    _normalize_key("Morningglory"): "Morningglory",
    _normalize_key("MorningGlory"): "Morningglory",
    _normalize_key("Ragweed"): "Ragweed",
    _normalize_key("Palmer Amaranth"): "Palmer Amaranth",
    _normalize_key("PalmerAmaranth"): "Palmer Amaranth",
    _normalize_key("Purslane"): "Purslane",
    _normalize_key("Spotted spurge"): "Spotted spurge",
    _normalize_key("SpottedSpurge"): "Spotted spurge",
    _normalize_key("Waterhemp"): "Waterhemp",
}


@dataclass
class Sample:
    image_path: Path
    xml_path: Path
    width: int
    height: int
    yolo_lines: list[str]
    dominant_class: int


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Prepare exp1 dataset from 2021+2022 only")
    parser.add_argument(
        "--source-root",
        type=Path,
        default=repo_root / "data" / "3SeasonWeedDet10",
        help="Root containing data2021 and data2022",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=repo_root / "exp1" / "dataset",
        help="Output dataset root",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--train-ratio", type=float, default=0.70)
    parser.add_argument("--val-ratio", type=float, default=0.15)
    parser.add_argument("--test-ratio", type=float, default=0.15)
    parser.add_argument("--copy-mode", choices=["copy", "hardlink"], default="copy")
    parser.add_argument("--clean", action="store_true", help="Delete output-root before processing")
    return parser.parse_args()


def find_pairs(season_dir: Path) -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []
    for img in season_dir.rglob("*"):
        if not img.is_file() or img.suffix.lower() not in IMG_EXTS:
            continue
        xml = img.with_suffix(".xml")
        if xml.exists():
            pairs.append((img, xml))
    return pairs


def clip(v: float, low: float, high: float) -> float:
    return max(low, min(high, v))


def to_yolo_line(cls_id: int, x1: float, y1: float, x2: float, y2: float, w: int, h: int) -> str:
    bw = clip((x2 - x1) / w, 0.0, 1.0)
    bh = clip((y2 - y1) / h, 0.0, 1.0)
    cx = clip((x1 + x2) / (2.0 * w), 0.0, 1.0)
    cy = clip((y1 + y2) / (2.0 * h), 0.0, 1.0)
    return f"{cls_id} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}"


def parse_xml_to_sample(image_path: Path, xml_path: Path) -> Sample | None:
    try:
        root = ET.parse(xml_path).getroot()
    except Exception:
        return None

    size = root.find("size")
    if size is None:
        return None

    try:
        width = int(float(size.findtext("width", default="0")))
        height = int(float(size.findtext("height", default="0")))
    except Exception:
        return None

    if width <= 1 or height <= 1:
        return None

    class_count = defaultdict(int)
    yolo_lines: list[str] = []

    for obj in root.findall("object"):
        raw_name = (obj.findtext("name", default="")).strip()
        norm_name = _normalize_key(raw_name)
        official_name = ALIAS_TO_OFFICIAL.get(norm_name)
        if official_name is None:
            continue
        bnd = obj.find("bndbox")
        if bnd is None:
            continue
        try:
            x1 = float(bnd.findtext("xmin", default="0"))
            y1 = float(bnd.findtext("ymin", default="0"))
            x2 = float(bnd.findtext("xmax", default="0"))
            y2 = float(bnd.findtext("ymax", default="0"))
        except Exception:
            continue

        if x2 <= x1 or y2 <= y1:
            continue

        cls_id = CLASS_TO_ID[official_name]
        yolo_lines.append(to_yolo_line(cls_id, x1, y1, x2, y2, width, height))
        class_count[cls_id] += 1

    if not yolo_lines:
        return None

    dominant_class = sorted(class_count.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    return Sample(
        image_path=image_path,
        xml_path=xml_path,
        width=width,
        height=height,
        yolo_lines=yolo_lines,
        dominant_class=dominant_class,
    )


def split_stratified(samples: list[Sample], seed: int, train_ratio: float, val_ratio: float, test_ratio: float) -> dict[str, list[Sample]]:
    if abs((train_ratio + val_ratio + test_ratio) - 1.0) > 1e-6:
        raise ValueError("train/val/test ratio must sum to 1.0")

    grouped: dict[int, list[Sample]] = defaultdict(list)
    for s in samples:
        grouped[s.dominant_class].append(s)

    rng = random.Random(seed)
    out = {"train": [], "val": [], "test": []}

    for _, group in grouped.items():
        rng.shuffle(group)
        n = len(group)
        n_train = int(round(n * train_ratio))
        n_val = int(round(n * val_ratio))
        n_test = n - n_train - n_val

        # Keep each class represented whenever possible.
        if n >= 3:
            n_train = max(1, n_train)
            n_val = max(1, n_val)
            n_test = max(1, n_test)
            while n_train + n_val + n_test > n:
                if n_train >= n_val and n_train >= n_test and n_train > 1:
                    n_train -= 1
                elif n_val >= n_test and n_val > 1:
                    n_val -= 1
                elif n_test > 1:
                    n_test -= 1
                else:
                    break
            while n_train + n_val + n_test < n:
                n_train += 1

        out["train"].extend(group[:n_train])
        out["val"].extend(group[n_train : n_train + n_val])
        out["test"].extend(group[n_train + n_val :])

    return out


def write_item(sample: Sample, split: str, output_root: Path, copy_mode: str) -> None:
    img_dir = output_root / "images" / split
    lab_dir = output_root / "labels" / split
    img_dir.mkdir(parents=True, exist_ok=True)
    lab_dir.mkdir(parents=True, exist_ok=True)

    dst_img = img_dir / sample.image_path.name
    dst_lab = lab_dir / f"{sample.image_path.stem}.txt"

    if copy_mode == "hardlink":
        if dst_img.exists():
            dst_img.unlink()
        dst_img.hardlink_to(sample.image_path)
    else:
        shutil.copy2(sample.image_path, dst_img)

    dst_lab.write_text("\n".join(sample.yolo_lines) + "\n", encoding="utf-8")


def write_data_yaml(output_root: Path) -> None:
    train = (output_root / "images" / "train").resolve().as_posix()
    val = (output_root / "images" / "val").resolve().as_posix()
    test = (output_root / "images" / "test").resolve().as_posix()
    lines = [
        f"path: {output_root.resolve().as_posix()}",
        f"train: {train}",
        f"val: {val}",
        f"test: {test}",
        "",
        f"nc: {len(CLASS_NAMES)}",
        "names:",
    ]
    for i, n in enumerate(CLASS_NAMES):
        lines.append(f"  {i}: '{n}'")
    (output_root / "data.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    random.seed(args.seed)

    if args.clean and args.output_root.exists():
        shutil.rmtree(args.output_root)
    args.output_root.mkdir(parents=True, exist_ok=True)

    seasons = [args.source_root / "data2021", args.source_root / "data2022"]
    for s in seasons:
        if not s.exists():
            raise FileNotFoundError(f"Season dir not found: {s}")

    all_pairs: list[tuple[Path, Path]] = []
    for s in seasons:
        all_pairs.extend(find_pairs(s))

    accepted: list[Sample] = []
    dropped = 0
    for img, xml in all_pairs:
        sample = parse_xml_to_sample(img, xml)
        if sample is None:
            dropped += 1
            continue
        accepted.append(sample)

    split = split_stratified(
        accepted,
        seed=args.seed,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
    )

    for subset, items in split.items():
        for item in items:
            write_item(item, subset, args.output_root, args.copy_mode)

    (args.output_root / "classes.txt").write_text("\n".join(CLASS_NAMES) + "\n", encoding="utf-8")
    write_data_yaml(args.output_root)

    stats = {
        "seed": args.seed,
        "source_root": str(args.source_root.resolve()),
        "output_root": str(args.output_root.resolve()),
        "ratios": {"train": args.train_ratio, "val": args.val_ratio, "test": args.test_ratio},
        "total_pairs": len(all_pairs),
        "accepted": len(accepted),
        "dropped": dropped,
        "split_sizes": {k: len(v) for k, v in split.items()},
        "split_class_counts": {
            k: dict(sorted(__class_counts(v).items())) for k, v in split.items()
        },
    }
    (args.output_root / "split_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    log_path = args.output_root.parent / "logs" / "prepare_dataset.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("[DONE] prepare_dataset")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


def __class_counts(items: list[Sample]) -> dict[int, int]:
    out: dict[int, int] = defaultdict(int)
    for s in items:
        out[s.dominant_class] += 1
    return out


if __name__ == "__main__":
    raise SystemExit(main())
