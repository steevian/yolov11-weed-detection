#!/usr/bin/env python3
# exp1/test2.py
from pathlib import Path
import sys
import time
import json

REPO_ROOT = Path(__file__).resolve().parents[1]
CUSTOM_UL_ROOT = REPO_ROOT / "training" / "ultralytics_custom"
sys.path.insert(0, str(CUSTOM_UL_ROOT))
sys.path.insert(0, str(REPO_ROOT))

from ultralytics import YOLO
from ultralytics.utils.torch_utils import get_num_params, get_flops, unwrap_model
import numpy as np

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def safe_float(x):
    try:
        x = float(x)
        if np.isnan(x) or np.isinf(x):
            return None
        return x
    except Exception:
        return None


def extract_metric(metric_obj, key):
    box = getattr(metric_obj, "box", None)
    if box is None:
        return None
    value = getattr(box, key, None)
    if value is None:
        return None
    if isinstance(value, (list, tuple, np.ndarray)):
        if len(value) == 0:
            return None
        return safe_float(np.mean(value))
    return safe_float(value)


def count_images_in_path(p: Path) -> int:
    if not p.exists():
        return 0
    if p.is_file():
        try:
            return sum(1 for l in p.read_text(encoding="utf-8").splitlines() if l.strip())
        except Exception:
            return 0
    # directory
    return sum(1 for f in p.rglob("*") if f.suffix.lower() in IMG_EXTS)


def main() -> int:
    print("请输入模型路径")
    weights = input().strip()
    if not weights:
        print("未输入模型路径，退出")
        return 1

    weights_path = Path(weights)
    if not weights_path.exists():
        print(f"模型文件不存在: {weights_path}")
        return 2

    data_yaml = (REPO_ROOT / "exp1" / "dataset" / "data.yaml").resolve()
    if not data_yaml.exists():
        print(f"未找到 data.yaml: {data_yaml}")
        return 3

    model_name = weights_path.stem
    out_dir = REPO_ROOT / "exp1" / "eval"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / f"{model_name}_test_results.json"

    print(f"Evaluate weights: {weights_path}")
    print(f"Using data yaml: {data_yaml}")

    evaluator = YOLO(str(weights_path))
    imgsz = 640
    batch = 1

    t0 = time.time()
    try:
        val_res = evaluator.val(
            data=str(data_yaml),
            split="test",
            imgsz=imgsz,
            batch=batch,
            workers=0,
            iou=0.7,
            device="cpu",
            verbose=False,
        )
    except Exception as e:
        print("评估出错:", e)
        return 4
    duration = time.time() - t0

    metrics = {
        "precision": extract_metric(val_res, "mp"),
        "recall": extract_metric(val_res, "mr"),
        "mAP50": extract_metric(val_res, "map50"),
        "mAP50-95": extract_metric(val_res, "map"),
    }

    # FPS: prefer validator speed inference (ms/image), fallback to images/duration
    fps = None
    try:
        speed = getattr(val_res, "speed", None)
        inf_ms = None
        if isinstance(speed, dict):
            inf_ms = speed.get("inference")
        if inf_ms and inf_ms > 0:
            fps = safe_float(1000.0 / inf_ms)
        else:
            # fallback count images from data.yaml test path
            try:
                import yaml

                data = yaml.safe_load(data_yaml.read_text(encoding="utf-8"))
                test_path = data.get("test")
            except Exception:
                test_path = None
            n_images = 0
            if test_path:
                n_images = count_images_in_path(Path(test_path))
            if n_images > 0 and duration > 0:
                fps = safe_float(n_images / duration)
    except Exception:
        fps = None

    # Params(M) and FLOPs(G)
    params_m = None
    flops_g = None
    try:
        try:
            evaluator.fuse()
        except Exception:
            pass
        info = evaluator.info(imgsz=imgsz)  # returns (layers, params, grads, flops)
        if info:
            try:
                _, n_p, _, flops = info
                params_m = safe_float(n_p / 1e6)
                flops_g = safe_float(flops)
            except Exception:
                pass
        if params_m is None or flops_g is None:
            model_obj = getattr(evaluator, "model", None)
            if model_obj is not None:
                model_unwrapped = unwrap_model(model_obj)
                params_m = safe_float(get_num_params(model_unwrapped) / 1e6)
                flops_g = safe_float(get_flops(model_unwrapped, imgsz))
    except Exception:
        pass

    payload = {
        "model": model_name,
        "weights": str(weights_path.resolve()),
        "data": str(data_yaml.resolve()),
        "metrics": metrics,
        "FPS": safe_float(fps) if fps is not None else None,
        "FLOPs(G)": flops_g,
        "Params(M)": params_m,
        "runtime_seconds": safe_float(duration),
    }

    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Done. Saved:", out_json)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())