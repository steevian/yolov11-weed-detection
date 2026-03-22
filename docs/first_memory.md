# 项目基础记忆（memory）


## 19. ECA2三点式修订训练与对比验证（2026-03-19）
- 2026-03-20 11:33:46 | run_id=mbv3_eca2_smoke50_20260319_184000 | status=completed
- 中断恢复结果：successful_resume_from_last_pt
- 最终训练方案：smoke50_eval_only
- 目标总轮次：50
- 改进内容：将旧版ECA从Backbone+Neck/PAN多点插入，修订为仅在P3/P4/P5后各插1个ECA（共3个）。
- 结构修改细节：不修改MobileNetV3主干结构、通道数和缩放系数；仅调整ECA插入位置，且不在Neck/PAN插入注意力。
- 关键结果（test协议）：
  - 旧ECA: recall=0.2974, map50=0.2501, fps=43.95, params=9312087, flops=11506435416
  - 新ECA2: recall=0.2868, map50=0.3297, fps=42.96, params=7464841, flops=6730181464
- 对比结论：
  - 轻量效率：新版相对旧版参数差值=-1847246，FLOPs差值=-4776253952。
  - 精度与召回：新版相对旧版 mAP50差值=0.0796，Recall差值=-0.0106。
  - 推理速度：新版相对旧版 FPS差值=-0.99。

## 20. ECA2早停公平性与四模型正式评测（2026-03-22）
- 2026-03-22 18:10:28 | run_id=mbv3_eca2_smoke50_20260319_184000 | status=completed
- 公平性结论：公平（Fair）。
- 判定依据：四模型核心训练口径一致（data、imgsz、batch、optimizer、增强、seed、patience=50）；ECA2在epoch=197因连续50轮未提升触发早停，属于统一训练规则下的自然停止，不构成额外优势。
- ECA2训练关键信息：best_epoch=147（val mAP50-95=0.89133），final_epoch=197（早停）。
- 四模型最佳权重统一test评测（batch=1, workers=0, imgsz=640）：
  - YOLOv11-S：P=0.3570, R=0.2657, mAP50=0.2155, mAP50-95=0.1911, FPS=57.35, Params=9416670, FLOPs=10660633600
  - YOLOv11-S-MBV3：P=0.3962, R=0.2971, mAP50=0.2406, mAP50-95=0.2151, FPS=47.65, Params=7464830, FLOPs=6728743256
  - YOLOv11-S-MBV3-ECA：P=0.3888, R=0.2974, mAP50=0.2501, mAP50-95=0.2238, FPS=39.48, Params=9312087, FLOPs=11506435416
  - YOLOv11-S-MBV3-ECA2：P=0.4181, R=0.2835, mAP50=0.3450, mAP50-95=0.3229, FPS=45.27, Params=7464841, FLOPs=6730181464
- ECA2相对旧ECA（test）：ΔP=+0.0293, ΔR=-0.0139, ΔmAP50=+0.0949, ΔmAP50-95=+0.0990, ΔFPS=+5.78, ΔParams=-1847246, ΔFLOPs=-4776253952。
- 综合结论：ECA2在精度与轻量效率上均显著优于旧ECA，且优于其余三模型的mAP50/mAP50-95；建议论文主结果采用该次四模型统一评测表。
- 产物路径：
  - experiments/summary/full200_validation_20260322/comparison_metrics_full200_4models.csv
  - experiments/summary/full200_validation_20260322/comparison_metrics_full200_4models.md
