"""Register custom modules into training/ultralytics_custom working copy.

This script patches local Ultralytics package source only.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Register custom modules into local ultralytics copy")
    parser.add_argument("--repo-root", type=Path, default=repo_root)
    return parser.parse_args()


def replace_once(text: str, old: str, new: str, file_hint: str) -> str:
    if old not in text:
        raise RuntimeError(f"Patch anchor not found in {file_hint}: {old[:80]}...")
    return text.replace(old, new, 1)


def copy_custom_modules(repo_root: Path, ul_root: Path) -> None:
    src_models = repo_root / "training" / "models"
    dst_modules = ul_root / "ultralytics" / "nn" / "modules"
    dst_modules.mkdir(parents=True, exist_ok=True)

    (dst_modules / "eca.py").write_text((src_models / "eca.py").read_text(encoding="utf-8"), encoding="utf-8")
    (dst_modules / "mobilenetv3_backbone.py").write_text(
        (src_models / "mobilenetv3_backbone.py").read_text(encoding="utf-8"), encoding="utf-8"
    )


def patch_modules_init(ul_root: Path) -> None:
    path = ul_root / "ultralytics" / "nn" / "modules" / "__init__.py"
    text = path.read_text(encoding="utf-8")

    if "from .eca import ECA" not in text:
        text += "\nfrom .eca import ECA\n"
    if "from .mobilenetv3_backbone import MobileNetV3Backbone" not in text:
        text += "from .mobilenetv3_backbone import MobileNetV3Backbone\n"

    if '"ECA"' not in text:
        text = replace_once(text, '    "v10Detect",\n)', '    "v10Detect",\n    "ECA",\n    "MobileNetV3Backbone",\n)', str(path))

    path.write_text(text, encoding="utf-8")


def patch_tasks_import(ul_root: Path) -> None:
    path = ul_root / "ultralytics" / "nn" / "tasks.py"
    text = path.read_text(encoding="utf-8")

    if "ECA," not in text:
        text = replace_once(text, "    v10Detect,\n)", "    v10Detect,\n    ECA,\n    MobileNetV3Backbone,\n)", str(path))

    path.write_text(text, encoding="utf-8")


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    ul_root = repo_root / "training" / "ultralytics_custom"
    ul_pkg = ul_root / "ultralytics"
    if not ul_pkg.exists():
        print(f"[ERROR] Missing local ultralytics copy: {ul_pkg}")
        print("Run phase0_prepare_ultralytics_custom.py first.")
        return 1

    copy_custom_modules(repo_root, ul_root)
    patch_modules_init(ul_root)
    patch_tasks_import(ul_root)
    print("[DONE] phase3_register_custom_modules")
    print(f"ultralytics_root: {ul_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
