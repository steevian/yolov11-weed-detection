# ECA旧版 vs ECA2新版（Smoke50）

| model | recall | map50 | fps | params | flops |
| --- | --- | --- | --- | --- | --- |
| YOLOv11-S-MBV3-ECA-old-smoke50 | 0.2974 | 0.2501 | 43.95 | 9312087 | 11506435416 |
| YOLOv11-S-MBV3-ECA2-new-smoke50 | 0.2868 | 0.3297 | 42.96 | 7464841 | 6730181464 |

## 差值（新版-旧版）
- Recall: -0.0106
- mAP50: 0.0796
- FPS: -0.99
- Params: -1847246
- FLOPs: -4776253952

## 结论模板
- 新版ECA2仅在P3/P4/P5放置3个ECA，维持主干与通道预算一致。
- 相比旧版ECA（Neck/PAN多处插入），新版在轻量性上更符合设计目标。
