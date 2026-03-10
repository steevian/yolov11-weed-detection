"""Phase 0 helper: copy installed ultralytics package to training/ultralytics_custom."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Prepare local ultralytics working copy")
    parser.add_argument("--repo-root", type=Path, default=repo_root)
    parser.add_argument("--force", action="store_true", help="Overwrite existing copy")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()

    try:
        import ultralytics  # type: ignore
    except Exception as exc:
        print(f"[ERROR] Cannot import ultralytics: {exc}")
        return 1

    src = Path(ultralytics.__file__).resolve().parent
    dst = repo_root / "training" / "ultralytics_custom" / "ultralytics"
    dst.parent.mkdir(parents=True, exist_ok=True)

    if dst.exists():
        if not args.force:
            print(f"[SKIP] Destination already exists: {dst}")
            print("Use --force to refresh copy.")
            return 0
        shutil.rmtree(dst)

    shutil.copytree(src, dst)
    print("[DONE] phase0_prepare_ultralytics_custom")
    print(f"source: {src}")
    print(f"target: {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
