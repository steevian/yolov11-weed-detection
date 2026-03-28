# 毕设核心基线文档（newmemory）

> 文档定位：本文件是导师新方案下的毕业论文核心基线，只保留第二次实验（exp1）可直接用于写作的主线信息（计划、协议、核心指标口径、结论位）。
> 维护边界：exp1 的过程日志统一记录在 `docs/exp1_log.md`；第一次实验历史资料归档至 `exp0/` 与 `docs/exp0.md`，不再作为主结论依据。

## 1. 新实验目标与边界
- 实验总目标：按新方案完成可复现训练与评估链路，全部产物沉淀到 `exp1/`。
- 数据边界：仅使用 `data2021 + data2022`，不使用 2023。
- 公平性原则：三模型除结构差异外，训练参数、评估参数、数据划分、随机种子保持一致。

## 2. 项目定位与系统事实（继承基线）
- 仓库目录名：`yolo_web-main`
- README 标题：`yolov11-weed-detection`
- 系统形态：前后端分离的杂草检测系统（Vue3 + Flask + YOLO）
- 论文研究主线：在统一协议下完成 YOLOv11-S 基线与 MBV3/ECA/ECA2 改进模型的公平对比，验证轻量化与精度权衡。

## 2.1. 技术栈与系统边界
- 前端：Vue 3、Vite、TypeScript、Vue Router、Pinia、Element Plus、Axios、Socket.IO Client
- 后端：Python、Flask、Flask-Cors、Flask-SocketIO
- 模型推理：Ultralytics YOLO、PyTorch、OpenCV、NumPy、Pillow
- 数据与鉴权：SQLite、PyJWT
- 训练工程边界：训练代码集中在 `training/`，业务代码集中在 `yolo_weed_detection_flask/` 与 `yolo_weed_detection_vue/`，相互解耦。

## 2.2 系统结构与已实现能力

### 2.2.1 核心目录
- `yolo_weed_detection_flask/`：后端服务入口、检测接口、数据与用户管理。
- `yolo_weed_detection_vue/`：前端页面、路由、接口封装。
- `training/`：训练脚本、模型配置、复现配置与守护脚本。
- `experiments/`：训练日志、评测结果、汇总报告、样例导出。

### 2.2.2 业务功能现状
- 检测能力：图像/视频/摄像头检测，含结果保存与进度推送。
- 历史记录：支持分页、筛选、详情查询与删除。
- 用户权限：JWT 鉴权，角色路由过滤。
- 训练管理：前后端接口已具备；业务后端以占位和 runs 扫描为主，不承担正式训练调度。

## 2.3 环境与复现基线
- 机器：Windows 11，RTX 3060 Laptop GPU，16GB RAM。
- 项目训练环境：Miniconda `weedweb_detection`。
- 关键依赖：PyTorch GPU 版（`torch 2.9.1+cu128`）、Ultralytics `8.4.7`。
- 复现原则：关键实验前进行环境快照归档，保证可追溯。
- 业务系统与训练系统仍保持解耦：本轮训练工作区以 `exp1/` 为中心。
- 论文主线调整：本次论文主结果以 exp1 实验链路输出为准，历史 experiments 结果仅作背景参考。

## 3. 新实验目录基线（exp1）
- `exp1/configs/`：模型结构与复现配置。
- `exp1/models/`：`mobilenetv3_backbone.py`、`eca.py`。
- `exp1/train.py`：统一训练入口（baseline/mbv3/eca）。
- `exp1/expand.py`：扩充实验（可选）。
- `exp1/report.py`：汇总报告生成。
- `exp1/dataset/`：数据划分与 `data.yaml`。
- `exp1/runs/`：训练过程与权重产物。
- `exp1/eval/`：测试评估 JSON。
- `exp1/reports/`：论文可用汇总表。
- `exp1/meta/`：环境快照。
- `exp1/logs/`：执行日志。

## 4. 数据准备协议（固定）
- 输入源：`data/3SeasonWeedDet10/data2021`、`data/3SeasonWeedDet10/data2022`。
- 预处理脚本：`exp1/scripts/prepare_dataset.py`。
- 数据转换：XML -> YOLO 标签，输出 10 类 `classes.txt`（ID 0~9）。
- 划分策略：`7:1.5:1.5` 分层随机划分（seed=42）。
- 输出资产：
	- `exp1/dataset/images/{train,val,test}`
	- `exp1/dataset/labels/{train,val,test}`
	- `exp1/dataset/data.yaml`
	- `exp1/dataset/split_stats.json`
	- `exp1/logs/prepare_dataset.log`

## 5. 模型方案（新基线）
- Baseline：`exp1/configs/yolov11s.yaml`
- MBV3：`exp1/configs/yolov11s_mbv3.yaml`
- ECA：`exp1/configs/yolov11s_mbv3_eca.yaml`
- 结构约束：Neck 与 Detect 保持 YOLOv11-S 主体结构不变；ECA 方案采用 P3/P4/P5 三点插入口径。

## 6. 统一训练与评估协议

### 6.1 训练参数（统一固定）
- `epochs=200, batch=6, imgsz=640`
- `optimizer=SGD, lr0=0.01, lrf=0.01`
- `momentum=0.937, weight_decay=0.0005`
- `warmup_epochs=3.0, warmup_momentum=0.8, warmup_bias_lr=0.1`
- `patience=50, device=0, workers=1`

### 6.2 增强参数（统一固定）
- `hsv_h=0.015, hsv_s=0.7, hsv_v=0.4`
- `degrees=8.0, translate=0.1, scale=0.2`
- `shear=0.0, perspective=0.0, flipud=0.1, fliplr=0.5`
- `mosaic=1.0, mixup=0.0, copy_paste=0.0`
- `auto_augment=randaugment, erasing=0.4, close_mosaic=10`

### 6.3 评估参数（统一固定）
- `iou=0.7, max_det=300`

## 7. 复现与抗中断口径
- 统一入口：`exp1/train.py --model baseline|mbv3|eca`
- 支持断点续训：优先恢复 `last.pt`。
- 训练结束自动评估：使用 `best.pt` 在测试集评估。
- 环境快照：`exp1/meta/environment_snapshot.json`。

## 8. 论文结果资产出口
- 训练结果：`exp1/runs/{model}/results.csv`
- 测试评估：`exp1/eval/{model}_test_results.json`
- 汇总报告：`exp1/reports/exp1_report.md`
- 扩充实验：`exp1/expand/*.csv`

## 9. 执行顺序（新方案）
1. 数据准备与校验。
2. baseline 全量训练（200轮）并监控日志。
3. MBV3 全量训练。
4. ECA 全量训练。
5. 统一评估与报告生成。

## 10. 验收标准
- 全部新产物位于 `exp1/`。
- 三模型在同一套参数协议下可复现训练与评估。
- `exp1/eval` 与 `exp1/reports` 输出可直接用于论文表格与分析。

## 11. 状态声明
- 第一次实验方案已退出主线；其历史文件仅用于备查，不进入本轮论文主结论。
