# yolov11-weed-detection

本项目是一个基于YOLO的杂草检测系统，包含前端（Vue3+Vite）和后端（Flask）两部分，支持本地运行和云端部署（后续）。目前仍在持续更新，这是一个简单的readme。

## 项目特点
- 支持图片和视频的杂草检测与结果展示
- 前端采用Vue3 + Vite。我觉得很有意思的一个部分是我的前端登录页面，借鉴了一些其他GitHub项目和我在流媒体上看到的创意，如果你有兴趣，可以先查看我的根目录下的Login.html，这个可以大致还原登陆页面。
- 后端基于Flask，集成YOLO模型推理
- 持续维护与优化中

## 目录结构
- yolo_weed_detection_vue/  前端源码（Vue3）
- yolo_weed_detection_flask/  后端源码（Flask）

## 快速开始
1. 克隆本仓库到本地
2. 分别进入前端和后端目录，安装依赖
3. 启动后端服务（Flask）
4. 启动前端服务（Vite）

Tips：
requirements.txt在flask目录下。

---

如有建议或问题，欢迎提交 issue。

版权所有 © 2026 Yudong Chen
