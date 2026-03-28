# 项目过程备查文档（exp0）

> 文档定位：本文件为项目过程备查手册，归档未进入 `basememory.md` 的过程性信息（运行日志、调试过程、失败尝试、临时分析、口径讨论）。用于论文写作时的证据追溯与细节补充，不作为主结论文档。

## 1. 归档来源
- `docs/firstmemory.md`（已重命名为 `docs/basememory.md` 前的主过程档）
- `docs/first_memory.md`（补充性高价值快照）
- `docs/analysis1.txt`（深度分析稿）

## 2. 归档分类
- A类：训练流程与阶段进展
- B类：异常与修复记录
- C类：公平性与口径决策
- D类：评测结果与资产管理
- E类：独立分析稿（未入核心文档的原分析）

---

## A类：训练流程与阶段进展（过程档）

### A1. 基线阶段划分与执行顺序（原规划）
- 阶段0：环境与目录基线固化。
- 阶段1：数据集合并划分、VOC 转 YOLO、`data.yaml` 自动生成与校验。
- 阶段2：YOLOv11-S 训练。
- 阶段3：MobileNetV3 改造训练。
- 阶段4：ECA 插入与训练。
- 阶段5：统一评测、样例导出、报告生成。

### A2. 阶段1关键过程记录
- 数据规则：`data2021+data2022` 用于 train/val（85:15），`data2023` 全量为 test。
- 小样本冒烟：`train=170`、`val=30`、`test=200`。
- 标签转换冒烟：`converted=400`、`failed=0`。
- 校验：`data.yaml` 验证 `PASS`。
- 全量执行结果：`train=5654`、`val=998`、`test=1784`，转换 `converted=8436`、`failed=0`。

### A3. 阶段2/3/4主过程记录
- phase2 冒烟 50 epochs：`baseline_20260310_141013`。
- phase3 冒烟 50 epochs：`mbv3_20260310_155214`。
- phase4 冒烟 50 epochs：`mbv3_eca_20260310_175456`。
- 正式 full200 链路：后续分阶段完成并归档。

### A4. 后续里程碑节点
- 2026-03-15：phase2 正式 run 完整 200 轮完成。
- 2026-03-17：phase3 正式 run 完成并启动 phase4。
- 2026-03-19：phase4 完成，开始 full200 独立验证与论文资产保全。
- 2026-03-22：四模型统一评测与公平性说明形成固定口径。

---

## B类：异常与修复记录（调试档）

### B1. 典型报错与根因
- `DataLoader worker process` 异常，伴随 OpenCV `Insufficient memory`。
- 训练中断后出现空权重 run（`weights/` 为空），不可 resume。
- 日志观测误判：旧日志文件仍在但不再刷新，导致看起来在跑，实际已停。

### B2. 主要修复动作
- phase2 脚本加入 `--workers`、`--device`、`--cache` 参数，默认收敛到稳定配置。
- 发生 DataLoader 内存问题时自动降级重试（`workers=0`，必要时 batch 阶梯降级）。
- 新增守护脚本 `run_phase2_resilient.ps1`，支持异常后自动重试与断点续训。
- 增加失败归档日志：`experiments/logs/phase2_failures/`。
- 加固流水线：阶段失败即中止，且仅选取含 `weights/best.pt` 的有效 run。

### B3. 环境修复记录
- 修复前：`torch 2.9.1+cpu`，GPU 不可用。
- 修复后：`torch 2.9.1+cu128`、`torchvision 0.24.1+cu128`、`torchaudio 2.9.1+cu128`，`torch.cuda.is_available() = True`。
- 训练执行解释器口径固定：优先使用 conda 环境解释器，避免命中 CPU 版 torch。

### B4. 高密度失败时间窗（保留）
- `mbv3_eca2_smoke50_20260319_184000` 在 2026-03-20 11:36 至 13:07 出现连续失败重启。
- 该 run 最终在 2026-03-21 恢复完成；可作为抗中断守护有效但不稳定阶段存在大量重试的过程证据。

---

## C类：公平性与口径决策（过程口径）

### C1. 关键决策
- 明确废弃batch 混用的历史结果（`batch=8` 与 `batch=6` 混合）用于主对比。
- 正式实验统一关键参数：`epochs=200`、`batch=6`、固定数据协议。
- 训练中断场景下，不允许将无效 run 混入正式结论。

### C2. 口径澄清
- `707/943` 是每轮迭代步数变化，不是样本总数变化。
- `workers` 从 0 到 1 的变更仅影响数据加载并行度，不改变优化目标函数。
- ECA2 早停发生在统一 patience 规则内，属于公平训练协议允许事件。

---

## D类：评测结果与资产管理（非主文档细节）

### D1. 冒烟资产保全
- 保全目录：`experiments/summary/smoke50_preservation_20260319/`。
- 内容：保全说明、关键文件 SHA256、三模型冒烟 run 的核心证据文件。

### D2. full200 三模型验证落盘
- 目录：`experiments/summary/full200_validation_20260319/`。
- 关键文件：`comparison_metrics_full200.csv`、`comparison_metrics.md`、`实验汇总报告.md`、`figures_index.md`。

### D3. 四模型统一评测落盘
- 目录：`experiments/summary/full200_validation_20260322/`。
- 关键文件：`comparison_metrics_full200_4models.csv`、`comparison_metrics_full200_4models.md`。

### D4. 过程结论性补充（来自 first_memory）
- 新版 ECA2 相对旧 ECA：参数/FLOPs 显著下降，mAP50 与 mAP50-95 显著提升。
- 但 Recall 未同步提升到理想水平，说明跨域漏检问题未被完全根治。

---

## E类：独立分析稿归档（analysis1 提炼版）

### E1. 主要判断
- 数据增强是开启且有效的，不属于未做增强。
- 验证高分与测试低分的主要原因是跨年 domain shift，而非训练流程失效。
- ECA2 达成更轻 + 更准的结构目标，但单靠结构改进不足以彻底解决跨域召回瓶颈。

### E2. 优化建议分层
- 不改训练协议：阈值扫描、TTA、模型集成（优先）。
- 改训练协议：强增广短程微调、半监督伪标签回灌（需单列为扩展实验）。

### E3. 论文使用建议
- 主结论使用 `basememory.md`。
- 方法细节与追溯证据从本文件抽取。
- 若答辩需为什么测试明显掉点，优先引用 domain shift 证据链。

---

## 3. 维护说明
- 本文档允许保留过程冗余，用于可追溯。
- 若后续继续训练，请在对应分类中追加时间-动作-结果三元记录。
- 与 `basememory.md` 同步原则：核心结论上收，过程流水下沉。
