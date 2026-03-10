"""Phase 5: generate markdown comparison/report artifacts for thesis."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Generate thesis markdown report artifacts")
    parser.add_argument(
        "--metrics-csv",
        type=Path,
        default=repo_root / "experiments" / "summary" / "comparison_metrics.csv",
    )
    parser.add_argument(
        "--summary-dir",
        type=Path,
        default=repo_root / "experiments" / "summary",
    )
    return parser.parse_args()


def markdown_table(df: pd.DataFrame) -> str:
    return df.to_markdown(index=False)


def main() -> int:
    args = parse_args()
    args.summary_dir.mkdir(parents=True, exist_ok=True)
    if not args.metrics_csv.exists():
        print(f"[ERROR] metrics csv not found: {args.metrics_csv}")
        return 1

    df = pd.read_csv(args.metrics_csv)

    cmp_md = args.summary_dir / "comparison_metrics.md"
    report_md = args.summary_dir / "实验汇总报告.md"
    fig_index_md = args.summary_dir / "figures_index.md"

    cmp_lines = [
        "# Comparison Metrics",
        "",
        "统一测试协议：test(2023), batch=1, warmup=10, iters=100, imgsz=640。",
        "",
        markdown_table(df),
        "",
    ]
    cmp_md.write_text("\n".join(cmp_lines), encoding="utf-8")

    best_map = df.sort_values("map50", ascending=False).iloc[0]
    best_fps = df.sort_values("fps", ascending=False).iloc[0]

    report_lines = [
        "# 实验汇总报告",
        "",
        "## 1. 实验设置",
        "- 数据集：3SeasonWeedDet10，2021+2022训练/验证，2023测试",
        "- 输入尺寸：640",
        "- 训练超参：epochs=200, batch=8, lr0=0.01, optimizer=SGD",
        "- 对比模型：YOLOv11-S、YOLOv11-S-MBV3、YOLOv11-S-MBV3-ECA",
        "",
        "## 2. 结果对比",
        markdown_table(df),
        "",
        "## 3. 自动结论",
        f"- mAP@0.5 最优模型：{best_map['model']} ({best_map['map50']:.4f})",
        f"- FPS 最优模型：{best_fps['model']} ({best_fps['fps']:.2f})",
        "- 请结合参数量/FLOPs与检测效果做论文中的综合权衡讨论。",
        "",
    ]
    report_md.write_text("\n".join(report_lines), encoding="utf-8")

    figure_lines = [
        "# Figures Index",
        "",
        "- 训练曲线：`experiments/**/plots/metrics_curve_1280x720.png`",
        "- 混淆矩阵：`experiments/**/plots/confusion_matrix.png`",
        "- 可视化样例：`experiments/summary/samples/`",
        "- 指标表：`experiments/summary/comparison_metrics.md`",
        "",
    ]
    fig_index_md.write_text("\n".join(figure_lines), encoding="utf-8")

    print("[DONE] phase5_generate_report")
    print(f"comparison: {cmp_md}")
    print(f"report: {report_md}")
    print(f"figures index: {fig_index_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
