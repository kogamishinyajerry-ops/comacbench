#!/usr/bin/env python3
"""生成 benchmark 覆盖评估雷达图（数据来源：registry.yaml + results/* 汇总，2026-08-21）。"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np

OUT = os.path.dirname(os.path.abspath(__file__))

# ---- 中文字体（macOS 常见字体逐个探测） ----
for cand in ["PingFang SC", "Hiragino Sans GB", "Arial Unicode MS", "STHeiti", "Heiti TC"]:
    try:
        font_manager.findfont(cand, fallback_to_default=False)
        plt.rcParams["font.family"] = cand
        break
    except Exception:
        continue
plt.rcParams["axes.unicode_minus"] = False


def radar(ax, labels, series, title):
    n = len(labels)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    for name, vals, color, fill in series:
        v = vals + vals[:1]
        ax.plot(angles, v, "o-", linewidth=2, label=name, color=color, markersize=4)
        if fill:
            ax.fill(angles, v, alpha=0.18, color=color)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylim(0, 1.0)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"], fontsize=7, color="#888")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.set_title(title, fontsize=13, pad=22)
    ax.legend(loc="upper right", bbox_to_anchor=(1.32, 1.12), fontsize=9)


# ============ 图 1：九维度评测能力雷达 ============
labels1 = ["航空知识\nknowledge\n(cfdquery/aeroengqa)", "科学编程\ncoding\n(scicode/cfdcode)", "CAD/几何\ncad_geometry\n(cadgen/openvsp)",
           "CFD\ncfd\n(superwing/hilift/foam)", "结构\nstructures\n(simjeb/engdesign)", "动力\npropulsion\n(pycycle)",
           "飞控\nflight_control\n(gtm)", "总体/MDO\nmdo_design\n(aviary)", "鲁棒审计\nrobustness_audit\n(横切)"]
# 覆盖度 = 该维度 registry 内 integrated 数 / 全部条目数（integrated+staged+proposed+paused-env+deferred）
coverage = [0.50, 1.00, 0.00, 0.60, 0.00, 1.00, 0.00, 0.33, 0.60]
# 基线可得 = 维度内已有 integrated 基准且 GLM-4.6 + MiniMax-M3 双基线落盘（含 ML/oracle 参照）
baseline = [1.00, 1.00, 0.00, 1.00, 0.00, 1.00, 0.00, 1.00, 0.60]

fig1, ax1 = plt.subplots(figsize=(9.5, 8.5), subplot_kw=dict(polar=True))
radar(ax1, labels1, [
    ("维度覆盖度（已集成/在册基准数）", coverage, "#1f77b4", True),
    ("双模型基线可得性（GLM-4.6+M3 落盘）", baseline, "#d62728", True),
], "九维度评测能力雷达（v0.1，2026-08-21）\n15/38 基准 integrated · 2119 任务 · 双基线全覆盖")
fig1.tight_layout()
fig1.savefig(os.path.join(OUT, "radar_nine_dim.png"), dpi=160, bbox_inches="tight")
plt.close(fig1)

# ============ 图 2：评测体系（harness）能力雷达 ============
labels2 = ["公共可比层\n(10 基准·双基线·加强测试)", "工程可执行层\n(5 基准端到端可运行)", "受控隐藏层\n(生成器+划分纪律)",
           "多模态评测\n(VLM 通道)", "Adapter 类型\n(4/5 接线)", "环境覆盖\n(4 类 live·商业栈缺)",
           "判分自检\n(oracle 11/15)", "可复现审计\n(manifest/seed/sha256)"]
harness = [0.95, 0.65, 0.30, 0.05, 0.80, 0.50, 0.73, 0.90]

fig2, ax2 = plt.subplots(figsize=(9.0, 8.5), subplot_kw=dict(polar=True))
radar(ax2, labels2, [
    ("当前能力（0-1，口径见 README.md）", harness, "#2ca02c", True),
], "评测体系能力雷达：三层架构 × 判分 × 环境（2026-08-21）")
fig2.tight_layout()
fig2.savefig(os.path.join(OUT, "radar_harness.png"), dpi=160, bbox_inches="tight")
plt.close(fig2)

print("OK:", OUT)
