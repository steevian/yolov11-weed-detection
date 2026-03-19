# Comparison Metrics

统一测试协议：test(2023), batch=1, warmup=10, iters=100, imgsz=640。

| model | weights | precision | recall | map50 | map50_95 | fps | params | flops |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| YOLOv11-S | experiments\YOLOv11-S\baseline_full200_fresh_20260313_195344\weights\best.pt | 0.357033602365424 | 0.2657067907581703 | 0.2154826671572794 | 0.1911393797536753 | 56.28154686336004 | 9416670.0 | 10660633600.0 |
| YOLOv11-S-MBV3 | experiments\YOLOv11-S-MBV3\mbv3_full200_fresh_20260315_234917\weights\best.pt | 0.3961862643541259 | 0.2971305447806401 | 0.2406302569804834 | 0.2151046958846255 | 44.21532847257725 | 7464830.0 | 6728743256.0 |
| YOLOv11-S-MBV3-ECA | experiments\YOLOv11-S-MBV3-ECA\mbv3_eca_20260317_114514\weights\best.pt | 0.3887608091237516 | 0.2974440400876098 | 0.25013522010955 | 0.2238181020034545 | 43.34962368772759 | 9312087.0 | 11506435416.0 |
