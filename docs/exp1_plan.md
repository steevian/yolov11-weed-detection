# exp1 毕设实验执行计划（2026-03-26）

## 0. 目标与边界
- 目标：按导师新方案完成可复现实验链路，输出全部沉淀到 `D:/cyd/Desktop/yolo_web-main/exp1/`。
- 边界：仅使用 `data2021 + data2022`，不使用 2023。
- 公平性：三模型除结构差异外，训练与评估超参数、数据划分、随机种子保持一致。

## 1. 环境一致性核验
- 固定软件与硬件口径（Python 3.11.3, ultralytics 8.4.7, torch 2.9.1, RTX 3060 Laptop 6GB, Windows 11）。
- 固定随机性：
  - `seed: 42`
  - `deterministic: true`
  - `cudnn_benchmark: false`
  - `python_hash_seed: 42`
- 生成环境快照文件到 `exp1/meta/environment_snapshot.json`。

## 2. 数据准备（prepare_dataset.py）
- 输入：`data/3SeasonWeedDet10/data2021`、`data/3SeasonWeedDet10/data2022`。
- 执行：
  1) 汇总图片+XML索引。
  2) XML 转 YOLO txt，输出 `classes.txt`（10类，ID 0~9，官方顺序）。
  3) 按 7:1.5:1.5 分层随机划分 train/val/test（seed=42）。
  4) 生成 `exp1/dataset/data.yaml`（绝对路径）。
- 输出：
  - `exp1/dataset/images/{train,val,test}`
  - `exp1/dataset/labels/{train,val,test}`
  - `exp1/dataset/classes.txt`
  - `exp1/dataset/data.yaml`
  - `exp1/dataset/split_stats.json`
  - `exp1/logs/prepare_dataset.log`

## 3. 模型与配置
- Baseline：`exp1/configs/yolov11s.yaml`（引用官方 YOLOv11-S 结构）。
- MBV3：`exp1/configs/yolov11s_mbv3.yaml`（对齐历史全量 mbv3 改造）。
- ECA：`exp1/configs/yolov11s_mbv3_eca.yaml`（仅在 P3/P4/P5 后各插入 1 个 ECA）。
- 代码：
  - `exp1/models/mobilenetv3_backbone.py`
  - `exp1/models/eca.py`
- 说明：Neck 与 Detect 保持 YOLOv11-S 结构不变。

## 4. 统一训练参数与评估参数
- 训练固定参数（200轮）：
  - `epochs=200, batch=6, imgsz=640, optimizer=SGD, lr0=0.01, lrf=0.01`
  - `momentum=0.937, weight_decay=0.0005`
  - `warmup_epochs=3.0, warmup_momentum=0.8, warmup_bias_lr=0.1`
  - `patience=50, device=0, workers=1`
- 增强固定参数：
  - `hsv_h=0.015, hsv_s=0.7, hsv_v=0.4, degrees=8.0, translate=0.1, scale=0.2`
  - `shear=0.0, perspective=0.0, flipud=0.1, fliplr=0.5, mosaic=1.0`
  - `mixup=0.0, copy_paste=0.0, auto_augment=randaugment, erasing=0.4, close_mosaic=10`
- 评估固定参数：`iou=0.7, max_det=300`。

## 5. 核心脚本（train.py）
- 参数：`--model baseline|mbv3|eca`。
- 功能：
  1) 自动映射并加载模型 yaml。
  2) 使用统一参数训练200轮。
  3) 支持断点续训与抗打断（优先恢复 last.pt）。
  4) 训练结束自动用 best.pt 在测试集评估。
  5) 输出：
     - `exp1/runs/{model}/results.csv`
     - `exp1/eval/{model}_test_results.json`
  6) 指标字段完整：precision, recall, mAP50, mAP50-95, Params(M), FLOPs(G), FPS。
  7) 额外论文数据：训练参数、数据摘要、环境摘要、耗时、权重路径、评估原始摘要。

## 6. 扩充实验（expand.py，可选）
- 仅基于 ECA 模型（本方案中使用 eca 对应最终模型）。
- 对比组：
  1) 划分比例：7:1:2 / 6:2:2 / 5:2:3
  2) 样本量：100% / 70% / 50%
  3) 学习率：0.001 / 0.005 / 0.01（可100轮快速验证）
- 输出：`exp1/expand/*.csv`。

## 7. 汇总脚本（report.py）
- 自动读取 `exp1/eval` 与 `exp1/expand`。
- 生成：
  - 消融实验表（baseline, mbv3, eca）
  - 扩充实验表
  - 轻量化指标表
- 输出：`exp1/reports/exp1_report.md`。

## 8. 执行顺序（按你的要求）
1. 先落地本计划文件 `docs/exp1_plan.md`。
2. 立即开发并落地到阶段五所需文件。
3. 完成后立刻启动 baseline 全量训练（200轮）并进入日志监控。

## 9. 验收条件
- 所有新产物位于 `exp1/`（脚本可放 `exp1/scripts`）。
- 三模型可在同一套参数和数据下复现训练。
- baseline 训练已启动，日志持续更新。
- `exp1/eval`、`exp1/reports` 可生成论文直接可用数据。
