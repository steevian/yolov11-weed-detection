# 项目基础记忆（memory）

## 1. 项目名称
- 仓库目录名：`yolo_web-main`
- README 标题：`yolov11-weed-detection`
- 项目形态：前后端分离的杂草检测系统（Vue3 + Flask + YOLO）

## 2. 技术栈
- 前端：`Vue 3`、`Vite`、`TypeScript`、`Vue Router`、`Pinia`、`Element Plus`、`Axios`、`Socket.IO Client`
- 后端：`Python`、`Flask`、`Flask-Cors`、`Flask-SocketIO`
- AI 推理：`ultralytics YOLO`、`torch`、`opencv-python`、`numpy`、`Pillow`
- 数据存储：`SQLite`（本地文件数据库）
- 鉴权：`PyJWT`（JWT）
- 训练相关：后端提供训练管理接口（当前为占位/联调实现，未接入真实训练调度）

依据文件：
- `README.md`
- `yolo_weed_detection_flask/requirements.txt`
- `yolo_weed_detection_vue/package.json`

## 3. 核心目录结构（实际存在）
```text
yolo_web-main/
  yolo_weed_detection_flask/        # Flask后端（主服务）
    main.py                         # 服务入口与路由注册
    user_manager.py                 # 用户与JWT逻辑
    core/
      settings.py                   # 环境配置读取
      database.py                   # SQLite连接与PRAGMA
    predict/
      predictImg.py                 # 图像推理类
    weights/                        # 模型权重（含 weed_best.pt）
    uploads/                        # 上传资源
    results/                        # 检测结果资源
    runs/                           # 运行与中间产物
    weed_detection.db               # SQLite数据库文件

  yolo_weed_detection_vue/          # Vue前端
    src/
      api/                          # 接口封装（login/menu/train）
      router/                       # 静态/动态路由与权限过滤
      views/
        Dashboard/
        Detect/                     # Image/Video/Camera
        History/                    # Image/Video/Camera
        Train/                      # 训练管理相关页面
        Login/
        UserCenter/
      utils/request.ts              # Axios实例与拦截器
    vite.config.ts                  # 开发代理与构建配置

  data/3SeasonWeedDet10/            # 数据集目录（含 data2021/2022/2023）
  docs/                             # 项目文档
  _legacy_archive/                  # 历史归档（旧结果/旧权重/旧DB备份等）
  reference/                        # 参考项目代码（独立参考，不是当前主运行目录）
  start_local.ps1                   # 本地一键启动脚本
  start_local.bat                   # Windows 启动入口
  .env.example                      # 环境变量模板
```

## 4. 已实现功能（仅基于现有代码）

### 4.1 检测与媒体处理
- 图像检测：支持上传/URL输入后进行 YOLO 推理并返回标签、置信度、检测框、耗时。
- 视频检测：支持视频处理并输出结果视频，处理过程通过 Socket.IO 推送进度。
- 摄像头检测：提供摄像头检测与停止接口。
- 静态资源访问：可通过后端访问 `uploads`、`results`、`runs` 下文件。

依据文件：
- `yolo_weed_detection_flask/main.py`（`predictImg`、`predictVideo`、`predictCamera`、`stopCamera`、Socket 事件）
- `yolo_weed_detection_flask/predict/predictImg.py`

### 4.2 检测记录管理
- 数据表：`img_records`、`video_records`、`camera_records`。
- 能力：分页查询、按条件查询、按 ID 删除、视频记录详情查询。
- 路径处理：数据库写入时将绝对路径标准化为项目内相对路径（以 `/uploads`、`/results`、`/runs` 等为锚点）。

依据文件：
- `yolo_weed_detection_flask/main.py`（`DatabaseManager` + 记录接口）
- `yolo_weed_detection_flask/core/database.py`

### 4.3 用户与权限
- 用户注册、登录、查询、更新、删除。
- 启动时会确保存在默认管理员账号（`admin/admin123`）。
- 登录成功返回 JWT；前端请求拦截器会将 token 放入 `Authorization` 头。
- 前端路由按角色过滤，`admin` 拥有用户管理与训练管理菜单。

依据文件：
- `yolo_weed_detection_flask/user_manager.py`
- `yolo_weed_detection_flask/main.py`（用户接口）
- `yolo_weed_detection_vue/src/router/route.ts`
- `yolo_weed_detection_vue/src/router/frontEnd.ts`
- `yolo_weed_detection_vue/src/utils/request.ts`

### 4.4 训练管理（当前状态）
- 前端已具备训练管理页面与 API 封装（任务、监控、数据集、模型比较）。
- 后端已实现训练管理接口与管理员权限校验。
- 当前接口为“占位 + runs 扫描”模式：
  - 不执行真实训练调度。
  - 部分数据可从 `runs/**/results.csv` 读取；其余返回占位数据。

依据文件：
- `yolo_weed_detection_vue/src/views/Train/*`
- `yolo_weed_detection_vue/src/api/train/index.ts`
- `yolo_weed_detection_flask/main.py`（`get_train_*`、`create_train_task`）

## 5. 模块说明
- 后端入口模块：`yolo_weed_detection_flask/main.py`
  - `VideoProcessingApp` 负责 Flask/SocketIO 初始化、路由注册、模型加载、检测流程。
  - `DatabaseManager` 负责检测记录表与记录读写。
- 用户模块：`yolo_weed_detection_flask/user_manager.py`
  - 用户表初始化、密码哈希、JWT 生成/校验、用户CRUD。
- 前端路由模块：`yolo_weed_detection_vue/src/router/*`
  - 路由守卫、登录拦截、角色菜单过滤、前后端路由控制模式。
- 前端接口模块：`yolo_weed_detection_vue/src/api/*`
  - 登录、菜单、训练相关 API 封装。

## 6. 路径与命名约定（代码中的实际约定）
- 后端路径锚定：所有运行目录默认锚定在 `yolo_weed_detection_flask/` 下。
  - 上传：`uploads/`
  - 推理结果：`results/`
  - 运行产物：`runs/`
  - 模型：`weights/weed_best.pt`
- 路径标准化：数据库中优先保存项目内相对路径（如 `/results/videos/xxx.mp4`）。
- 前端路由约定：`route.ts` 明确建议“路由 path 与页面目录名称对应”。
- 本地开发代理：`vite.config.ts` 将 `/flask`、`/predict*`、`/uploads`、`/results`、`/runs`、`/socket.io` 等代理到 Flask。

## 7. 启动与环境约定
- 本地一键启动脚本：`start_local.ps1`（由 `start_local.bat` 调用）。
- 默认端口：后端 `8080`，前端 Vite `5173`（HTTPS 开启）。
- 环境模板：`.env.example` 提供 `PORT`、`FLASK_HOST`、`VITE_FLASK_BASE_URL`、`SQLITE_DB_PATH` 示例。

## 8. 非主线目录说明
- `_legacy_archive/`：历史文件归档目录（备份DB、旧结果、旧工具）。
- `reference/`：参考实现目录，用于参考，不属于当前主服务运行入口。
- `docs/`：过程文档与规划文档。

## 9. 当前可作为后续工作的事实基线

## 10. 本机硬件环境与虚拟环境软件版本归档（训练前环境确认）

> **说明**：
> 在开展 yolov11 训练前，归档本机硬件环境与当前虚拟环境主要软件包版本，便于后续溯源、复现和排查环境相关问题。建议每次重要训练前都进行一次环境快照归档。

### 10.1 本机硬件环境（2026-03-10）

- **主机型号**：Redmi G 2022
- **操作系统**：Windows 11 家庭中文版 10.0.26100
- **处理器**：AMD Ryzen 7 6800H with Radeon Graphics（8核16线程，主频约3.2GHz）
- **内存**：16GB（2×8GB Samsung DDR5 4800MHz）
- **硬盘**：Phison CFESR512GMTCT-E9C-2 512GB SSD
- **显卡**：NVIDIA GeForce RTX 3060 Laptop GPU + AMD Radeon(TM) Graphics
- **主板**：TIMI TM2137
- **系统类型**：x64-based PC
- **网络**：Realtek Gaming 2.5GbE、Realtek RTL8852BE WiFi 6、蓝牙、虚拟网卡等

### 10.2 当前虚拟环境与主要软件包（2026-03-10）

- **本项目专用虚拟环境**：weedweb_detection（Miniconda3 环境）
- **主 Python 版本**：3.11.3
- **conda 版本**：22.11.1
- **说明**：本项目仅使用 weedweb_detection 虚拟环境，其他如 base、py39、yolo_detect、yolo_dzyj 等为其他项目环境，与本项目无关。
- **当前环境主要包（部分）**：
  - Flask 3.1.2
  - flask-cors 6.0.2
  - Flask-SocketIO 5.6.0
  - torch 2.9.1
  - torchvision 0.24.1
  - ultralytics 8.4.7
  - opencv-python 4.13.0.90
  - numpy 2.4.1
  - pillow 12.1.0
  - PyJWT 2.11.0
  - scipy 1.17.0
  - matplotlib 3.10.8
  - tqdm 4.67.3
  - 其余见 pip/conda list 归档

> **完整包列表快照**：
> - pip/conda list 详见本地归档（如需溯源可查 VSCode Copilot Chat 归档或命令行快照）。

---
（本节每次重要训练前建议更新，确保环境可复现与问题可追溯）

## 11. 毕设训练与论文一体化执行基线（2026-03-10）

### 11.1 总体原则
- 训练代码独立于业务代码：所有训练与实验脚本放在 `training/`，不修改 `yolo_weed_detection_flask/` 与 `yolo_weed_detection_vue/`。
- 实验产物统一沉淀到 `experiments/`，作为论文图表和表格的唯一来源目录。
- 三模型对比公平性：除模型结构差异外，训练参数、数据划分、评测协议保持一致。

### 11.2 分阶段落地顺序
- 阶段0：环境与目录基线固化（目录、依赖、复现实验配置）。
- 阶段1：数据集合并划分、VOC 转 YOLO、`data.yaml` 自动生成与校验（优先完成）。
- 阶段2：基线 YOLOv11-S 训练与实验记录。
- 阶段3：MobileNetV3 backbone 改造与同参训练。
- 阶段4：ECA 注意力插入、结构健全性检查与训练。
- 阶段5：三模型统一评测、样例导出、论文报告自动生成。

### 11.3 阶段1执行要求（已定）
- 数据规则：`data2021+data2022` 作为 train/val 候选池（85:15 分层），`data2023` 全量作为 test。
- 类别顺序固定为 10 类：
  `Carpetweed, Eclipta, Goosegrass, Lambsquarters, Morningglory, Ragweed, Palmer Amaranth, Purslane, Spotted spurge, Waterhemp`。
- 容错日志：坏图、缺失 XML、空标注、XML 转换错误必须写入 `experiments/logs/`。
- 先做小样本冒烟（`--limit`），通过后再跑全量。

### 11.4 当前新增基础文件（训练工作区）
- `training/requirements-training.txt`
- `training/configs/reproducibility.yaml`
- `training/scripts/phase1_merge_split.py`
- `training/scripts/phase1_voc_to_yolo.py`
- `training/scripts/phase1_generate_data_yaml.py`

### 11.5 执行入口（阶段1）
```powershell
python training/scripts/phase1_merge_split.py --limit 200 --clean-output
python training/scripts/phase1_voc_to_yolo.py
python training/scripts/phase1_generate_data_yaml.py
```

冒烟通过后去掉 `--limit` 跑全量。

### 11.6 执行进度状态（2026-03-10）
- 阶段0：已完成基础骨架
  - 已创建 `training/`、`training/configs/`、`training/scripts/`、`training/lib/`、`training/ultralytics_custom/`、`experiments/summary/`。
  - 已创建依赖文件 `training/requirements-training.txt` 与复现配置 `training/configs/reproducibility.yaml`。
- 阶段1：已完成脚本开发并通过小样本冒烟
  - 冒烟命令：`phase1_merge_split.py --limit 200 --limit-test 200 --clean-output`
  - 冒烟结果：`train=170`、`val=30`、`test=200`
  - 转换结果：`phase1_voc_to_yolo.py --force` 后 `converted=400`、`failed=0`
  - 校验结果：`phase1_generate_data_yaml.py --validate-only` 为 `PASS`
- 阶段2：已完成训练脚本与记录模块开发
  - 已新增 `phase2_train_yolo11s.py`、`experiment_logger.py`、`plotter.py`
  - 脚本参数帮助验证通过（`--help` 正常）
  - 50 epochs 冒烟训练已完成（run_id: `baseline_20260310_141013`）
  - 训练耗时：约 `01:28:50`
  - 最优轮（按 `mAP50-95`）：epoch `47`
    - `mAP50=0.8247`
    - `mAP50-95=0.6585`
    - `Precision=0.9798`
    - `Recall=0.6528`
- 阶段3：已完成代码落地
  - 已新增 `training/configs/yolo11s_mbv3.yaml`
  - 已新增 `training/scripts/phase3_train_yolo11s_mbv3.py`
  - 已完成模型配置实例化冒烟（可构建 `DetectionModel`）
  - 50 epochs 冒烟训练已完成（run_id: `mbv3_20260310_155214`）
  - 训练耗时：约 `01:32:08`
  - 最优轮（按 `mAP50-95`）：epoch `47`
    - `mAP50=0.8269`
    - `mAP50-95=0.4941`
    - `Precision=0.7521`
    - `Recall=0.8333`
- 阶段4：已完成代码落地与结构验证
  - 已新增 `training/models/eca.py`、`training/configs/yolo11s_mbv3_eca.yaml`
  - 已新增 `training/scripts/phase4_sanity_check_forward.py`、`phase4_train_yolo11s_mbv3_eca.py`
  - 已完成本地 `ultralytics` 副本准备与模块注册：
    - `phase0_prepare_ultralytics_custom.py`
    - `phase3_register_custom_modules.py`
  - 前向健全性结果：参数量约 `9.32M`，FLOPs 约 `11.59G`（imgsz=640）
  - 50 epochs 冒烟训练已完成（run_id: `mbv3_eca_20260310_175456`）

## 12. 训练公平性关键决策（2026-03-11）

- 决策：放弃此前“前20轮 batch=8 后续再改 batch=6”的基线结果，不再作为正式对比依据。
- 原因：该过程存在 batch 混用，会破坏三模型横向对比的同参公平性，影响论文结论严谨性与可答辩性。
- 新基线要求：YOLOv11-S 必须执行全新全量训练，`epochs=200`、`batch=6`、`resume=false`、`strict-batch=true`。
- 执行策略：训练异常时不做降 batch 续训，不混用历史 checkpoint；失败 run 视为废弃并清理后重启全新 run。
- 目标：产出“全程 batch=6、无断点、无混参”的标准 baseline，用于与 MobileNetV3 改进版、ECA 改进版进行公平对比。
- 2026-03-11 晚重新执行：已停止此前所有失败重试链与守护进程，清空 `baseline_full200_fresh*` / `baseline_full200_retry*` 残留 run 与相关日志后，重新从 `yolo11s.pt` 启动全新 200 轮训练。
- 当前重启原则：只保留一条活跃训练终端，统一跟踪 `phase2_active_progress.log`，避免 stdout/stderr 分裂或旧日志残留误导对训练进度的判断。
  - 训练耗时：约 `02:04:47`
  - 最优轮（按 `mAP50-95`）：epoch `47`
    - `mAP50=0.7977`
    - `mAP50-95=0.4983`
    - `Precision=0.9474`
    - `Recall=0.7461`
- 阶段5：已完成评测与报告脚本开发
  - `phase5_evaluate_all.py`
  - `phase5_export_samples.py`
  - `phase5_generate_report.py`
  - 已配置链式自动执行脚本：`training/scripts/run_phase3_to_phase5_chain.ps1`
    - phase3完成后自动进入 phase4（50 epochs）
    - phase4完成后自动执行 phase5 评测、样例导出与报告生成
  - 已启动 phase4->phase5 自动链：`training/scripts/run_phase4_to_phase5_chain.ps1`
  - 已手动完成 phase5 收口：
    - `experiments/summary/comparison_metrics.csv`
    - `experiments/summary/comparison_metrics.md`
    - `experiments/summary/实验汇总报告.md`
    - `experiments/summary/figures_index.md`
    - `experiments/summary/samples/`

### 11.7 当前结果解释边界（重要）
- 当前 `phase2~phase5` 结果属于“流程冒烟验证结果”，不能直接作为论文最终结论。
- 原因1：阶段1目前使用的是冒烟数据集（`--limit 200 --limit-test 200`），当前 test 仅覆盖 4 个类别，而不是完整 10 类。
- 原因2：阶段2/3/4 当前均为 `50 epochs` 冒烟训练，不是计划中的 `200 epochs` 全量正式训练。
- 当前 smoke test 的 test 类别覆盖统计：`{3: 200, 5: 36, 6: 23, 7: 25}`，因此样例导出只能得到 `8` 张，而不是计划中的 `20` 张。
- 结论：现有产物用于验证脚本链路、目录规范、日志与报告生成是否正确；若用于论文正式结果，需要先重跑全量 Phase1，再用全量数据执行 200 epochs 正式训练与评测。

### 11.8 正式版执行进展（2026-03-10 晚）
- 全量 Phase1 已完成（使用 hardlink 模式避免磁盘占用）：
  - 命令：`phase1_merge_split.py --clean-output --copy-mode hardlink`
  - 结果：`train=5654`、`val=998`、`test=1784`
  - 标签转换：`converted=8436`、`failed=0`
  - `data.yaml` 校验：`PASS`
- 正式版 200 epochs 全流程脚本已创建并启动：
  - 脚本：`training/scripts/run_formal_200_pipeline.ps1`
  - 执行顺序：phase2(200) -> phase3(200) -> phase4(200) -> phase5
  - 当前状态：已进入 phase2 正式训练启动阶段
- 数据覆盖补充说明：当前 full test split 实际覆盖到 8 个类别（ID：`0,2,3,5,6,7,8,9`），未见 `1,4` 类。

### 11.9 断训排查与GPU环境修复（2026-03-11）
- test 集类别缺失结论确认：
  - 已确认并非 Phase1 脚本问题。
  - 根因是 `data2023` 原始数据本身仅覆盖 8 类，因此 full test split 缺失 `1,4` 类属于数据源客观事实。
- 断训现场排查：
  - `experiments/YOLOv11-S/baseline_full200_20260310_215138/weights/` 为空，属于中断后未产出有效权重的残留 run。
  - 该残留 run 不可直接用于 resume（无 `last.pt`/`best.pt`），建议新开 run 重新执行 Phase2 正式训练。
- 本机环境复扫（训练前二次确认）：
  - GPU：`NVIDIA GeForce RTX 3060 Laptop GPU`
  - 驱动版本：`552.22`
  - NVIDIA 报告 CUDA 版本：`12.4`
  - Python（weedweb_detection）：`3.11.14`
- PyTorch GPU可用性修复结果：
  - 原状态：`torch 2.9.1+cpu`（`torch.cuda.is_available() = False`）
  - 修复后：
    - `torch 2.9.1+cu128`
    - `torchvision 0.24.1+cu128`
    - `torchaudio 2.9.1+cu128`
    - `ultralytics 8.4.7`
    - `torch.cuda.is_available() = True`，可识别 1 张 GPU。
- 全流程脚本加固（避免“失败后继续跑后续阶段”）：
  - 已修改 `training/scripts/run_formal_200_pipeline.ps1`：
    - 每个 phase 执行后强制检查退出码，失败立即中止。
    - 读取阶段产物时仅选择含 `weights/best.pt` 的最新有效 run，规避中断残留目录干扰。
- Phase2 新增稳定性修复（DataLoader 内存报错）：
  - 报错现象：训练在 epoch 3 附近触发 `DataLoader worker process` 异常，根因是 OpenCV `Insufficient memory`（多进程图像读取内存紧张）。
  - 代码修复：已修改 `training/scripts/phase2_train_yolo11s.py`，新增 `--workers`（默认2）、`--device`（默认0）参数，并在捕获到 DataLoader/OpenCV 内存错误时自动降级重试 `workers=0`。
  - 续训策略：使用 `weights/last.pt + --resume` 从断点继续训练，当前已从 epoch 3 恢复成功并继续执行。
- Phase2 抗中断执行增强：
  - 已新增 `training/scripts/run_phase2_resilient.ps1`，用于从 `last.pt` 弹性续训；当进程异常退出时，脚本会按间隔自动重试，直至训练完成或达到最大重试次数。
  - 当前实际执行参数为 `workers=0`，优先稳定性，避免 DataLoader 多进程导致的 OpenCV 内存抖动。
- 无效目录清理：
  - 已清理中断残留目录 `experiments/YOLOv11-S/baseline_full200_20260310_215138`（空权重）和 `experiments/YOLOv11-S/baseline_20260311_142052`（仅元数据占位）。
  - 影响评估：上述目录不被训练脚本硬编码依赖，删除不影响当前续训与后续 phase 链路。
- 2026-03-11 晚间再次“中断”复盘与加强：
  - 复盘结论：用户贴出的 `worker process 6` 报错为旧日志片段；当前 `last.pt` 中 `train_args.workers=0`，并非持续使用旧的多进程参数。
  - 强化改造：
    - `phase2_train_yolo11s.py` 默认参数进一步收敛为 `workers=0`、`batch=6`，并新增内存降级阶梯重试（`batch=4 -> 2`）。
    - `run_phase2_resilient.ps1` 新增 `-Batch` 参数，守护启动默认以保守参数恢复（当前使用 `workers=0, batch=4`）。
  - 当前状态：已从同一 run 断点恢复到更后轮次（日志显示已继续到 `epoch 19`），并由后台守护进程接管，降低会话关闭导致中断的风险。
- 2026-03-11 训练稳态方案（稳定+提速并重）：
  - `phase2_train_yolo11s.py` 已支持 `--cache` 参数（默认 `disk`），在不增加RAM峰值风险的情况下提升读取吞吐。
  - `run_phase2_resilient.ps1` 已升级参数：`workers=0, batch=6, cache=disk`（稳态默认），并保留失败自动重试与断点续训。
  - 每次异常退出会在 `experiments/logs/phase2_failures/` 写入独立失败记录（退出码、时间戳、checkpoint状态），同时总日志持续写入：
    - `experiments/logs/phase2_resilient_stdout.log`
    - `experiments/logs/phase2_resilient_stderr.log`
  - GPU利用率判断规则：
    - 不能只看 `GPU_mem`；显存占用不是唯一效率指标。
    - 实测采样：`utilization.gpu=100%`、`memory.used≈5819MiB/6144MiB`，说明训练阶段已基本吃满GPU，属于有效利用状态。
- 2026-03-11 持续自动巡检已启用：
  - 已新增 `training/scripts/run_phase2_monitor.ps1`，作为独立后台巡检与自愈脚本。
  - 功能：周期性写入状态文件与心跳日志，并在发现 `phase2_train_yolo11s.py` 与 `run_phase2_resilient.ps1` 都不在运行时，自动重新拉起弹性续训脚本。
  - 当前状态文件与日志：
    - `experiments/logs/phase2_monitor_status.json`
    - `experiments/logs/phase2_monitor_heartbeat.log`
  - 当前观测：巡检已检测到训练守护缺失并自动完成一次重启；最新心跳显示 `python=1`、`resilient=1`，说明训练与守护都已重新在线。
- 2026-03-11 手动误点运行 Phase2 的影响与处置：
  - 用户从编辑器直接运行 `phase2_train_yolo11s.py` 时，由于未带 `--resume`，脚本按默认行为新建了一个从第1轮开始的 run：`baseline_20260311_190518`。
  - 该误启动 run 的 `weights/` 为空，未形成有效断点，也未覆盖正式 run；对正式训练无实质影响。
  - 已删除该无效目录，保留正式 run：`baseline_full200_retry_20260311_140837`。
  - 为避免再次误触，`phase2_train_yolo11s.py` 已新增保护：若检测到已有可续训的 `weights/last.pt`，则默认拒绝启动新的 fresh run，必须显式传 `--resume` 或 `--force-new-run`。
  - 已额外打开可见日志终端任务 `Watch Phase2 Training Log`，用于直接观察正式训练输出。
- 2026-03-11 可见终端与乱码问题修复：
  - `Watch Phase2 Training Log` 出现“不动”的根因：该任务跟踪的是旧文件日志，而训练在自愈重启后切换为直接进程输出，日志文件不再持续刷新。
  - 已切换为“可见终端直接运行训练守护”：`Run Phase2 Resilient Visible UTF8`，可实时看到真实训练输出。
  - 已在启动命令中强制 UTF-8（`chcp 65001` + `PYTHONUTF8=1`）以缓解中文/进度条乱码。
- 2026-03-11 论文可比性参数锁定修复：
  - `707/943` 是“每轮迭代步数（batches per epoch）”而非样本总数变化；当前 train 图像总数仍为 `5654`。
  - 根因：历史 run 使用 `batch=8`（`5654/8 -> 707`），当前稳态 run 使用 `batch=6`（`5654/6 -> 943`）。
  - 为保证毕业论文三模型公平对比，已将正式流水线 `run_formal_200_pipeline.ps1` 锁定为统一 `batch=6`，并新增每阶段 `args.yaml` 硬校验（batch 与 data 不一致即中止）。
  - `phase3_train_yolo11s_mbv3.py` 与 `phase4_train_yolo11s_mbv3_eca.py` 默认 `batch` 也已统一为 `6`，避免手动单跑时参数漂移。
近期状态记录
- 2026-03-11：已停止旧 resume 守护链与失败重试链。
- 2026-03-11：已清空 baseline_full200_fresh 与 baseline_full200_retry 残留 run，重新从零启动正式 baseline。
- 2026-03-11：已将 phase5_generate_report.py 中过时的 batch=8 描述修正为 batch=6。
- 2026-03-11：已新增统一 active progress 机制与清洗版实时终端，避免再次盯错旧日志或错误流。

## 13. 训练公平性与Phase2重构收口（2026-03-13）

- 断点恢复分支判定：`baseline_full200_retry_20260311_140837/weights/last.pt` 不存在，无法恢复 140+ 轮完整状态。
- 按规则执行清理分支：
	- 仅保留 50 轮冒烟成果目录 `experiments/YOLOv11-S/baseline_20260310_141013`。
	- 已清理其他 Phase2 非必要 run 目录（含 full200 残留目录）。
- Phase2 脚本重构完成：
	- 唯一主训练脚本：`training/scripts/phase2_train_yolo11s.py`
	- 唯一守护脚本：`training/scripts/run_phase2_resilient.ps1`
	- 已删除冗余 Phase2 脚本：`run_phase2_fresh_monitor.ps1`、`run_phase2_fresh_resilient.ps1`、`run_phase2_monitor.ps1`、`watch_phase2_active_progress_clean.ps1`
- 三阶段公平参数对齐：
	- `phase2_train_yolo11s.py`、`phase3_train_yolo11s_mbv3.py`、`phase4_train_yolo11s_mbv3_eca.py`
	- 统一关键参数：`epochs=200`、`batch=6`、`workers=0`、`cache=disk`、`device=0`、`amp=True`。
- 数据保全与追溯：
	- Phase2 训练过程中自动保留并归档 `train.log`、`results.csv`、`args.yaml`、`results.png`、`env.txt`、`run_summary.json`。
	- 异常与处理过程写入 `docs/trianlog.md`，并自动触发 `firstmemory` 状态更新。
- `.gitignore` 已精准化：不再整目录忽略 `experiments/`，改为忽略大文件产物并追踪核心文本资产。
- Fresh 200 轮已重新启动：活跃 run 为 `baseline_full200_fresh_20260313_195344`（从 `yolo11s.pt` 全新启动）。

## 14. 训练终端并行冲突处置（2026-03-13）

- 出现过双终端并行训练冲突：两个守护实例同时启动导致两个 fresh run 并行，终端进度不一致。
- 已完成止血：仅保留正式守护实例，停止误开的调试实例。
- 新增重开观察脚本：`training/scripts/reopen_phase2_watch.ps1`，可在重开 VSCode 后快速恢复单一进度观察终端。

## 15. Phase2中断恢复结论（2026-03-15）

- 正式 run：`experiments/YOLOv11-S/baseline_full200_fresh_20260313_195344`
- 中断后核验结论：`last.pt` 完整可用，`results.csv` 已稳定记录到 `epoch 107`，训练结果连续正常。
- 误开 run：`baseline_full200_fresh_20260313_195142` 无有效权重，已删除。
- 已重新通过 `run_phase2_resilient.ps1 -Mode resume` 恢复训练，并验证日志从 `108/200` 接续执行。

## 12. Phase2自动更新追踪
- 2026-03-14 23:26:42 | run_id=baseline_full200_fresh_20260313_195344 | status=interrupted
- 2026-03-15 19:21:50 | run_id=baseline_full200_fresh_20260313_195344 | status=failed
- 2026-03-15 19:31:23 | run_id=baseline_full200_fresh_20260313_195344 | status=failed
- 2026-03-15 19:32:38 | run_id=baseline_full200_fresh_20260313_195344 | status=failed
- 2026-03-15 19:34:16 | run_id=baseline_full200_fresh_20260313_195344 | status=failed
- 2026-03-15 23:42:15 | run_id=baseline_full200_fresh_20260313_195344 | status=completed

## 16. Phase3启动审计（2026-03-15）

- 2026-03-15 23:52:41 | 审计结论：Phase2已完整200轮完成（run_id=baseline_full200_fresh_20260313_195344，status=completed）。
- 2026-03-15 23:52:41 | 公平性说明：workers从0调整到1仅影响数据加载并行度，不改变优化目标；在固定seed与其余超参一致前提下，公平性可接受。
- 2026-03-15 23:52:41 | Phase3已启动：run_id=mbv3_full200_fresh_20260315_234917，epochs=200, batch=6, workers=1, cache=disk, device=0, amp=True。

## 16. Phase3自动更新追踪
- 2026-03-16 13:24:46 | run_id=mbv3_full200_fresh_20260315_234917 | status=failed
- 2026-03-16 16:40:14 | run_id=mbv3_full200_fresh_20260315_234917 | status=failed
- 2026-03-16 22:45:17 | run_id=mbv3_full200_fresh_20260315_234917 | status=failed
- 2026-03-17 10:53:08 | run_id=mbv3_full200_fresh_20260315_234917 | status=completed

## 17. Phase3核查与Phase4启动（2026-03-17）

- Phase3正式全量run确认完成：mbv3_full200_fresh_20260315_234917（200/200）。
- Phase3对比YOLOv11-S基线：precision略升，但recall与mAP50/mAP50-95下降；当前阶段MBV3改造未优于基线总体检测效果。
- 已执行保守清理：删除Phase3与ECA冒烟中的可再生中间大文件，保留best/last和所有核心可追踪文本资产。
- 新增Phase4守护与观察脚本：training/scripts/run_phase4_resilient.ps1、training/scripts/reopen_phase4_watch.ps1。
- 已增强phase4_train_yolo11s_mbv3_eca.py：支持checkpoint resume、fresh失败后可由守护脚本自动切resume、并自动写trianlog/firstmemory/run_summary。

## 17. Phase4自动更新追踪
- 2026-03-18 17:13:42 | run_id=mbv3_eca_20260317_114514 | status=failed
- 2026-03-19 01:32:01 | run_id=mbv3_eca_20260317_114514 | status=completed
