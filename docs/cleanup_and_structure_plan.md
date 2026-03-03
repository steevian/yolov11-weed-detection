# YOLOv11 杂草检测项目清理与结构标准化方案（不破坏现有功能）

## 一、统一结论

- 运行中的真实写入目录在 `yolo_weed_detection_flask` 内部：`uploads`、`results`、`runs`、`weights`。
- 根目录同名目录可判定为历史遗留（可清理或归档后清理）。
- 资源目录应统一放在 Flask 内部，原因是后端代码路径锚定到 `main.py` 所在目录。

## 二、可安全删除清单（建议先归档再删）

1. `files/`
   - 历史临时视频文件，当前前后端主链路不引用该目录。
2. `uploads/`（根目录）
   - 与 Flask 内部 `uploads/` 重复，当前运行写入点不在根目录。
3. `results/`（根目录）
   - 与 Flask 内部 `results/` 重复，当前运行写入点不在根目录。
4. `runs/`（根目录）
   - 与 Flask 内部 `runs/` 重复，当前运行写入点不在根目录。
5. `weights/`（根目录）
   - 空目录，模型实际在 `yolo_weed_detection_flask/weights/weed_best.pt`。
6. `weed_detection.db`（根目录）
   - 历史数据库副本；当前使用的是 `yolo_weed_detection_flask/weed_detection.db`。

## 三、最终采用目录结构（轻量、可维护）

```text
yolo_web-main/
├─ yolo_weed_detection_flask/
│  ├─ main.py
│  ├─ user_manager.py
│  ├─ core/
│  │  ├─ settings.py
│  │  └─ database.py
│  ├─ uploads/
│  │  ├─ avatar/
│  │  └─ detect/
│  │     ├─ images/
│  │     └─ videos/
│  ├─ results/
│  │  ├─ images/
│  │  └─ videos/
│  ├─ runs/
│  │  ├─ images/
│  │  └─ video/
│  ├─ weights/
│  │  └─ weed_best.pt
│  ├─ predict/
│  └─ weed_detection.db
├─ yolo_weed_detection_vue/
├─ docs/
├─ start_local.ps1
├─ start_local.bat
└─ yolo_weed_detection_springboot.zip
```

> 注：本方案不做 `storage/*` 重映射，直接在现有 `uploads` 下拆分 `avatar` 与 `detect`，改动最小且风险最低。

## 四、逐文件/逐目录迁移步骤（零停机风险版）

### Step 0：创建归档目录

```powershell
Set-Location -LiteralPath "D:/cyd/Desktop/yolo_web-main"
New-Item -ItemType Directory -Force -Path "./_legacy_archive" | Out-Null
```

### Step 1：先归档根目录遗留文件（不直接删）

```powershell
$items = @("files","uploads","results","runs","weights","weed_detection.db")
foreach ($i in $items) {
  if (Test-Path "./$i") {
    Move-Item -LiteralPath "./$i" -Destination "./_legacy_archive/$i" -Force
  }
}
```

### Step 2：核验系统功能（必须）

- 启动后端与前端，验证：图片检测、视频检测、摄像头检测、登录注册、头像上传、记录增删查。
- 若全部正常，说明根目录重复目录可永久删除。

### Step 2.5：目录拆分核验（本次结构调整新增）

- 新上传头像应落在 `yolo_weed_detection_flask/uploads/avatar/`。
- 新上传检测图片应落在 `yolo_weed_detection_flask/uploads/detect/images/`。
- 新上传检测视频应落在 `yolo_weed_detection_flask/uploads/detect/videos/`。
- 历史 `yolo_weed_detection_flask/uploads/images` 中旧文件可保留（兼容历史URL），后续可按需离线整理。

### Step 3：删除归档（可选，建议延后1-3天）

```powershell
# 确认无回滚需求后再执行
Remove-Item -LiteralPath "./_legacy_archive" -Recurse -Force
```

## 五、若要实现“头像单独目录”且不影响功能

已完成：

1. 新增头像上传接口：`/flask/upload/avatar`
2. 前端个人中心与用户管理上传 action 已切换到该接口
3. 检测上传保留原接口 `/flask/upload`，但落盘目录改为 `uploads/detect/images|videos`

说明：默认头像历史路径仍可继续使用，不影响当前登录与用户管理功能。
