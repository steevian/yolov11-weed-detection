"""Phase 1: merge/split 3SeasonWeedDet10 for YOLO training.

Rules:
- data2021 + data2022 -> candidate pool, split 85:15 into train/val
- data2023 -> full test set
- broken image / missing XML / empty labels are skipped and logged
"""

from __future__ import annotations

import argparse
import random
import shutil
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET

from PIL import Image
from sklearn.model_selection import train_test_split


IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


@dataclass
class Sample:
    year: str
    stem: str
    image_path: Path
    xml_path: Path
    json_path: Path | None
    classes: list[str]

    @property
    def prefixed_stem(self) -> str:
        return f"{self.year}_{self.stem}"

    @property
    def primary_class(self) -> str:
        if not self.classes:
            return "__empty__"
        counts = Counter(self.classes)
        return sorted(counts.items(), key=lambda x: (-x[1], x[0]))[0][0]


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Merge/split 3SeasonWeedDet10 dataset")
    parser.add_argument("--repo-root", type=Path, default=repo_root)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--train-ratio", type=float, default=0.85)
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="For smoke test: cap max candidate samples from 2021+2022. 0 means full.",
    )
    parser.add_argument(
        "--limit-test",
        type=int,
        default=0,
        help="For smoke test: cap max samples copied from 2023 test set. 0 means full.",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--clean-output", action="store_true")
    return parser.parse_args()


def ensure_dirs(base: Path) -> None:
    for split in ("train", "val", "test"):
        (base / "images" / split).mkdir(parents=True, exist_ok=True)
        (base / "annotations" / split).mkdir(parents=True, exist_ok=True)
        (base / "json" / split).mkdir(parents=True, exist_ok=True)


def append_issue(log_file: Path, text: str) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as f:
        f.write(text.rstrip() + "\n")


def image_ok(path: Path) -> bool:
    try:
        with Image.open(path) as im:
            im.verify()
        return True
    except Exception:
        return False


def parse_classes_from_xml(xml_path: Path) -> list[str]:
    root = ET.parse(xml_path).getroot()
    classes: list[str] = []
    for obj in root.findall("object"):
        name = (obj.findtext("name") or "").strip()
        if name:
            classes.append(name)
    return classes


def collect_samples(src_dir: Path, year: str, issue_log: Path) -> list[Sample]:
    samples: list[Sample] = []
    for img_path in sorted(p for p in src_dir.iterdir() if p.is_file() and p.suffix.lower() in IMG_EXTS):
        stem = img_path.stem
        xml_path = src_dir / f"{stem}.xml"
        json_path = src_dir / f"{stem}.json"

        if not xml_path.exists():
            append_issue(issue_log, f"[MISSING_XML] {img_path}")
            continue

        if not image_ok(img_path):
            append_issue(issue_log, f"[BAD_IMAGE] {img_path}")
            continue

        try:
            classes = parse_classes_from_xml(xml_path)
        except Exception as exc:
            append_issue(issue_log, f"[XML_PARSE_FAIL] {xml_path} | {exc}")
            continue

        if not classes:
            append_issue(issue_log, f"[EMPTY_LABEL] {xml_path}")
            continue

        samples.append(
            Sample(
                year=year,
                stem=stem,
                image_path=img_path,
                xml_path=xml_path,
                json_path=json_path if json_path.exists() else None,
                classes=classes,
            )
        )
    return samples


def safe_train_val_split(
    samples: list[Sample], train_ratio: float, seed: int, issue_log: Path
) -> tuple[list[Sample], list[Sample]]:
    if len(samples) < 2:
        return samples, []

    labels = [s.primary_class for s in samples]
    unique_labels = set(labels)
    stratify_labels = labels if len(unique_labels) > 1 else None

    try:
        train_s, val_s = train_test_split(
            samples,
            train_size=train_ratio,
            random_state=seed,
            stratify=stratify_labels,
        )
        return list(train_s), list(val_s)
    except ValueError as exc:
        append_issue(issue_log, f"[SPLIT_FALLBACK_RANDOM] {exc}")
        rnd = random.Random(seed)
        shuffled = samples[:]
        rnd.shuffle(shuffled)
        cut = max(1, int(len(shuffled) * train_ratio))
        return shuffled[:cut], shuffled[cut:]


def copy_group(samples: Iterable[Sample], split: str, output_root: Path, dry_run: bool = False) -> int:
    copied = 0
    for s in samples:
        dst_stem = s.prefixed_stem
        img_dst = output_root / "images" / split / f"{dst_stem}{s.image_path.suffix.lower()}"
        xml_dst = output_root / "annotations" / split / f"{dst_stem}.xml"
        json_dst = output_root / "json" / split / f"{dst_stem}.json"

        if not dry_run:
            shutil.copy2(s.image_path, img_dst)
            shutil.copy2(s.xml_path, xml_dst)
            if s.json_path and s.json_path.exists():
                shutil.copy2(s.json_path, json_dst)
        copied += 1
    return copied


def clear_output(output_root: Path) -> None:
    for child in (output_root / "images", output_root / "annotations", output_root / "json"):
        if child.exists():
            shutil.rmtree(child)


def main() -> int:
    args = parse_args()
    random.seed(args.seed)

    repo_root = args.repo_root.resolve()
    src_base = repo_root / "data" / "3SeasonWeedDet10"
    data2021 = src_base / "data2021"
    data2022 = src_base / "data2022"
    data2023 = src_base / "data2023"
    output_root = repo_root / "datasets" / "processed_3seasonweeddet10"
    issue_log = repo_root / "experiments" / "logs" / "data_issues.log"

    for p in (data2021, data2022, data2023):
        if not p.exists():
            print(f"[ERROR] Missing source directory: {p}")
            return 1

    if args.clean_output and output_root.exists() and not args.dry_run:
        clear_output(output_root)

    ensure_dirs(output_root)
    if issue_log.exists():
        issue_log.unlink()

    samples_2021 = collect_samples(data2021, "2021", issue_log)
    samples_2022 = collect_samples(data2022, "2022", issue_log)
    samples_2023 = collect_samples(data2023, "2023", issue_log)

    train_val_pool = samples_2021 + samples_2022
    if args.limit > 0:
        train_val_pool = train_val_pool[: args.limit]

    train_samples, val_samples = safe_train_val_split(
        train_val_pool, train_ratio=args.train_ratio, seed=args.seed, issue_log=issue_log
    )
    test_samples = samples_2023
    if args.limit_test > 0:
        test_samples = test_samples[: args.limit_test]

    n_train = copy_group(train_samples, "train", output_root, dry_run=args.dry_run)
    n_val = copy_group(val_samples, "val", output_root, dry_run=args.dry_run)
    n_test = copy_group(test_samples, "test", output_root, dry_run=args.dry_run)

    print("[DONE] phase1_merge_split")
    print(f"train: {n_train}")
    print(f"val:   {n_val}")
    print(f"test:  {n_test}")
    print(f"issues log: {issue_log}")
    print(f"output root: {output_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
