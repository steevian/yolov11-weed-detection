#!/usr/bin/env python3
# exp1/eval_best_sp4eca.py
from pathlib import Path
import sys, time, json

REPO_ROOT = Path(__file__).resolve().parents[1]
CUSTOM_UL_ROOT = REPO_ROOT / "training" / "ultralytics_custom"
sys.path.insert(0, str(CUSTOM_UL_ROOT))
sys.path.insert(0, str(REPO_ROOT))

from ultralytics import YOLO
import numpy as np

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

model_name = "mbv3_sp4eca"
weights = (REPO_ROOT / "exp1" / "runs" / model_name / "weights" / "best.pt").resolve()
data_yaml = (REPO_ROOT / "exp1" / "dataset" / "data.yaml").resolve()
out_dir = REPO_ROOT / "exp1" / "eval"
out_dir.mkdir(parents=True, exist_ok=True)
out_json = out_dir / f"{model_name}_test_results.json"

print(f"Evaluate weights: {weights}")
print(f"Using data yaml: {data_yaml}")

evaluator = YOLO(str(weights))
t0 = time.time()
val_res = evaluator.val(
    data=str(data_yaml),
    split="test",
    imgsz=640,
    batch=1,
    workers=0,
    iou=0.7,
    max_det=300,
    verbose=False,
)
duration = time.time() - t0

metrics = {
    "precision": extract_metric(val_res, "mp"),
    "recall": extract_metric(val_res, "mr"),
    "mAP50": extract_metric(val_res, "map50"),
    "mAP50-95": extract_metric(val_res, "map"),
}

payload = {
    "model": model_name,
    "weights": str(weights),
    "data": str(data_yaml),
    "metrics": metrics,
    "runtime_seconds": safe_float(duration),
}

with out_json.open("w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

print("Done. Saved:", out_json)
print(json.dumps(payload, ensure_ascii=False, indent=2))