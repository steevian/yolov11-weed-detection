# 归档说明（2026-03-28）

已归档目录：
- experiments -> exp0/archive_legacy_20260328/experiments
- runs -> exp0/archive_legacy_20260328/runs

保留原位目录：
- training（未归档）

原因：
- training 下存在大量可执行脚本与 .vscode 任务、绝对路径依赖；直接迁移会造成较高的运行中断风险。
- 旧实验产物 experiments 与根目录 runs 已退出主线，迁移到 exp0 风险可接受。

潜在影响：
- 历史脚本/文档中引用 experiments、runs 原路径将失效；若需回看，需改为 exp0/archive_legacy_20260328 下对应路径。
