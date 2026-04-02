# exp2 消融实验执行计划（2026-03-31）

## 0. 目标与约束
- 目标：在毕业设计主线下，基于 `mbv3` 扩展 P2 与 Neck 轻量化，验证 Recall 补偿与参数压缩的平衡。
- 复用约束：`baseline` 与 `mbv3` 的正式训练结果已在 `exp1` 完成，exp2 不重复训练两者。
- 压缩原则：尽可能减少新训练模型数量，仅保留必要对照。

## 1. 实验分组（B 组压缩版）
- 参考组（直接复用 exp1 结果，不重训）：
  - `baseline` -> `exp1/eval/baseline_test_results.json`
  - `mbv3` -> `exp1/eval/mbv3_test_results.json`
- 新训练组（exp2 训练 4 组）：
  1. `p2_simam`
  2. `p2_simam_dwconv`
  3. `p2_simam_shuffle`
  4. `p2_simam_dwconv_p075ghost`

说明：为满足当前实验需求，`p075ghost` 已纳入正式消融并作为高压缩对照组。

## 2. 公平性协议（沿用 exp1）
- 数据：统一使用 `exp1/dataset/data.yaml`（data2021+data2022）。
- 训练参数：与 exp1 统一口径（epochs=200, batch=6, imgsz=640, SGD, seed=42）。
- 评估参数：`iou=0.7, max_det=300`。

## 3. 目录结构
- `exp2/configs/`：exp2 新模型 yaml。
- `exp2/models/`：新增模块（SimAM）。
- `exp2/train.py`：统一训练入口（仅新训练组）。
- `exp2/report.py`：合并 exp1 参考组 + exp2 新组，输出总表。
- `exp2/eval/`：exp2 新训练组评估 JSON。
- `exp2/reports/`：实验报告。
- `exp2/meta/`：运行清单与环境快照。

## 4. 执行顺序
1. 验证并复用 `exp1/dataset/data.yaml`。
2. 按顺序训练 `p2_simam`、`p2_simam_dwconv`、`p2_simam_shuffle`、`p2_simam_dwconv_p075ghost`。
3. 生成 `exp2/reports/exp2_report.md`，与 exp1 参考组汇总比较。

## 5. 验收标准
- `exp2` 成功复现 4 组新模型训练与评估。
- 汇总报告明确标注“baseline/mbv3 为 exp1 复用结果”。
- 全部文本文件 UTF-8，无乱码。
