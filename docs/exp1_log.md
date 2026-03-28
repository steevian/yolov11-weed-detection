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

