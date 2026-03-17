## 2026-03-13 19:51:17 | Phase2 watchdog start

- mode=fresh
- checkpoint=
- epochs=200, batch=6, workers=0, cache=disk, device=0

## 2026-03-13 19:51:43 | Phase2启动

- run_id=baseline_full200_fresh_20260313_195142
- resume=False
- checkpoint=D:\cyd\Desktop\yolo_web-main\experiments\YOLOv11-S\baseline_20260310_141013\weights\last.pt
- epochs=200, batch=6, workers=0, cache=disk, amp=True
## 2026-03-13 19:53:34 | Phase2 watchdog start

- mode=fresh
- checkpoint=
- epochs=200, batch=6, workers=0, cache=disk, device=0

## 2026-03-13 19:53:46 | Phase2启动

- run_id=baseline_full200_fresh_20260313_195344
- resume=False
- checkpoint=D:\cyd\Desktop\yolo_web-main\experiments\YOLOv11-S\baseline_20260310_141013\weights\last.pt
- epochs=200, batch=6, workers=0, cache=disk, amp=True

## 2026-03-13 20:00:00 | Phase2恢复性判定与清理分支执行

- 判定结论：历史路径 `experiments/YOLOv11-S/baseline_full200_retry_20260311_140837/weights/last.pt` 不存在，无法恢复 140+ 轮完整状态。
- 执行分支：按规则转为“清理无效全量残留 + fresh 200轮重启”。
- 清理保留策略：仅保留 `baseline_20260310_141013`（50轮冒烟完整成果）。
- 已删除目录：
- `baseline_20260310_233358`
- `baseline_full200_fresh_20260313_122052`
- `baseline_full200_fresh_20260313_131247`
- `baseline_full200_fresh_recover_20260313_131330`

## 2026-03-13 20:00:30 | Phase2脚本重构与公平性加固

- `training/scripts/phase2_train_yolo11s.py` 已重构为唯一 Phase2 主训练脚本。
- 关键能力：
- 支持 `--resume --checkpoint` 完整断点续训（epoch/optimizer/lr状态由 Ultralytics `last.pt` 接管）。
- 自动落盘 `train.log`、`env.txt`、`hyperparams.json`、`environment_snapshot.json`、`run_summary.json`。
- 训练异常/中断自动写入 `docs/trianlog.md`，并同步更新 `docs/firstmemory.md`。
- 参数公平锁定（Phase2/3/4 对齐）：`epochs=200`、`batch=6`、`workers=0`、`cache=disk`、`device=0`、`amp=True`、`resume`按模式控制。

## 2026-03-13 20:01:00 | Phase2守护脚本精简

- `training/scripts/run_phase2_resilient.ps1` 为唯一 Phase2 守护脚本。
- 守护模式：`-Mode fresh|resume`，失败自动重试，失败详情写入 `experiments/logs/phase2_failures/`。
- 已移除冗余 Phase2 脚本：
- `run_phase2_fresh_monitor.ps1`
- `run_phase2_fresh_resilient.ps1`
- `run_phase2_monitor.ps1`
- `watch_phase2_active_progress_clean.ps1`

## 2026-03-13 20:01:20 | .gitignore精准化

- 不再整体忽略 `experiments/`，改为“忽略大文件产物 + 追踪核心文本资产”。
- 可追踪核心文件：`results.csv`、`metrics_epoch.csv`、`run_summary.json`、`args.yaml`、`hyperparams.json`、`environment_snapshot.json`、`env.txt`、`train.log`、`experiments/logs/*.json|*.md|*.csv|*.log`、`experiments/summary/*.md|*.csv`。

## 2026-03-13 20:01:40 | 本轮fresh 200启动状态

- 守护启动参数：`Mode=fresh, Epochs=200, Batch=6, Workers=0, Cache=disk, Device=0, Amp=true, MaxRestarts=500`。
- 当前活跃 run：`baseline_full200_fresh_20260313_195344`（已进入 epoch 1 训练）。

## 2026-03-13 20:02:10 | 勘误

- 19:51 与 19:53 的 `Phase2启动` 记录中 `checkpoint=` 字段来自旧逻辑自动探测展示，不代表实际使用 `--resume`。
- 已修复：fresh 模式不再写入自动探测的 checkpoint 字段，后续日志将准确反映真实训练模式。

## 2026-03-13 20:10:20 | 进度卡顿与双终端不一致排查

- 现象：出现两个训练终端，显示进度不一致，并有卡住观感。
- 根因：误开了两套守护链，导致两个 fresh run 并行训练：
- `baseline_full200_fresh_20260313_195142`
- `baseline_full200_fresh_20260313_195344`
- 处置：保留正式守护链（`MaxRestarts=500` + `--amp`）并停止误开的单次调试链（`MaxRestarts=1`）。
- 结果：当前仅保留单路训练进程（1个 powershell + 1个 python），进度来源已统一。
- 状态确认：GPU 利用率约 100%，属于正常训练而非卡死。

## 2026-03-15 00:35:00 | Phase2意外中断恢复处理

- 现象：正式 run `baseline_full200_fresh_20260313_195344` 意外中断，`run_summary.json` 记录状态为 `interrupted`。
- 断点资产核验：
- `weights/last.pt` 存在，大小约 `38.15 MB`，最后写入时间为 `2026-03-14 23:24:59`。
- 已完成训练进度约至 `epoch 107`，中断发生在 `epoch 108` 批次中段。
- 当前结果健康性检查：
- `results.csv` 到 `epoch 107` 连续完整，无 NaN、无列断裂、无异常回退。
- 最近指标稳定：`mAP50-95` 约 `0.9033~0.9037`，`precision/recall` 保持正常波动，说明训练曲线连续且结果正常。

## 2026-03-15 00:37:00 | 误开并行 run 评估与清理

- 误开 run：`baseline_full200_fresh_20260313_195142`
- 评估结论：无有效权重文件，`weights/` 为空，仅保留早期日志，不能用于 resume，也不具备论文结果价值。
- 处理：已删除该目录，避免后续再次误判为有效训练资产。

## 2026-03-15 00:40:00 | Phase2断点续训重启与验证

- 已通过守护脚本重新启动：`run_phase2_resilient.ps1 -Mode resume -Checkpoint .../baseline_full200_fresh_20260313_195344/weights/last.pt`
- 续训进程拓扑校验通过：当前仅保留 `1 个 powershell 守护 + 1 个 python 训练`。
- 续训有效性校验通过：`train.log` 已明确从 `108/200` 继续写入，而非重新从 `1/200` 开始。
- 当前结论：Phase2 已恢复为正常续训状态，可继续向 `200 epochs` 收敛。
## 2026-03-14 23:26:42 | Phase2中断

- run_id=baseline_full200_fresh_20260313_195344
- Training interrupted by user/terminal.
## 2026-03-15 00:22:04 | Phase2 watchdog start

- mode=resume
- checkpoint=D:/cyd/Desktop/yolo_web-main/experiments/YOLOv11-S/baseline_full200_fresh_20260313_195344/weights/last.pt
- epochs=200, batch=6, workers=0, cache=disk, device=0

## 2026-03-15 00:22:17 | Phase2启动

- run_id=baseline_full200_fresh_20260313_195344
- resume=True
- checkpoint=D:\cyd\Desktop\yolo_web-main\experiments\YOLOv11-S\baseline_full200_fresh_20260313_195344\weights\last.pt
- epochs=200, batch=6, workers=0, cache=disk, amp=True
## 2026-03-15 19:21:50 | Phase2异常

- run_id=baseline_full200_fresh_20260313_195344
- error=OpenCV(4.13.0) D:\a\opencv-python\opencv-python\opencv\modules\core\src\alloc.cpp:73: error: (-4:Insufficient memory) Failed to allocate 72000000 bytes in function 'cv::OutOfMemoryError'

- traceback:
- Traceback (most recent call last):
  File "D:\cyd\Desktop\yolo_web-main\training\scripts\phase2_train_yolo11s.py", line 265, in main
    train_results = model.train(**train_kwargs)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\ultralytics\engine\model.py", line 774, in train
    self.trainer.train()
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\ultralytics\engine\trainer.py", line 244, in train
    self._do_train()
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\ultralytics\engine\trainer.py", line 405, in _do_train
    for i, batch in pbar:
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\ultralytics\utils\tqdm.py", line 350, in __iter__
    for item in self.iterable:
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\ultralytics\data\build.py", line 76, in __iter__
    yield next(self.iterator)
          ^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\torch\utils\data\dataloader.py", line 732, in __next__
    data = self._next_data()
           ^^^^^^^^^^^^^^^^^
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\torch\utils\data\dataloader.py", line 788, in _next_data
    data = self._dataset_fetcher.fetch(index)  # may raise StopIteration
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\torch\utils\data\_utils\fetch.py", line 52, in fetch
    data = [self.dataset[idx] for idx in possibly_batched_index]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\torch\utils\data\_utils\fetch.py", line 52, in <listcomp>
    data = [self.dataset[idx] for idx in possibly_batched_index]
            ~~~~~~~~~~~~^^^^^
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\ultralytics\data\base.py", line 376, in __getitem__
    return self.transforms(self.get_image_and_label(index))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\ultralytics\data\base.py", line 389, in get_image_and_label
    label["img"], label["ori_shape"], label["resized_shape"] = self.load_image(index)
                                                               ^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\ultralytics\data\base.py", line 235, in load_image
    im = imread(f, flags=self.cv2_flag)  # BGR
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\ultralytics\utils\patches.py", line 42, in imread
    im = cv2.imdecode(file_bytes, flags)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
cv2.error: OpenCV(4.13.0) D:\a\opencv-python\opencv-python\opencv\modules\core\src\alloc.cpp:73: error: (-4:Insufficient memory) Failed to allocate 72000000 bytes in function 'cv::OutOfMemoryError'


## 2026-03-15 19:21:54 | Phase2 watchdog retry

- attempt=1
- exit_code=2
- failure_file=D:\cyd\Desktop\yolo_web-main\experiments\logs\phase2_failures\attempt_1_20260315_192154.log

## 2026-03-15 19:22:31 | Phase2启动

- run_id=baseline_full200_fresh_20260313_195344
- resume=True
- checkpoint=D:\cyd\Desktop\yolo_web-main\experiments\YOLOv11-S\baseline_full200_fresh_20260313_195344\weights\last.pt
- epochs=200, batch=6, workers=0, cache=disk, amp=True
## 2026-03-15 19:31:23 | Phase2异常

- run_id=baseline_full200_fresh_20260313_195344
- error=OpenCV(4.13.0) D:\a\opencv-python\opencv-python\opencv\modules\core\src\alloc.cpp:73: error: (-4:Insufficient memory) Failed to allocate 72000000 bytes in function 'cv::OutOfMemoryError'

- traceback:
- Traceback (most recent call last):
  File "D:\cyd\Desktop\yolo_web-main\training\scripts\phase2_train_yolo11s.py", line 265, in main
    train_results = model.train(**train_kwargs)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\ultralytics\engine\model.py", line 774, in train
    self.trainer.train()
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\ultralytics\engine\trainer.py", line 244, in train
    self._do_train()
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\ultralytics\engine\trainer.py", line 405, in _do_train
    for i, batch in pbar:
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\ultralytics\utils\tqdm.py", line 350, in __iter__
    for item in self.iterable:
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\ultralytics\data\build.py", line 76, in __iter__
    yield next(self.iterator)
          ^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\torch\utils\data\dataloader.py", line 732, in __next__
    data = self._next_data()
           ^^^^^^^^^^^^^^^^^
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\torch\utils\data\dataloader.py", line 788, in _next_data
    data = self._dataset_fetcher.fetch(index)  # may raise StopIteration
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\torch\utils\data\_utils\fetch.py", line 52, in fetch
    data = [self.dataset[idx] for idx in possibly_batched_index]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\torch\utils\data\_utils\fetch.py", line 52, in <listcomp>
    data = [self.dataset[idx] for idx in possibly_batched_index]
            ~~~~~~~~~~~~^^^^^
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\ultralytics\data\base.py", line 376, in __getitem__
    return self.transforms(self.get_image_and_label(index))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\ultralytics\data\base.py", line 389, in get_image_and_label
    label["img"], label["ori_shape"], label["resized_shape"] = self.load_image(index)
                                                               ^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\ultralytics\data\base.py", line 235, in load_image
    im = imread(f, flags=self.cv2_flag)  # BGR
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\ultralytics\utils\patches.py", line 42, in imread
    im = cv2.imdecode(file_bytes, flags)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
cv2.error: OpenCV(4.13.0) D:\a\opencv-python\opencv-python\opencv\modules\core\src\alloc.cpp:73: error: (-4:Insufficient memory) Failed to allocate 72000000 bytes in function 'cv::OutOfMemoryError'


## 2026-03-15 19:31:26 | Phase2 watchdog retry

- attempt=2
- exit_code=2
- failure_file=D:\cyd\Desktop\yolo_web-main\experiments\logs\phase2_failures\attempt_2_20260315_193126.log

## 2026-03-15 19:31:57 | Phase2启动

- run_id=baseline_full200_fresh_20260313_195344
- resume=True
- checkpoint=D:\cyd\Desktop\yolo_web-main\experiments\YOLOv11-S\baseline_full200_fresh_20260313_195344\weights\last.pt
- epochs=200, batch=6, workers=0, cache=disk, amp=True
## 2026-03-15 19:32:37 | Phase2异常

- run_id=baseline_full200_fresh_20260313_195344
- error=CUDA error: unknown error
Search for `cudaErrorUnknown' in https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__TYPES.html for more information.
CUDA kernel errors might be asynchronously reported at some other API call, so the stacktrace below might be incorrect.
For debugging consider passing CUDA_LAUNCH_BLOCKING=1
Compile with `TORCH_USE_CUDA_DSA` to enable device-side assertions.

- traceback:
- Traceback (most recent call last):
  File "D:\cyd\Desktop\yolo_web-main\training\scripts\phase2_train_yolo11s.py", line 265, in main
    train_results = model.train(**train_kwargs)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\ultralytics\engine\model.py", line 774, in train
    self.trainer.train()
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\ultralytics\engine\trainer.py", line 244, in train
    self._do_train()
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\ultralytics\engine\trainer.py", line 442, in _do_train
    self.optimizer_step()
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\ultralytics\engine\trainer.py", line 692, in optimizer_step
    self.scaler.unscale_(self.optimizer)  # unscale gradients
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\torch\amp\grad_scaler.py", line 337, in unscale_
    self._scale.double().reciprocal().float()
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
torch.AcceleratorError: CUDA error: unknown error
Search for `cudaErrorUnknown' in https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__TYPES.html for more information.
CUDA kernel errors might be asynchronously reported at some other API call, so the stacktrace below might be incorrect.
For debugging consider passing CUDA_LAUNCH_BLOCKING=1
Compile with `TORCH_USE_CUDA_DSA` to enable device-side assertions.


## 2026-03-15 19:33:15 | Phase2 watchdog retry

- attempt=3
- exit_code=2
- failure_file=D:\cyd\Desktop\yolo_web-main\experiments\logs\phase2_failures\attempt_3_20260315_193315.log

## 2026-03-15 19:33:45 | Phase2启动

- run_id=baseline_full200_fresh_20260313_195344
- resume=True
- checkpoint=D:\cyd\Desktop\yolo_web-main\experiments\YOLOv11-S\baseline_full200_fresh_20260313_195344\weights\last.pt
- epochs=200, batch=6, workers=0, cache=disk, amp=True
## 2026-03-15 19:34:16 | Phase2异常

- run_id=baseline_full200_fresh_20260313_195344
- error=bad allocation
- traceback:
- Traceback (most recent call last):
  File "D:\cyd\Desktop\yolo_web-main\training\scripts\phase2_train_yolo11s.py", line 265, in main
    train_results = model.train(**train_kwargs)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\ultralytics\engine\model.py", line 774, in train
    self.trainer.train()
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\ultralytics\engine\trainer.py", line 244, in train
    self._do_train()
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\ultralytics\engine\trainer.py", line 440, in _do_train
    self.scaler.scale(self.loss).backward()
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\torch\_tensor.py", line 625, in backward
    torch.autograd.backward(
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\torch\autograd\__init__.py", line 354, in backward
    _engine_run_backward(
  File "C:\Users\cyd\miniconda3\envs\weedweb_detection\Lib\site-packages\torch\autograd\graph.py", line 841, in _engine_run_backward
    return Variable._execution_engine.run_backward(  # Calls into the C++ engine to run the backward pass
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
RuntimeError: bad allocation

## 2026-03-15 19:34:18 | Phase2 watchdog retry

- attempt=4
- exit_code=2
- failure_file=D:\cyd\Desktop\yolo_web-main\experiments\logs\phase2_failures\attempt_4_20260315_193418.log

## 2026-03-15 19:34:47 | Phase2启动

- run_id=baseline_full200_fresh_20260313_195344
- resume=True
- checkpoint=D:\cyd\Desktop\yolo_web-main\experiments\YOLOv11-S\baseline_full200_fresh_20260313_195344\weights\last.pt
- epochs=200, batch=6, workers=0, cache=disk, amp=True
## 2026-03-15 19:52:42 | Phase2 watchdog start

- mode=resume
- checkpoint=D:/cyd/Desktop/yolo_web-main/experiments/YOLOv11-S/baseline_full200_fresh_20260313_195344/weights/last.pt
- epochs=200, batch=6, workers=0, cache=disk, device=0

## 2026-03-15 19:53:05 | Phase2启动

- run_id=baseline_full200_fresh_20260313_195344
- resume=True
- checkpoint=D:\cyd\Desktop\yolo_web-main\experiments\YOLOv11-S\baseline_full200_fresh_20260313_195344\weights\last.pt
- epochs=200, batch=6, workers=0, cache=disk, amp=True
## 2026-03-15 23:42:15 | Phase2完成

- run_id=baseline_full200_fresh_20260313_195344
- results_csv=D:\cyd\Desktop\yolo_web-main\experiments\YOLOv11-S\baseline_full200_fresh_20260313_195344\results.csv
- train_log=D:\cyd\Desktop\yolo_web-main\experiments\YOLOv11-S\baseline_full200_fresh_20260313_195344\train.log
## 2026-03-15 23:42:17 | Phase2 watchdog completed

- attempt=1
- exit_code=0

## 2026-03-15 23:49:04 | Phase3 watchdog start

- mode=fresh
- checkpoint=
- epochs=200, batch=6, workers=1, cache=disk, device=0

## 2026-03-15 23:49:19 | Phase3启动

- run_id=mbv3_full200_fresh_20260315_234917
- resume=False
- checkpoint=N/A
- epochs=200, batch=6, workers=1, cache=disk, amp=True
