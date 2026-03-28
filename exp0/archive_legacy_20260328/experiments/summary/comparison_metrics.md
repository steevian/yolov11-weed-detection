# Comparison Metrics

统一测试协议：test(2023), batch=1, warmup=10, iters=100, imgsz=640。

| model | weights | precision | recall | map50 | map50_95 | fps | params | flops |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| YOLOv11-S | D:\cyd\Desktop\yolo_web-main\experiments\YOLOv11-S\baseline_20260310_141013\weights\best.pt | 0.0213271512338161 | 0.0409774436090225 | 0.0035885746246389 | 0.0024555421356294 | 8.151415277663423 | 9416670.0 | 10660633600.0 |
| YOLOv11-S-MBV3 | D:\cyd\Desktop\yolo_web-main\experiments\YOLOv11-S-MBV3\mbv3_20260310_155214\weights\best.pt | 0.2739338952052502 | 0.0214285714285714 | 0.0049467896231029 | 0.002036918643872 | 9.434661052104872 | 7464830.0 | 6728743256.0 |
| YOLOv11-S-MBV3-ECA | D:\cyd\Desktop\yolo_web-main\experiments\YOLOv11-S-MBV3-ECA\mbv3_eca_20260310_175456\weights\best.pt | 0.0249854325044851 | 0.0240601503759398 | 0.0043230282516799 | 0.0020984278090789 | 6.56658503767093 | 9312087.0 | 11506435416.0 |
