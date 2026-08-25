#!/usr/bin/env python3
"""生成 benchmark 覆盖评估雷达图（数据时点 2026-08-25，接 2026-08-21-coverage-assessment）。

数据来源：
- registry/registry.yaml（39 条目）+ comac_registry 实时状态
- tasks/*/ 任务 YAML 实数（19 integrated = 2403；tasks/.foam_tail 20 题在制未转正）
- results/*/ provider 落盘实数（oracle 15/19；双基线 19/19）
- results/nine-dim-{baseline,increment}*.md、harness-eval-2026-08-24.md、harness-lineage-2026-08-25.md

变更（vs 2026-08-21 版）：
- 图 1：flight_control 0→1.00（gtm v1 8-22 解零 + gtm_hard 8-23 区分带）；加 08-22 时点参照线
- 图 2：新增第 9 轴「Harness 臂评测」（v0.3 四臂矩阵 + 谱系化 4/5 + arm_router）；
  工程可执行层 6→8 基准（+gtm×2 MATLAB）；环境覆盖 4→5 类 live（+matlab）；
  判分自检 13/17→15/19；可复现审计 +git init
"""
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
    for name, vals, color, fill, ls in series:
        v = vals + vals[:1]
        ax.plot(angles, v, "o-", linestyle=ls or "-", linewidth=2, label=name, color=color, markersize=4)
        if fill:
            ax.fill(angles, v, alpha=0.18, color=color)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(0, 1.0)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"], fontsize=7, color="#888")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.set_title(title, fontsize=12.5, pad=24)
    ax.legend(loc="upper right", bbox_to_anchor=(1.34, 1.12), fontsize=8.5)


# ============ 图 1：九维度评测能力雷达 ============
labels1 = ["航空知识\nknowledge\n(cfdquery/aeroengqa/mechvqa)", "科学编程\ncoding\n(scicode/cfdcode)", "CAD/几何\ncad_geometry\n(cadgen/openvsp)",
           "CFD\ncfd\n(superwing/hilift/foam)", "结构\nstructures\n(calculix/simjeb)", "动力\npropulsion\n(pycycle 28题)",
           "飞控\nflight_control\n(gtm v1+hard)", "总体/MDO\nmdo_design\n(aviary 27题)", "鲁棒审计\nrobustness_audit\n(横切)",
           "工程办公\noffice_productivity\n(engtable 19题)"]
# 覆盖度 = 维度内 integrated 基准数 / registry 在册基准数（integrated+proposed+paused-env+deferred）
# 2026-08-24 structures 解零更新：calculix.fea_basic integrated（simjeb/engdesign 仍 proposed）
# —— structures 0.00→0.33，九维全部有数（全景闭合）
# 2026-08-25 窄路 A 落地：cadbench_seldon.sketch_lite integrated（2D 草图子轴首批 15 题）
# —— cad_geometry 在册 4（cadgen+sketch_lite integrated / openvsp paused / seldon.hard proposed）覆盖度 0.33→0.50
coverage = [0.75, 1.00, 0.50, 0.60, 0.33, 1.00, 1.00, 0.33, 0.60, 1.00]
coverage_prev = [0.75, 1.00, 0.50, 0.60, 0.00, 1.00, 1.00, 0.33, 0.60, 0.00]  # 08-24 上午时点（办公维尚不存在）
# 基线可得 = 维度内 integrated 基准双基线落盘（M3+GLM 系；mechvqa=双 VLM；ccx=固定对 5.3+M3）
baseline = [1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 0.60, 1.00]

fig1, ax1 = plt.subplots(figsize=(10.0, 9.0), subplot_kw=dict(polar=True))
radar(ax1, labels1, [
    ("覆盖度 2026-08-24（已集成/在册）", coverage, "#1f77b4", True, ""),
    ("双基线可得性（M3+GLM 系落盘）", baseline, "#d62728", True, ""),
    ("覆盖度 08-24 上午时点（参照）", coverage_prev, "#999999", False, "--"),
], "评测能力雷达·十维（v0.4，2026-08-25 办公维落地）\n22/43 基准 integrated · 2458 任务 · 集成项双基线全覆盖 · 10/10 维有数")
fig1.tight_layout()
fig1.savefig(os.path.join(OUT, "radar_nine_dim.png"), dpi=160, bbox_inches="tight")
plt.close(fig1)

# ============ 图 2：评测体系（harness）能力雷达 ============
labels2 = ["公共可比层\n(11 基准·双基线·加强测试)", "工程可执行层\n(10 基准端到端·含MATLAB/ccx)", "受控隐藏层\n(生成器+划分纪律)",
           "多模态评测\n(VLM 通道+判分·单厂商)", "Adapter 类型\n(5/5 接线)", "环境覆盖\n(6 类 live·商业CFD/FEA缺)",
           "判分自检\n(oracle 16/20)", "可复现审计\n(manifest/seed/sha256/git)",
           "Harness 臂评测\n(H0-H3·谱系4/5·路由)"]
# 2026-08-24 晚更新：工程可执行 8→9 基准（+calculix.fea_basic）→0.80→0.82；
# 环境 5→6 类 live（+calculix_native）→0.56→0.62；判分自检 15/19→16/20→0.79→0.80
harness = [0.95, 0.82, 0.30, 0.55, 1.00, 0.62, 0.80, 0.92, 0.75]
harness_prev = [0.95, 0.80, 0.30, 0.55, 1.00, 0.56, 0.79, 0.92, 0.75]  # 08-24 上午时点

fig2, ax2 = plt.subplots(figsize=(9.6, 9.0), subplot_kw=dict(polar=True))
radar(ax2, labels2, [
    ("当前能力（2026-08-24 晚，口径见 README.md）", harness, "#2ca02c", True, ""),
    ("08-24 上午时点（参照）", harness_prev, "#999999", False, "--"),
], "评测体系能力雷达：三层架构 × 判分 × 环境 × harness（2026-08-24 晚更新）")
fig2.tight_layout()
fig2.savefig(os.path.join(OUT, "radar_harness.png"), dpi=160, bbox_inches="tight")
plt.close(fig2)

print("OK:", OUT)
