"""gen_tasks_aviary.py — 自建 aviary.transport_mission 任务集（M3；2026-08-21 扩题 8→27）。

产出（幂等，--check 校验；参考值由 gold 脚本在本机预计算锁定）：
  data/aviary/transport_mission/base/aircraft_for_bench_GwGm.csv   基准模型（v1.0.1 venv 内拷贝）
  data/aviary/transport_mission/derived/<name>.csv                  参数化派生模型
  data/aviary/transport_mission/gold/<tid>.py                       gold 解脚本
  data/aviary/transport_mission/references/<tid>.json               预计算参考（tol 锁定）
  data/aviary/transport_mission/hidden/{generator.py,answers.b64,README.md}
  tasks/aviary.transport_mission/<tid>.yaml + .md

任务协议（simulation_agent / aviary_mission，分析模式 run_driver=False）：
  gate   = 脚本跑通 + result.json 可解析（missing_output）
  physics = 逐数值字段对参考相对误差（|Δ|/|ref| ≤ rel_tol 计 1）取均值
  requirements = result.json 必填键存在率
  objective/robustness = N/A（静态任务，权重 0）
模型输出契约：单个 ```python 脚本，在 cwd 写出 result.json（键与容差在题面声明）。

2026-08-21 扩题与修复（append-only + gold 路径可移植性修复）：
  - 新增 19 题：任务分析 range×mach 网格 10 + 总重权衡 2 + 总重扫描敏感度 1 +
    燃油比 2 + 航程扫描 2 + 模型修复 2；全部 gold 在收敛域内真实跑通；
  - 存量 8 题的 YAML/MD/references/派生 CSV 逐字节冻结（已存在即不重写）；
    gold 脚本全量重写为路径可移植版（不再内嵌仓库绝对路径——建集日后仓库搬迁使
    旧绝对路径失效；修复后旧 gold 逐一重跑对锁定 references 等效验证，见 PROVENANCE）；
  - 【解释器变更】_venv_python() 由 .venv 改指 .venv-aviary/bin/python
    （.venv 2026-08-21 起为 pycycle 钉子栈，不含 aviary；.venv-aviary = aviary 1.0.1 +
    openmdao 3.45.0 + numpy 2.5.2，与 2026-08-19 建集环境同代）。本生成器须用
    .venv-aviary/bin/python 运行（顶部 import aviary 定位基准 CSV）；
  - 隐藏动态（hidden/）冻结：answers.b64 已在库即不重算；
  - seed / REL_TOL / ASSETS_REVISION / 判分口径均不变。

已知模型口径（如实记录，沿用存量 8 题同一事实）：two_dof GwGm 分析模式
（run_driver=False）下燃油对 range/mach 不敏感（巡航时长冻结于 initial_guesses），
仅 design:gross_mass 真实影响燃油——range/mach 类题与存量 T1-T3 同口径（判分仍
对各自锁定参考），真正非退化族为总重权衡/扫描/修复。详见 PROVENANCE 扩题节。

隐藏动态（评审件）：generator.py 以固定种子采样 (range, mach, gross_mass)，
答案由 gold 预计算后 base64 隔离存 answers.b64（不入明文库；泄漏监控见 scoring §5）。
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import random
import re
import subprocess
import sys
import tempfile
import warnings
from copy import deepcopy
from pathlib import Path

import yaml

warnings.filterwarnings("ignore")

BENCH = Path(__file__).resolve().parent.parent
DATA = BENCH / "data/aviary/transport_mission"
TASKS_DIR = BENCH / "tasks/aviary.transport_mission"
ASSETS_REVISION = "aviary-mission@selfbuilt-2026-08-19+aviary1.0.1"

REL_TOL = 0.01  # 数值判分相对容差（分析模式确定性求解，1% 覆盖模型口径差）

# ---------------------------------------------------------------- 基础模型

BASE_CSV_NAME = "aircraft_for_bench_GwGm.csv"


def _venv_python() -> str:
    # 2026-08-21：.venv 已重建为 pycycle 钉子栈（无 aviary），aviary 栈在 .venv-aviary
    return str(BENCH / ".venv-aviary/bin/python")


def _modify_csv(src: str, edits: dict[str, str]) -> str:
    """按 key 改 value（key 形如 'aircraft:design:range'）。"""
    out = []
    hit = set()
    for line in src.splitlines():
        key = line.split(",")[0].strip()
        if key in edits:
            parts = line.split(",")
            parts[1] = edits[key]
            line = ",".join(parts)
            hit.add(key)
        out.append(line)
    missing = set(edits) - hit
    if missing:
        raise ValueError(f"CSV 未找到键: {missing}")
    return "\n".join(out) + "\n"


# gold 头（2026-08-21 起路径可移植：CSV 以 data/aviary/transport_mission 相对定位，
# 锚点 = gold 文件目录（仓库内）/ cwd / aviary 包位置（沙箱内 venv 装在仓库下），
# 逐级上溯定位仓库根——不再内嵌仓库绝对路径）
_GOLD_HEADER = '''"""gold 解（aviary 分析模式）。判分参考预计算用；模型不可见。"""
import json
import os
import warnings
from copy import deepcopy
from pathlib import Path

warnings.filterwarnings("ignore")

from aviary.interface.run_aviary import run_aviary
from aviary.models.missions.two_dof_default import phase_info
from aviary.variable_info.variables import Mission


def _tm_root() -> Path:
    """定位 data/aviary/transport_mission（路径可移植：不内嵌仓库绝对路径）。"""
    cands = [Path(__file__).resolve().parent, Path.cwd()]
    try:
        import aviary as _av
        cands.append(Path(_av.__file__).resolve().parent)
    except Exception:
        pass
    for _c in cands:
        for _anc in [_c] + list(_c.parents)[:10]:
            if (_anc / "data" / "aviary" / "transport_mission").is_dir():
                return _anc / "data" / "aviary" / "transport_mission"
    raise RuntimeError("data/aviary/transport_mission not found "
                       "(anchors: __file__ / cwd / aviary-package)")


def _p(rel: str) -> str:
    return str(_tm_root() / rel)


def solve(csv_path: str, mach: float):
    pi = deepcopy(phase_info)
    pi["cruise"]["user_options"]["mach_cruise"] = mach
    prob = run_aviary(csv_path, pi, optimizer="SLSQP", run_driver=False,
                      verbosity=0, make_plots=False)
    fuel = float(prob.get_val(Mission.TOTAL_FUEL_MASS, units="lbm")[0])
    final = float(prob.get_val(Mission.FINAL_MASS, units="lbm")[0])
    return {"fuel_burn_lbm": fuel, "final_mass_lbm": final}
'''


def _mk_derived(base_csv: str, edits: dict[str, str]) -> str:
    return _modify_csv(base_csv, edits)


# ---------------------------------------------------------------- 任务定义

def task_defs(base_csv: str, derived_dir: Path) -> list[dict]:
    """返回任务描述列表（含派生 CSV 落盘与 gold 脚本内容）。

    derived() 写派生 CSV（幂等：同 base 同 edits 字节不变），返回
    (绝对路径, 仓库相对 data/aviary/transport_mission 路径) 二元组。
    """
    T = []

    def derived(name: str, edits: dict[str, str]) -> tuple[str, str]:
        p = derived_dir / f"{name}.csv"
        p.write_text(_mk_derived(base_csv, edits), encoding="utf-8")
        rel = f"derived/{name}.csv"
        return str(p.resolve()), rel

    # ---- T1-T3 任务分析：range × mach（存量，gold 重渲染为可移植路径）----
    for tid, rng, mach in (("av_range_3000_m80", 3000, 0.80),
                           ("av_range_2500_m75", 2500, 0.75),
                           ("av_range_3200_m785", 3200, 0.785)):
        rel_pair = derived(tid, {"aircraft:design:range": str(rng)})
        T.append({
            "tid": tid, "kind": "analysis", "csv": rel_pair[0], "csv_rel": rel_pair[1],
            "mach": mach,
            "keys": ["fuel_burn_lbm", "final_mass_lbm"],
            "title": f"任务分析：航程 {rng} NM、巡航马赫 {mach}",
            "ask": (f"Using the aircraft model CSV provided and Aviary (installed), run a "
                    f"forward mission analysis (run_driver=False) at cruise Mach {mach}. "
                    f"Write result.json with keys fuel_burn_lbm (total mission fuel, lbm) "
                    f"and final_mass_lbm (landing mass, lbm). Numeric tolerance: 1% relative."),
            "gold": _GOLD_HEADER + f'''

if __name__ == "__main__":
    r = solve(_p({rel_pair[1]!r}), {mach})
    json.dump(r, open("result.json", "w"), indent=1)
''',
        })

    # ---- T4 总重权衡：三总重同任务（存量）----
    name = "av_grossmass_trade"
    variants = {}
    for gm in (165400, 175400, 185400):
        variants[gm] = derived(f"{name}_{gm}", {"aircraft:design:gross_mass": str(gm)})
    T.append({
        "tid": name, "kind": "trade", "csv": None, "mach": 0.80,
        "keys": ["fuel_165400_lbm", "fuel_175400_lbm", "fuel_185400_lbm", "min_fuel_grossmass_lbm"],
        "title": "总重权衡：三种设计总重下的燃油",
        "ask": ("Run forward mission analyses (run_driver=False, cruise Mach 0.80) for the three "
                "aircraft CSVs provided (design gross mass 165400 / 175400 / 185400 lbm). "
                "Write result.json with keys fuel_165400_lbm, fuel_175400_lbm, fuel_185400_lbm "
                "and min_fuel_grossmass_lbm (the gross-mass value of the lowest-fuel variant, lbm). "
                "Numeric tolerance: 1% relative (min key: exact value match)."),
        "gold": _GOLD_HEADER + f'''

if __name__ == "__main__":
    fuels = {{}}
    for gm, csv in {sorted({gm: rel for gm, (_, rel) in variants.items()}.items())!r}:
        fuels[gm] = solve(_p(csv), 0.80)["fuel_burn_lbm"]
    r = {{
        "fuel_165400_lbm": fuels[165400],
        "fuel_175400_lbm": fuels[175400],
        "fuel_185400_lbm": fuels[185400],
        "min_fuel_grossmass_lbm": float(min(fuels, key=fuels.get)),
    }}
    json.dump(r, open("result.json", "w"), indent=1)
''',
    })

    # ---- T5 航程扫描 + 敏感度（存量）----
    name = "av_range_sweep"
    ranges = (2400, 2800, 3200, 3600)
    variants = {}
    for rg in ranges:
        variants[rg] = derived(f"{name}_{rg}", {"aircraft:design:range": str(rg)})
    T.append({
        "tid": name, "kind": "sweep", "csv": None, "mach": 0.80,
        "keys": [f"fuel_{r}_lbm" for r in ranges] + ["dfuel_drange_lbm_per_nm"],
        "title": "航程扫描与燃油敏感度",
        "ask": ("Run forward mission analyses (run_driver=False, cruise Mach 0.80) for the four "
                "range-variant CSVs provided (2400/2800/3200/3600 NM). Write result.json with "
                "keys fuel_2400_lbm, fuel_2800_lbm, fuel_3200_lbm, fuel_3600_lbm and "
                "dfuel_drange_lbm_per_nm = least-squares slope of fuel vs range "
                "(lbm per NM). Numeric tolerance: 1% relative."),
        "gold": _GOLD_HEADER + f'''

if __name__ == "__main__":
    fuels = {{}}
    for rg, csv in {sorted({rg: rel for rg, (_, rel) in variants.items()}.items())!r}:
        fuels[rg] = solve(_p(csv), 0.80)["fuel_burn_lbm"]
    xs = {list(ranges)!r}
    ys = [fuels[x] for x in xs]
    n = len(xs)
    slope = (n * sum(x * y for x, y in zip(xs, ys)) - sum(xs) * sum(ys)) / (
        n * sum(x * x for x in xs) - sum(xs) ** 2)
    r = {{f"fuel_{{rg}}_lbm": fuels[rg] for rg in {ranges!r}}}
    r["dfuel_drange_lbm_per_nm"] = slope
    json.dump(r, open("result.json", "w"), indent=1)
''',
    })

    # ---- T6/T7 模型修复（存量）----
    ref_true = {"aircraft:design:range": "3200", "aircraft:design:gross_mass": "175400"}
    corrupt_specs = [
        ("av_repair_range", "aircraft:design:range", "4000", "3200",
         {"aircraft:design:range": "range mislabeled 4000 NM (true 3200 NM)",
          "aircraft:design:gross_mass": "gross mass mislabeled (true 175400 lbm)"}),
        ("av_repair_grossmass", "aircraft:design:gross_mass", "185400", "175400",
         {"aircraft:design:range": "range mislabeled (true 3200 NM)",
          "aircraft:design:gross_mass": "gross mass mislabeled 185400 lbm (true 175400 lbm)"}),
    ]
    for tid, param, bad, good, cand_desc in corrupt_specs:
        edits = {k: (bad if k == param else v) for k, v in ref_true.items()}
        csv_corrupt = derived(tid + "_corrupt", edits)
        csv_clean = derived(tid + "_clean", ref_true)
        T.append({
            "tid": tid, "kind": "repair", "csv": csv_corrupt[0], "csv_rel": csv_corrupt[1],
            "mach": 0.80,
            "keys": ["corrupted_param", "restored_value"],
            "title": f"模型修复：{param}",
            "ask": (
                "You are given ONE corrupted aircraft CSV and ONE clean reference table below. "
                "A reference forward analysis (cruise Mach 0.80, run_driver=False) of the TRUE model "
                f"yields the reference fuel burn already provided in result-reference.json. "
                "Exactly one row of the corrupted CSV differs from the true model. Candidates:\n"
                + "\n".join(f"- {k}: {v}" for k, v in cand_desc.items()) + "\n"
                "Identify the corrupted parameter by testing restorations with Aviary and write "
                "result.json with keys corrupted_param (exact CSV key string) and restored_value "
                "(the true numeric value as float). Exact-match grading."),
            "gold": _GOLD_HEADER + f'''

if __name__ == "__main__":
    # repair 参考：gold 直接给出真值（模型侧需通过 Aviary 实验识别）
    r = {{"corrupted_param": {param!r}, "restored_value": float({good!r})}}
    json.dump(r, open("result.json", "w"), indent=1)
''',
            "repair_extra": {"clean_csv": csv_clean[1], "corrupt_csv": csv_corrupt[1],
                             "param": param, "true": good},
        })

    # ---- T8 燃油比（存量）----
    name = "av_fuel_ratio"
    variants = {rg: derived(f"{name}_{rg}", {"aircraft:design:range": str(rg)})
                for rg in (2400, 3600)}
    T.append({
        "tid": name, "kind": "ratio", "csv": None, "mach": 0.80,
        "keys": ["fuel_ratio_3600_over_2400"],
        "title": "远近航程燃油比",
        "ask": ("Run forward mission analyses (run_driver=False, cruise Mach 0.80) for the two "
                "range-variant CSVs provided (2400 and 3600 NM). Write result.json with key "
                "fuel_ratio_3600_over_2400 = fuel(3600)/fuel(2400). Numeric tolerance: 1% relative."),
        "gold": _GOLD_HEADER + f'''

if __name__ == "__main__":
    f24 = solve(_p({variants[2400][1]!r}), 0.80)["fuel_burn_lbm"]
    f36 = solve(_p({variants[3600][1]!r}), 0.80)["fuel_burn_lbm"]
    json.dump({{"fuel_ratio_3600_over_2400": f36 / f24}}, open("result.json", "w"), indent=1)
''',
    })

    # ================= 2026-08-21 扩题（+19，append-only）=================
    # ---- F1 任务分析 range×mach 网格（+10；避开存量 3 组合）----
    for tid, rng, mach in (
        ("av_range_2400_m72", 2400, 0.72),
        ("av_range_2600_m75", 2600, 0.75),
        ("av_range_2800_m78", 2800, 0.78),
        ("av_range_3000_m82", 3000, 0.82),
        ("av_range_3400_m72", 3400, 0.72),
        ("av_range_3400_m80", 3400, 0.80),
        ("av_range_3600_m78", 3600, 0.78),
        ("av_range_2600_m82", 2600, 0.82),
        ("av_range_2800_m75", 2800, 0.75),
        ("av_range_3600_m82", 3600, 0.82),
    ):
        rel_pair = derived(tid, {"aircraft:design:range": str(rng)})
        T.append({
            "tid": tid, "kind": "analysis", "csv": rel_pair[0], "csv_rel": rel_pair[1],
            "mach": mach,
            "keys": ["fuel_burn_lbm", "final_mass_lbm"],
            "title": f"任务分析：航程 {rng} NM、巡航马赫 {mach}",
            "ask": (f"Using the aircraft model CSV provided and Aviary (installed), run a "
                    f"forward mission analysis (run_driver=False) at cruise Mach {mach}. "
                    f"Write result.json with keys fuel_burn_lbm (total mission fuel, lbm) "
                    f"and final_mass_lbm (landing mass, lbm). Numeric tolerance: 1% relative."),
            "gold": _GOLD_HEADER + f'''

if __name__ == "__main__":
    r = solve(_p({rel_pair[1]!r}), {mach})
    json.dump(r, open("result.json", "w"), indent=1)
''',
        })

    # ---- F2 总重权衡（+2；分析模式下 design:gross_mass 为唯一真实敏感参数）----
    for tid, gms in (("av_grossmass_trade2", (167400, 172400, 177400)),
                     ("av_grossmass_trade3", (179400, 180400, 182400))):
        variants = {}
        for gm in gms:
            variants[gm] = derived(f"{tid}_{gm}", {"aircraft:design:gross_mass": str(gm)})
        keys = [f"fuel_{gm}_lbm" for gm in gms] + ["min_fuel_grossmass_lbm"]
        T.append({
            "tid": tid, "kind": "trade", "csv": None, "mach": 0.80,
            "keys": keys,
            "title": f"总重权衡：三种设计总重下的燃油（{gms[0]}/{gms[1]}/{gms[2]} lbm）",
            "ask": (f"Run forward mission analyses (run_driver=False, cruise Mach 0.80) for the three "
                    f"aircraft CSVs provided (design gross mass {gms[0]} / {gms[1]} / {gms[2]} lbm). "
                    f"Write result.json with keys {', '.join(f'fuel_{gm}_lbm' for gm in gms)} "
                    f"and min_fuel_grossmass_lbm (the gross-mass value of the lowest-fuel variant, lbm). "
                    f"Numeric tolerance: 1% relative (min key: exact value match)."),
            "gold": _GOLD_HEADER + f'''

if __name__ == "__main__":
    fuels = {{}}
    for gm, csv in {sorted({gm: rel for gm, (_, rel) in variants.items()}.items())!r}:
        fuels[gm] = solve(_p(csv), 0.80)["fuel_burn_lbm"]
    r = {{f"fuel_{{gm}}_lbm": fuels[gm] for gm in {gms!r}}}
    r["min_fuel_grossmass_lbm"] = float(min(fuels, key=fuels.get))
    json.dump(r, open("result.json", "w"), indent=1)
''',
        })

    # ---- F3 总重扫描 + 敏感度（+1）----
    name = "av_grossmass_sweep"
    masses = (165400, 170400, 175400, 180400, 185400)
    variants = {}
    for gm in masses:
        variants[gm] = derived(f"{name}_{gm}", {"aircraft:design:gross_mass": str(gm)})
    T.append({
        "tid": name, "kind": "sweep", "csv": None, "mach": 0.80,
        "keys": [f"fuel_{gm}_lbm" for gm in masses] + ["dfuel_dgrossmass_lbm_per_lbm"],
        "title": "总重扫描与燃油敏感度",
        "ask": ("Run forward mission analyses (run_driver=False, cruise Mach 0.80) for the five "
                "gross-mass-variant CSVs provided (165400/170400/175400/180400/185400 lbm). "
                "Write result.json with keys fuel_165400_lbm, fuel_170400_lbm, fuel_175400_lbm, "
                "fuel_180400_lbm, fuel_185400_lbm and dfuel_dgrossmass_lbm_per_lbm = "
                "least-squares slope of fuel vs gross mass (lbm per lbm). "
                "Numeric tolerance: 1% relative."),
        "gold": _GOLD_HEADER + f'''

if __name__ == "__main__":
    fuels = {{}}
    for gm, csv in {sorted({gm: rel for gm, (_, rel) in variants.items()}.items())!r}:
        fuels[gm] = solve(_p(csv), 0.80)["fuel_burn_lbm"]
    xs = {list(masses)!r}
    ys = [fuels[x] for x in xs]
    n = len(xs)
    slope = (n * sum(x * y for x, y in zip(xs, ys)) - sum(xs) * sum(ys)) / (
        n * sum(x * x for x in xs) - sum(xs) ** 2)
    r = {{f"fuel_{{gm}}_lbm": fuels[gm] for gm in {masses!r}}}
    r["dfuel_dgrossmass_lbm_per_lbm"] = slope
    json.dump(r, open("result.json", "w"), indent=1)
''',
    })

    # ---- F4 燃油比（+2）----
    for tid, rg_lo, rg_hi in (("av_fuel_ratio_3500_over_2500", 2500, 3500),
                              ("av_fuel_ratio_3300_over_2700", 2700, 3300)):
        variants = {rg: derived(f"{tid}_{rg}", {"aircraft:design:range": str(rg)})
                    for rg in (rg_lo, rg_hi)}
        key = f"fuel_ratio_{rg_hi}_over_{rg_lo}"
        T.append({
            "tid": tid, "kind": "ratio", "csv": None, "mach": 0.80,
            "keys": [key],
            "title": f"远近航程燃油比（{rg_hi} vs {rg_lo} NM）",
            "ask": (f"Run forward mission analyses (run_driver=False, cruise Mach 0.80) for the two "
                    f"range-variant CSVs provided ({rg_lo} and {rg_hi} NM). Write result.json with key "
                    f"{key} = fuel({rg_hi})/fuel({rg_lo}). Numeric tolerance: 1% relative."),
            "gold": _GOLD_HEADER + f'''

if __name__ == "__main__":
    flo = solve(_p({variants[rg_lo][1]!r}), 0.80)["fuel_burn_lbm"]
    fhi = solve(_p({variants[rg_hi][1]!r}), 0.80)["fuel_burn_lbm"]
    json.dump({{{key!r}: fhi / flo}}, open("result.json", "w"), indent=1)
''',
        })

    # ---- F5 航程扫描（换基点/加密，+2）----
    for tid, rgs, mach in (("av_range_sweep_m78", (2400, 2600, 2800, 3000), 0.78),
                           ("av_range_sweep_fine", (3000, 3200, 3400, 3600), 0.80)):
        variants = {}
        for rg in rgs:
            variants[rg] = derived(f"{tid}_{rg}", {"aircraft:design:range": str(rg)})
        T.append({
            "tid": tid, "kind": "sweep", "csv": None, "mach": mach,
            "keys": [f"fuel_{r}_lbm" for r in rgs] + ["dfuel_drange_lbm_per_nm"],
            "title": f"航程扫描与燃油敏感度（{rgs[0]}-{rgs[-1]} NM @ M{mach}）",
            "ask": (f"Run forward mission analyses (run_driver=False, cruise Mach {mach}) for the four "
                    f"range-variant CSVs provided ({'/'.join(str(r) for r in rgs)} NM). "
                    f"Write result.json with keys {', '.join(f'fuel_{r}_lbm' for r in rgs)} and "
                    f"dfuel_drange_lbm_per_nm = least-squares slope of fuel vs range "
                    f"(lbm per NM). Numeric tolerance: 1% relative."),
            "gold": _GOLD_HEADER + f'''

if __name__ == "__main__":
    fuels = {{}}
    for rg, csv in {sorted({rg: rel for rg, (_, rel) in variants.items()}.items())!r}:
        fuels[rg] = solve(_p(csv), {mach})["fuel_burn_lbm"]
    xs = {list(rgs)!r}
    ys = [fuels[x] for x in xs]
    n = len(xs)
    slope = (n * sum(x * y for x, y in zip(xs, ys)) - sum(xs) * sum(ys)) / (
        n * sum(x * x for x in xs) - sum(xs) ** 2)
    r = {{f"fuel_{{rg}}_lbm": fuels[rg] for rg in {rgs!r}}}
    r["dfuel_drange_lbm_per_nm"] = slope
    json.dump(r, open("result.json", "w"), indent=1)
''',
        })

    # ---- F6 模型修复变体（+2）----
    repair_specs = [
        ("av_repair_grossmass_v2", "aircraft:design:gross_mass", "180400", "175400",
         {"aircraft:design:range": "3000"}, {"aircraft:design:range": "3000",
          "aircraft:design:gross_mass": "175400"},
         {"aircraft:design:range": "range mislabeled 3000 NM (true 3400 NM)",
          "aircraft:design:gross_mass": "gross mass mislabeled 180400 lbm (true 175400 lbm)"}),
        ("av_repair_range_v2", "aircraft:design:range", "2500", "3400",
         {"aircraft:design:gross_mass": "175400"}, {"aircraft:design:range": "3400",
          "aircraft:design:gross_mass": "175400"},
         {"aircraft:design:range": "range mislabeled 2500 NM (true 3400 NM)",
          "aircraft:design:gross_mass": "gross mass mislabeled (true 180400 lbm)"}),
    ]
    for tid, param, bad, good, corrupt_other, ref_true_v2, cand_desc in repair_specs:
        edits = {k: (bad if k == param else v) for k, v in ref_true_v2.items()}
        csv_corrupt = derived(tid + "_corrupt", edits)
        csv_clean = derived(tid + "_clean", ref_true_v2)
        T.append({
            "tid": tid, "kind": "repair", "csv": csv_corrupt[0], "csv_rel": csv_corrupt[1],
            "mach": 0.80,
            "keys": ["corrupted_param", "restored_value"],
            "title": f"模型修复：{param}（新数值组）",
            "ask": (
                "You are given ONE corrupted aircraft CSV and ONE clean reference table below. "
                "A reference forward analysis (cruise Mach 0.80, run_driver=False) of the TRUE model "
                f"yields the reference fuel burn already provided in result-reference.json. "
                "Exactly one row of the corrupted CSV differs from the true model. Candidates:\n"
                + "\n".join(f"- {k}: {v}" for k, v in cand_desc.items()) + "\n"
                "Identify the corrupted parameter by testing restorations with Aviary and write "
                "result.json with keys corrupted_param (exact CSV key string) and restored_value "
                "(the true numeric value as float). Exact-match grading."),
            "gold": _GOLD_HEADER + f'''

if __name__ == "__main__":
    # repair 参考：gold 直接给出真值（模型侧需通过 Aviary 实验识别）
    r = {{"corrupted_param": {param!r}, "restored_value": float({good!r})}}
    json.dump(r, open("result.json", "w"), indent=1)
''',
            "repair_extra": {"clean_csv": csv_clean[1], "corrupt_csv": csv_corrupt[1],
                             "param": param, "true": good},
        })
    return T


# ---------------------------------------------------------------- gold 执行与参考锁定

def run_gold(gold_code: str, workdir: Path, extra_files: dict[str, str] | None = None) -> dict:
    """在 venv 子进程里跑 gold 脚本（cwd=workdir），返回 result.json。"""
    script = workdir / "gold.py"
    script.write_text(gold_code, encoding="utf-8")
    for name, content in (extra_files or {}).items():
        p = workdir / name
        p.write_text(content, encoding="utf-8")
    import os
    env = dict(os.environ)
    env["MPLCONFIGDIR"] = "/tmp"
    r = subprocess.run([_venv_python(), str(script)], cwd=workdir,
                       capture_output=True, text=True, timeout=900, env=env)
    if r.returncode != 0:
        raise RuntimeError(f"gold 失败: {r.stderr[-400:]}")
    return json.loads((workdir / "result.json").read_text())


def write_task_yaml(t: dict, refs: dict, digests: dict[str, str],
                    prompt_sha: str) -> dict:
    # digests 键已是工作区相对全路径（data/aviary/transport_mission/...）
    assets = [{"path": p, "digest": d} for p, d in digests.items()]
    spec = {
        "id": t["tid"],
        "registry_id": "aviary.transport_mission",
        "domain": "mdo_design",
        "task_type": "simulation_agent",
        "model_profile": "plain_llm",
        "assets_revision": ASSETS_REVISION,
        "environment_digest": "computed-at-runtime",
        "hidden": False,
        "allowed_tools": ["python", "aviary"],
        "input": {
            "prompt_file": f"tasks/aviary.transport_mission/{t['tid']}.md",
            "prompt_sha256": prompt_sha,
            "assets": assets,
        },
        "output_contract": ["result.json"],
        "reference": {
            "source": "gold 脚本预计算（本 harness，aviary 1.0.1 分析模式确定性）",
            "revision": ASSETS_REVISION,
            "values": refs,
            "rel_tol": REL_TOL,
            "uncertainty_note": "确定性正向分析；容差覆盖模型间口径差异",
        },
        "grader": {
            "answer_format": "code",
            "exec_kind": "aviary_mission",
            "validity_gate": True,
            "result_keys": t["keys"],
            "numeric_rel_tol": REL_TOL,
            "exact_keys": ["corrupted_param", "restored_value", "min_fuel_grossmass_lbm"],
            "solver_backend": "aviary-analysis-venv",
            "oracle_source": f"data/aviary/transport_mission/gold/{t['tid']}.py",
            "sandbox": {"banned": "network/process/ctypes", "isolated_interpreter": True},
        },
        "scoring": {
            "weights": {"physics": 0.6, "requirements": 0.4, "objective": 0.0, "robustness": 0.0},
            "note": "physics=数值字段命中均值（容差 1%）；requirements=result.json 键完备；"
                    "objective/robustness=N/A（静态任务）权重 0",
        },
        "limits": {"cpu": 4, "memory_gb": 8, "wall_clock_s": 1200, "attempts": 3},
        "license_provenance": {
            "source": "自建任务 + NASA Aviary (Apache-2.0) 基准模型",
            "license": "Apache-2.0 (Aviary 及其模型)；任务文本自建",
            "status": "confirmed-repo",
            "revision": ASSETS_REVISION,
            "mirror_allowed": True,
            "attribution": "NASA Aviary, github.com/openmdao/Aviary",
        },
    }
    return spec


def build_prompt(t: dict, csv_abs: str | None, extra: dict | None) -> str:
    lines = [f"# {t['title']}", "", t["ask"], ""]
    if csv_abs:
        lines.append(f"Aircraft model CSV (absolute path, read-only): `{csv_abs}`")
    if extra:
        lines += ["", extra.get("note", "")]
    lines += ["", "Aviary 1.0.1 + numpy are installed. IMPORTANT environment constraints:",
              '- call run_aviary(..., run_driver=False, optimizer="SLSQP", verbosity=0, make_plots=False)',
              "  (pyoptsparse/IPOPT is NOT installed; pass optimizer explicitly or import fails)",
              "- cruise Mach is set via phase_info['cruise']['user_options']['mach_cruise'] "
              "(deepcopy the default phase_info from aviary.models.missions.two_dof_default first).",
              "Output variables (OpenMDAO promoted names, colon style): "
              "'mission:total_fuel_mass' (lbm), 'mission:final_mass' (lbm), 'mission:range' (NM); "
              "read via prob.get_val('mission:total_fuel_mass', units='lbm')[0].",
              "Write the result file to the current working directory as result.json.",
              "Respond with a single ```python code block and nothing else.", ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--force-refs", action="store_true")
    args = ap.parse_args()

    import aviary
    (DATA / "base").mkdir(parents=True, exist_ok=True)
    (DATA / "derived").mkdir(parents=True, exist_ok=True)
    (DATA / "gold").mkdir(parents=True, exist_ok=True)
    (DATA / "references").mkdir(parents=True, exist_ok=True)
    TASKS_DIR.mkdir(parents=True, exist_ok=True)

    base_dst = DATA / "base" / BASE_CSV_NAME
    src_csv = Path(aviary.__file__).parent / "validation_cases" / "validation_data" / "test_models" / BASE_CSV_NAME
    if not args.check:
        base_dst.write_text(src_csv.read_text(), encoding="utf-8")
    base_txt = base_dst.read_text(encoding="utf-8")

    tasks = task_defs(base_txt, DATA / "derived")

    # 资产摘要（base + 全部 derived）
    from .common import sha256_file
    digests = {}
    for p in sorted((DATA).glob("base/*.csv")) + sorted((DATA).glob("derived/*.csv")):
        digests[f"data/aviary/transport_mission/{p.relative_to(DATA).as_posix()}"] = sha256_file(p)

    drift = []
    frozen = 0
    for t in tasks:
        gold_path = DATA / "gold" / f"{t['tid']}.py"
        ref_path = DATA / "references" / f"{t['tid']}.json"
        yaml_path = TASKS_DIR / f"{t['tid']}.yaml"
        if not args.check:
            # gold 全量重写（含存量 8 题：路径可移植性修复，见模块 docstring）
            gold_path.write_text(t["gold"], encoding="utf-8")

        if args.check:
            if not gold_path.exists() or gold_path.read_text(encoding="utf-8") != t["gold"]:
                drift.append(t["tid"])
            continue

        # 存量任务（YAML 已在库）冻结：refs/YAML/MD 不重写（等效性另由重跑验证保证）
        if yaml_path.exists():
            frozen += 1
            print(f"[frozen] {t['tid']} (存量不重写 YAML/MD/refs；gold 已按可移植路径重写)")
            continue
        # 参考预计算（repair 任务需附 result-reference.json）
        extra_files = None
        if t["kind"] == "repair":
            clean_csv_rel = t["repair_extra"]["clean_csv"]
            with tempfile.TemporaryDirectory() as td:
                tmp = Path(td)
                g2 = _GOLD_HEADER + f"""

if __name__ == "__main__":
    r = solve(_p({clean_csv_rel!r}), 0.80)
    json.dump(r, open("result.json", "w"), indent=1)
"""
                ref_clean = run_gold(g2, tmp)
            extra_files = {"result-reference.json":
                           json.dumps({"fuel_burn_lbm": ref_clean["fuel_burn_lbm"]}, indent=1)}
            (DATA / "references" / f"{t['tid']}_reference_context.json").write_text(
                extra_files["result-reference.json"], encoding="utf-8")
        if args.force_refs or not ref_path.exists():
            with tempfile.TemporaryDirectory() as td:
                refs = run_gold(t["gold"], Path(td), extra_files=None)
            ref_path.write_text(json.dumps(refs, indent=1, sort_keys=True), encoding="utf-8")
        refs = json.loads(ref_path.read_text())

        csv_abs = t["csv"] if t.get("csv") else None   # derived() 已返回绝对路径
        extra = None
        if t["kind"] == "repair":
            ctx = json.loads((DATA / "references" / f"{t['tid']}_reference_context.json").read_text())
            cor = t["repair_extra"]["corrupt_csv"]
            extra = {"note": (
                f"Corrupted CSV (absolute path): `{(DATA / cor).resolve()}`\n"
                f"Reference fuel burn of the TRUE model (lbm): {ctx['fuel_burn_lbm']:.2f}\n"
                "The true model differs from the corrupted one in exactly the candidate row above.") }
            csv_abs = str((DATA / cor).resolve())
        prompt = build_prompt(t, csv_abs, extra)
        prompt_sha = hashlib.sha256(prompt.encode()).hexdigest()
        spec = write_task_yaml(t, refs, digests, prompt_sha)
        want = yaml.safe_dump(spec, sort_keys=False, allow_unicode=True)
        (TASKS_DIR / f"{t['tid']}.yaml").write_text(want, encoding="utf-8")
        (TASKS_DIR / f"{t['tid']}.md").write_text(prompt, encoding="utf-8")
        print(f"[gen] {t['tid']}: refs={sorted(refs.keys())}")

    # ---- 隐藏动态生成器（评审件）——2026-08-21 起冻结：answers.b64 已在库即不重算 ----
    if not args.check:
        if not (DATA / "hidden" / "answers.b64").exists():
            build_hidden(base_txt)
        else:
            print("[hidden] answers.b64 已在库，冻结不重算")

    if args.check:
        if drift:
            print(f"[check] gold 不一致: {drift}")
            return 1
        print(f"[check] {len(tasks)} 个任务与镜像一致")
        return 0
    print(f"[gen] {len(tasks)} tasks ({frozen} frozen) -> {TASKS_DIR}")
    return 0


def build_hidden(base_txt: str) -> None:
    hidden = DATA / "hidden"
    hidden.mkdir(exist_ok=True)
    gen = '''"""隐藏动态题生成器（aviary.transport_mission，M3 评审件）。

采样策略（版本化进 git）：
  - 参数空间：range ∈ [2200, 3800] NM（步长 50）、cruise Mach ∈ [0.72, 0.82]（步长 0.005）、
    设计总重 ∈ [165400, 185400] lbm（步长 1000）；
  - 种子：SAMPlING_SEED（每轮评测可轮换；轮换后须重跑本生成器重锁参考）；
  - 题目参数三元组均匀无放回采样；
  - 参考答案：gold 分析模式预计算 → base64 隔离存 answers.b64（不明文入库，
    满足 scoring/README.md §5「采样种子与参考答案不明文入库」）；
  - 泄漏监控：每轮统计 hidden-public 分差（report 汇总层），分差收窄触发轮换。
"""
import base64
import json
import random

SAMPLING_SEED = 20260819
N_SAMPLES = 3  # 试点规模；正式轮可扩

ranges = list(range(2200, 3801, 50))
machs = [round(0.72 + 0.005 * i, 3) for i in range(21)]
masses = list(range(165400, 185401, 1000))

rng = random.Random(SAMPLING_SEED)
combos = [(r, m, g) for r in ranges for m in machs for g in masses]
rng.shuffle(combos)
picked = combos[:N_SAMPLES]

payload = {"seed": SAMPLING_SEED, "combos": picked,
           "answers": {f"h{i+1}": None for i in range(N_SAMPLES)}}
print(json.dumps(payload, indent=1))
# answers 由外部 gold 预计算后填入并 base64 落盘（见 README.md）
'''
    (hidden / "generator.py").write_text(gen, encoding="utf-8")
    # 执行采样 + 预计算 3 例答案
    rng = random.Random(20260819)
    combos = [(r, m, g) for r in range(2200, 3801, 50)
              for m in [round(0.72 + 0.005 * i, 3) for i in range(21)]
              for g in range(165400, 185401, 1000)]
    rng.shuffle(combos)
    picked = combos[:3]
    answers = {}
    for i, (rg, mach, gm) in enumerate(picked, 1):
        edits = {"aircraft:design:range": str(rg),
                 "aircraft:design:gross_mass": str(gm)}
        csv_txt = _modify_csv(base_txt, edits)
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            (tmp / "hidden_case.csv").write_text(csv_txt, encoding="utf-8")
            g = _GOLD_HEADER + f"""

if __name__ == "__main__":
    r = solve(str({str(tmp / 'hidden_case.csv')!r}), {mach})
    json.dump(r, open("result.json", "w"), indent=1)
"""
            res = run_gold(g, tmp)
        answers[f"h{i}"] = {"range_nm": rg, "mach": mach, "gross_mass_lbm": gm, **res}
    blob = {"seed": 20260819, "answers": answers}
    (hidden / "answers.b64").write_text(
        base64.b64encode(json.dumps(blob).encode()).decode(), encoding="utf-8")
    (hidden / "README.md").write_text(
        "# aviary 隐藏动态题（隔离方案）\n\n"
        "- `generator.py`：参数空间与采样策略（版本化；种子轮换即新评测周期）。\n"
        "- `answers.b64`：base64 编码的预计算参考（防明文泄漏的一层隔离；参考答案不进任务明文）。\n"
        "- 隔离边界：模型题面只含 (range, mach, gross_mass) 三元组，不含答案；判分读 answers.b64。\n"
        "- 试点 3 例已预计算；正式轮扩容由生成器重跑（--force-refs 语义）。\n"
        "- 评审点（M3）：采样密度、种子轮换策略、泄漏监控阈值。\n", encoding="utf-8")
    print(f"[hidden] 3 例试点答案已预计算并隔离落盘")


if __name__ == "__main__":
    raise SystemExit(main())
