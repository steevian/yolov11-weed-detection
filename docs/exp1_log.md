# exp1 执行日志与问题修复记录

## 2026-03-27 数据集异常与训练纯净性核验

### 1) 问题现象
- 训练时每轮 batch 数仅约 495（batch=6），与预期不符。
- 对应训练集样本约 2970，明显低于 data2021+data2022 全量规模。

### 2) 根因定位
- 已核验源数据目录与规模：
	- `data2021`: images=4704, xml=4704
	- `data2022`: images=1948, xml=1948
	- 合计 `6652`
- 异常原因不是目录错误，而是 `exp1/scripts/prepare_dataset.py` 的类别名匹配过严：
	- XML 中真实类别存在别名：`MorningGlory`、`PalmerAmaranth`、`SpottedSpurge`
	- 旧逻辑仅按固定写法匹配，导致大量样本被当作无效样本丢弃。

### 3) 修复动作
- 修复文件：`exp1/scripts/prepare_dataset.py`
- 修复内容：新增类别名归一化与别名映射（大小写/空格/驼峰统一到官方10类）。
- 重建数据集（`--clean`）：
	- total_pairs=6652
	- accepted=6652
	- dropped=0
	- split(train/val/test)=4656/997/999（7:1.5:1.5）

### 4) 上一轮错误训练是否有价值
- 结论：**无论文价值，不可用于正式实验对比**。
- 原因：训练基于错误过滤后的样本集（accepted=4242），不满足新方案“仅2021+2022且按正确类别映射”的数据口径。

### 5) 清理动作（已执行）
- 为避免污染与断点续训串扰，已停止 baseline 在跑进程并清理相关产物：
	- 删除目录：`exp1/runs/baseline`
	- 删除文件：`exp1/meta/baseline_run_manifest.json`
- 目录去重清理：
	- 删除重复配置：`exp1/configs/yolo11s.yaml`
	- 保留方案定义配置：`exp1/configs/yolov11s.yaml`

### 6) 计划执行核验（对照 docs/exp1_plan.md）
- 已完成：
	- 计划文件落地 `docs/exp1_plan.md`
	- `exp1/scripts/prepare_dataset.py`
	- `exp1/train.py`
	- `exp1/report.py`
	- `exp1/expand.py`
	- `exp1/models/eca.py`
	- `exp1/models/mobilenetv3_backbone.py`
	- `exp1/configs/yolov11s.yaml`
	- `exp1/configs/yolov11s_mbv3.yaml`
	- `exp1/configs/yolov11s_mbv3_eca.yaml`
- 进行中：
	- baseline 200轮全量训练（clean rerun）
- 待完成：
	- baseline 完训后自动 test 评估并输出 `exp1/eval/baseline_test_results.json`
	- mbv3、eca 的同口径训练与评估
	- `report.py` 汇总表生成

### 7) 当前训练纯净性核验
- 当前 baseline 已重新启动，且满足方案要求：
	- 解释器环境：`C:/Users/cyd/miniconda3/envs/weedweb_detection/python.exe`
	- 关键版本：Ultralytics 8.4.7, torch 2.9.1+cu128
	- GPU：RTX 3060 Laptop 可用
	- 训练参数：epochs=200, batch=6, imgsz=640, optimizer=SGD, seed=42, deterministic=true
	- 数据集：`exp1/dataset/data.yaml`（仅 data2021+data2022）
	- 训练集扫描：`4656 images`
- 纯净性判断：
	- 先停进程再删 `exp1/runs/baseline` 后重启，**未继承上一轮错误产物**。

### 8) 当前在跑任务
- baseline clean run 正在执行中（已通过 AMP 检查并完成 train/val cache 扫描）。

## 2026-03-31 三模型完训对比分析与下一步方案

### 1) 三模型综合对比（同口径）

数据来源：
- `exp1/eval/baseline_test_results.json`
- `exp1/eval/mbv3_test_results.json`
- `exp1/eval/eca_test_results.json`

关键指标汇总：

| Model | Precision | Recall | mAP50 | mAP50-95 | Params(M) | FPS |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 0.9190 | 0.9208 | 0.9587 | 0.8927 | 9.4167 | 66.16 |
| mbv3 | 0.9332 | 0.9101 | 0.9598 | 0.8916 | 7.4648 | 45.40 |
| eca | 0.9329 | 0.9148 | 0.9571 | 0.8830 | 7.4648 | 47.23 |

相对 baseline 的变化：
- `mbv3`
	- 精度导向：Precision +1.42 个百分点，mAP50 +0.11 个百分点
	- 防漏检能力：Recall -1.07 个百分点，mAP50-95 -0.11 个百分点
	- 轻量化：参数量 -20.72%
	- 实测速度：FPS -31.38%
- `eca`
	- Precision +1.39 个百分点
	- Recall -0.60 个百分点（比 mbv3 略回升）
	- mAP50 -0.16 个百分点，mAP50-95 -0.97 个百分点
	- 参数量与 mbv3 基本一致，FPS 比 mbv3 略高（+4.03%）

结论（当前这组实验）：
- 若目标是“综合精度上限 + 防漏检（Recall）”：`baseline` 仍是最稳健基线。
- 若目标是“参数量下降且 mAP50 基本持平”：`mbv3` 有价值，但当前实现下吞吐未占优。
- `eca` 在当前插入位置与训练设定下，未形成预期精度补偿，尤其 mAP50-95 下滑明显。

### 2) 为什么 mbv3 参数更小但实测比 baseline 慢

该现象在当前结果中明确存在（`66.16 FPS -> 45.40 FPS`），常见原因如下：

- 理论复杂度不等于真实延迟：
	- Params/FLOPs 只能近似表征计算量，不能直接代表 GPU 实测吞吐。
- MobileNetV3 的深度可分离卷积在部分 GPU/算子路径上利用率较低：
	- 更偏 memory-bound，算子碎片化后 kernel launch 开销更高。
- 当前 mbv3 图结构包含 `TorchVision + Index` 路径：
	- 相比 baseline 的主干实现，可能更难触发高效算子融合与调度优化。
- 测速定义是端到端推理（含预处理/后处理）：
	- mbv3 在 `val_speed_ms` 中推理耗时高于 baseline，也会直接反映到 FPS。

补充：
- 这不代表 mbv3 一定慢，只说明“在当前框架实现 + 当前部署路径”下更慢。
- 若切换到 TensorRT、ONNX Runtime 或做算子融合/静态图优化，排序可能发生变化。

### 3) 在保持 mbv3 轻量化前提下继续精度补偿的推荐

#### 3.1 先做高性价比改进（优先级从高到低）

1. 蒸馏（推荐优先）
- Teacher: baseline
- Student: mbv3
- 组合蒸馏：分类 logits + 回归分支 + 关键层特征蒸馏
- 预期：参数基本不变，通常可稳定提升 Recall 与 mAP50-95。

2. 注意力“减法设计”而非“加法堆叠”
- 当前 eca 在 P3/P4/P5 全插入，建议改为仅在一个层级插入（先试 P4）。
- 做小网格实验：`none / P4-only / P5-only`，避免多点注意力导致信息过抑制。

3. 针对漏检的训练策略
- 保持主干不变，微调损失与采样：
	- 提高困难样本采样比例（hard sample replay）
	- 轻度类别重加权（针对易漏检类）
	- 仅小幅调整增强强度，避免过强增强损伤细粒度判别

#### 3.2 建议的下一轮实验矩阵（保持论文可控）

- Group A（结构）：
	- A0: mbv3（当前）
	- A1: mbv3 + ECA(P4-only)
	- A2: mbv3 + ECA(P5-only)
- Group B（训练）：
	- B0: mbv3 + Distill(baseline->mbv3)
	- B1: A1 + Distill
- 全部保持同一训练合同：epochs=200, batch=6, imgsz=640, seed=42, eval(iou=0.7, max_det=300)

验收标准（建议）：
- 主目标：`mAP50-95` 相比当前 mbv3 至少 +0.3 个百分点
- 约束目标：参数量变化 <= 3%，FPS 不低于当前 mbv3 的 95%

### 4) 当前阶段可用于论文的客观表述（建议）

- 本轮实验表明，MobileNetV3 主干可显著降低参数量，但在当前实现路径下未带来更高实测推理速度。
- ECA 注意力在当前插入策略中未有效提升综合检测精度，提示轻量模型的精度补偿更依赖于模块位置与训练策略协同，而非单纯叠加注意力模块。
- 下一阶段将采用“结构最小增量 + 知识蒸馏”路线，重点提升 Recall 与 mAP50-95，同时严格约束模型规模与端侧吞吐。

## 2026-03-31 文献复盘与架构优化方案（非蒸馏路线）

### 1) 外部文献材料提炼（来自 `paper/lunwen/yuancailiao.docx`）

共性结论（跨多篇农业检测论文的一致经验）：
- 轻量化主干（MobileNet/PP-LCNet/Ghost）后，精度补偿通常要在 Neck/融合层完成，而不是只在 Backbone 做通道重标定。
- 注意力模块并非“越多越好”：多篇工作显示“少量、关键位置插入”优于全层堆叠。
- 小目标任务提升 Recall 的核心通常是“多尺度融合 + 小尺度检测分支（P2/高分辨率分支）”。
- 架构优化要配合部署路径评估：参数量下降不必然带来端到端 FPS 上升。

### 2) 对当前 MBV3/ECA 架构的全面分析

当前 `mbv3` 架构要点：
- Backbone 使用 `mobilenet_v3_large` 提取多尺度特征（`Index` 取 P3/P4/P5）。
- Neck 基本沿用标准 PAN/FPN 形式。

当前 `eca` 架构要点：
- 在 Backbone 投影后的三个尺度（P3/P4/P5）全部插入 ECA（纯通道注意力）。
- Neck 未增加新的多尺度补偿结构。

与实验结果结合的诊断：
- `mbv3` 相比 baseline：参数量显著下降，但 Recall 与 mAP50-95 略降，说明轻量化后细粒度判别和复杂场景鲁棒性被削弱。
- `eca` 相比 `mbv3`：Recall 有轻微回升，但 mAP50/mAP50-95 未获有效补偿，说明“Backbone 端全尺度 ECA”对该任务不是最佳补偿位置。
- 结构层面根因更可能在“多尺度融合不足 + 空间信息补偿不足”，而不是“通道建模不够”。

### 3) 最合理的下一版方案（仅架构，不做蒸馏）

方案名（建议）：`YOLOv11s-MBV3-BiFPNlite-SimAM-P2`

核心设计：
1. 保留 MBV3 主干（维持轻量化基本盘）。
2. 移除 Backbone 端全尺度 ECA（避免过度通道门控）。
3. 在 Neck 引入轻量双向融合（BiFPN-Lite 思路，采用可学习融合权重）。
4. 增加一个小目标检测分支 P2（160x160），优先补 Recall。
5. 在 Neck 的高分辨率融合输出（建议 P3 或 P3+P4）插入参数极小注意力（优先 SimAM 或 NAM，先单点插入）。

为何这是当前最合理方案：
- 与你的目标一致：不做蒸馏、继续走架构改进。
- 与文献共识一致：轻量化后在融合层补偿优于 Backbone 全层注意力堆叠。
- 与现有结果对症：当前短板主要在 Recall/mAP50-95，而 P2 + 融合优化是最直接的补偿路径。

### 4) 实施优先级与风险控制

为降低试错成本，建议按以下顺序做小步迭代：

Step A（最低风险）：
- `mbv3` 基础上仅做 “ECA 全移除 + Neck 单点 SimAM/NAM（P3）”。

Step B（主改进）：
- 在 Step A 的基础上加入 `P2` 检测头。

Step C（融合增强）：
- 将 PAN 融合替换为 BiFPN-Lite 融合（可学习权重，保持通道规模克制）。

推荐验收门槛：
- 主目标：`mAP50-95` 相比当前 `mbv3` 至少 +0.3 个百分点。
- 次目标：Recall 不低于 baseline -0.3 个百分点。
- 约束：Params 增幅 <= 8%，FPS 不低于当前 `mbv3` 的 90%。

### 5) 论文可写的阶段结论（非蒸馏路线）

- 本研究在轻量化主干基础上验证了“仅通道注意力（ECA）全尺度插入”对精度补偿的局限性。
- 后续改进将转向“融合层优先”的结构设计，以小目标检测分支和轻量多尺度融合作为主要补偿路径。
- 该路线兼顾可解释性与工程可落地性，更符合农业小目标检测场景下对 Recall、实时性和模型规模的三重约束。

### 6) 方案再评估（可行性/工作量/风险）

对候选改造项做了快速参数复核（当前运行时为 Ultralytics YOLO11 系列）：
- 现有 `mbv3` 参数量：`7,472,350`。
- 将 Head 中全部 `C3k2` 替换为 `C3Ghost` 后：`7,572,238`（+99,888，+1.34%）。
- 结论：在当前 YOLO11 `mbv3` 结构中，`C3k2 -> C3Ghost` 并不能控参，反而增参，不建议作为主路径。

模块可复用性（工程现实）：
- 现成可用：`GhostConv/C3Ghost/GhostBottleneck`（运行时已有）。
- 当前缺失：`SimAM/NAM/BiFPN`（需自行实现并接入解析）。

修正后的建议路径（更稳）：
1. 保留 `mbv3` 主干。
2. 去掉全尺度 ECA（先回归 `mbv3` 纯净结构）。
3. 先加 `P2` 检测头（优先补小目标 Recall）。
4. 仅做“单点轻量注意力”验证（建议先 SimAM，因零参数）。
5. BiFPN-Lite 放在第三步（作为增益项，而非首改项）。

为什么这条路径更优：
- 避免了“C3k2 替换误降参”的方向性错误；
- 把主要工作量集中在最可能带来 Recall 提升的 `P2`；
- 先用零参数注意力验证收益，再决定是否引入更复杂融合结构，试错成本更低。

## 2026-03-31 Neck 轻量化两轮实测补充与后续方案定稿

### 1) 本次补充的目标与边界

目标：在当前 `mbv3` 架构下，量化评估 Neck/Head 卷积轻量化改造的参数收益，并据此给出下一阶段“最稳妥且收益最高”的实验路径。

边界：本轮仅做“可构图 + 参数量”实测，不包含训练收敛、mAP/FPS 实测结论。

### 2) 两轮实测数据同步

基线配置：`exp1/configs/yolov11s_mbv3.yaml`（baseline 参数 `7,472,350`）。

第一轮（快速摸底，环境默认 ultralytics）：
- `head_conv_to_ghost`：`7,108,510`（`-4.87%`）
- `adapters_plus_head_conv_to_ghost`：`6,857,054`（`-8.23%`）
- `head_conv_to_shuffle`：`KeyError: 'ShuffleConv'`

第一轮结论：GhostConv 可直接评测；ShuffleConv 当时未注册，无法构图。

第二轮（完成 ShuffleConv 接入后，使用项目 `training/ultralytics_custom` 路径复测）：

| Variant | Params | Delta vs baseline |
|---|---:|---:|
| neck_slim_0p625_plus_shuffle | 4,621,638 | -38.15% |
| neck_slim_0p625_plus_ghost | 4,758,278 | -36.32% |
| neck_slim_0p625 | 5,056,438 | -32.33% |
| neck_slim_0p75_plus_shuffle | 5,171,406 | -30.79% |
| neck_slim_0p75_plus_ghost | 5,366,094 | -28.19% |
| neck_slim_0p75 | 5,758,446 | -22.94% |
| adapters_plus_head_conv_to_dw | 6,223,326 | -16.72% |
| adapters_plus_head_conv_to_shuffle | 6,515,550 | -12.80% |
| head_conv_to_dw | 6,738,526 | -9.82% |
| head_conv_to_shuffle | 6,777,758 | -9.30% |
| adapters_plus_head_conv_to_ghost | 6,857,054 | -8.23% |
| head_conv_to_ghost | 7,108,510 | -4.87% |

注：
- `head_conv_to_*`：仅替换 Head 两个下采样 `Conv(3x3,s2)`。
- `adapters_plus_head_conv_to_*`：替换 backbone 三个 adapter 卷积（索引 4/5/6）+ Head 两个下采样卷积。
- `neck_slim_0p75/0p625`：将 Neck/Head 主通道按比例缩放（并做 8 对齐）。

### 3) 与期刊材料 + 项目现状 + 对话讨论的综合判断

与文献共识一致点：
- 轻量化主干后，补偿与优化重点应转向 Neck 融合层，而不是仅在 Backbone 叠加通道注意力。
- 小目标 Recall 提升首选 `P2` 与多尺度融合补偿。

结合项目现状（当前短板是 Recall/mAP50-95，而非仅 Params）：
- 参数降幅“最大”的方案（`0.625 + shuffle/ghost`）并不等于综合最优，精度回撤风险高、调参与复现实验成本也最高。
- 在工程可控性上，`adapters_plus_head_conv_to_dw` 是当前“降参幅度/实现复杂度/风险”三者最均衡的 Neck 轻量化切入点。
- `BiFPN-Lite` 定位仍然明确：属于 Neck 融合重构，不是 Detect Head 结构本体改造。

### 4) 下一阶段最合理方案（定稿）

建议采用“三阶段、门控推进”路线：

Stage 1（低风险优先，先补 Recall）：
1. 以 `mbv3` 纯净结构为底座（去掉全尺度 ECA）。
2. 加 `P2` 检测头（先解决小目标漏检）。
3. Neck 单点注意力（优先 SimAM，零参数）只放一个位置（P3 或 P3+P4 二选一，不全插）。

Stage 2（参数优化主阶段）：
1. 在 Stage 1 最优子配置上，优先尝试 `adapters_plus_head_conv_to_dw`。
2. 备选对照：`adapters_plus_head_conv_to_shuffle`（仅作为次选，不作为首发主线）。

Stage 3（激进压缩，仅在前两阶段达标后进行）：
1. 尝试 `neck_slim_0p75_plus_ghost`（先不直接上 0.625）。
2. 若出现明显精度回撤，则回退至 Stage 2 最优点，不继续压缩。

### 5) 可行性 / 工作量 / 风险评估

| 方案 | 可行性 | 工作量 | 风险 | 备注 |
|---|---|---|---|---|
| P2 + 单点 SimAM | 高 | 中 | 低 | 直接对准 Recall 短板 |
| adapters+head -> DWConv | 高 | 低-中 | 低 | 参数收益显著（-16.72%）且实现简单 |
| adapters+head -> ShuffleConv | 中-高 | 中 | 中 | 参数收益可观（-12.80%），但稳定性需验证 |
| neck_slim_0p75 + Ghost/Shuffle | 中 | 中-高 | 中-高 | 降参大（-28%~-31%），但精度回撤概率高 |
| neck_slim_0p625 + Ghost/Shuffle | 中 | 高 | 高 | 最大降参（-36%~-38%），不建议当前阶段直接投入 |

### 6) 建议验收门槛（继续沿用并细化）

- 主目标：`mAP50-95` 相比当前 `mbv3` 至少 `+0.3` 个百分点。
- Recall 目标：不低于 baseline `-0.3` 个百分点（优先确保小目标不恶化）。
- 轻量化目标：在 Stage 2 达到参数下降 `>=10%`（DWConv 路线可满足）。
- 速度目标：FPS 不低于当前 `mbv3` 的 `90%`。

结论：
- 目前最合理主线不是“直接追求最大降参”，而是“先补 Recall，再做中等强度 Neck 轻量化”。
- 因此优先路线定为：`P2 + 单点 SimAM` -> `adapters_plus_head_conv_to_dw` ->（达标后再考虑）`neck_slim_0p75_plus_ghost`。
