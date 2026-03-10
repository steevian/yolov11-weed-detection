"""Phase 1: convert VOC XML annotations to YOLO labels with resumable behavior."""

from __future__ import annotations

import argparse
import csv
import sys
import xml.etree.ElementTree as ET
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

def normalize_class_name(name: str) -> str:
    # Canonicalize VOC names: ignore spaces/underscores/case differences.
    return "".join(ch for ch in name.lower() if ch.isalnum())


NORMALIZED_CLASS_TO_ID = {
    normalize_class_name(name): idx for idx, name in enumerate(CLASS_NAMES)
}


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="VOC XML -> YOLO txt converter")
    parser.add_argument("--repo-root", type=Path, default=repo_root)
    parser.add_argument("--force", action="store_true", help="Force reconvert existing labels")
    return parser.parse_args()


def valid_yolo_label(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        lines = [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
        for line in lines:
            parts = line.split()
            if len(parts) != 5:
                return False
            int(parts[0])
            for p in parts[1:]:
                float(p)
        return True
    except Exception:
        return False


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def convert_xml_to_lines(xml_path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    lines: list[str] = []

    root = ET.parse(xml_path).getroot()
    width = int(root.findtext("size/width", default="0"))
    height = int(root.findtext("size/height", default="0"))

    if width <= 0 or height <= 0:
        errors.append("invalid_image_size")
        return lines, errors

    objects = root.findall("object")
    if not objects:
        errors.append("empty_objects")
        return lines, errors

    for obj in objects:
        raw_name = (obj.findtext("name") or "").strip()
        key = normalize_class_name(raw_name)
        if key not in NORMALIZED_CLASS_TO_ID:
            errors.append(f"unknown_class:{raw_name}")
            continue

        b = obj.find("bndbox")
        if b is None:
            errors.append(f"missing_bndbox:{raw_name}")
            continue

        try:
            xmin = float(b.findtext("xmin", default="0"))
            ymin = float(b.findtext("ymin", default="0"))
            xmax = float(b.findtext("xmax", default="0"))
            ymax = float(b.findtext("ymax", default="0"))
        except ValueError:
            errors.append(f"invalid_bbox_number:{raw_name}")
            continue

        xmin = clamp(xmin, 0, width)
        xmax = clamp(xmax, 0, width)
        ymin = clamp(ymin, 0, height)
        ymax = clamp(ymax, 0, height)

        bw = xmax - xmin
        bh = ymax - ymin
        if bw <= 1 or bh <= 1:
            errors.append(f"invalid_bbox_range:{raw_name}")
            continue

        x_center = (xmin + xmax) / 2.0 / width
        y_center = (ymin + ymax) / 2.0 / height
        w_norm = bw / width
        h_norm = bh / height
        class_id = NORMALIZED_CLASS_TO_ID[key]

        lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}")

    return lines, errors


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    ds_root = repo_root / "datasets" / "processed_3seasonweeddet10"
    ann_root = ds_root / "annotations"
    labels_root = ds_root / "labels"
    logs_root = repo_root / "experiments" / "logs"
    logs_root.mkdir(parents=True, exist_ok=True)
    error_csv = logs_root / "xml_convert_errors.csv"

    if not ann_root.exists():
        print(f"[ERROR] Missing annotations root: {ann_root}")
        print("Run phase1_merge_split.py first.")
        return 1

    converted = 0
    skipped = 0
    failed = 0
    rows: list[list[str]] = [["split", "xml_path", "error"]]

    for split in ("train", "val", "test"):
        xml_dir = ann_root / split
        label_dir = labels_root / split
        label_dir.mkdir(parents=True, exist_ok=True)

        for xml_path in sorted(xml_dir.glob("*.xml")):
            label_path = label_dir / f"{xml_path.stem}.txt"
            if not args.force and valid_yolo_label(label_path):
                skipped += 1
                continue

            try:
                lines, errs = convert_xml_to_lines(xml_path)
            except Exception as exc:
                failed += 1
                rows.append([split, str(xml_path), f"xml_parse_exception:{exc}"])
                continue

            if not lines:
                failed += 1
                if errs:
                    for e in errs:
                        rows.append([split, str(xml_path), e])
                else:
                    rows.append([split, str(xml_path), "empty_after_filter"])
                continue

            label_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            converted += 1

            for e in errs:
                rows.append([split, str(xml_path), e])

    with error_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    classes_txt = ds_root / "classes.txt"
    classes_txt.write_text("\n".join(CLASS_NAMES) + "\n", encoding="utf-8")

    print("[DONE] phase1_voc_to_yolo")
    print(f"converted: {converted}")
    print(f"skipped_existing: {skipped}")
    print(f"failed: {failed}")
    print(f"classes.txt: {classes_txt}")
    print(f"error csv: {error_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
