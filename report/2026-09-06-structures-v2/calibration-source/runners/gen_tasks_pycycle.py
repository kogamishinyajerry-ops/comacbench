"""gen_tasks_pycycle.py — 自建 pycycle.engine_cycle 任务集（batch-2；2026-08-21 扩题 7→28）。

产出（幂等；参考值由 gold 脚本预计算锁定）：
  data/pycycle/engine_cycle/{base/,gold/,references/,hidden/} + 任务 YAML/MD

任务协议（simulation_agent / pycycle_cycle 分支）：
  被测模型写 python 脚本，用已装 pycycle（om-pycycle 源码安装）构造 turbojet 循环求解，
  在 cwd 写 result.json；判分 = 数值对锁定参考的相对误差（1% 容差，exact_keys 精确匹配）。
  gold 引擎 = 官方 simple_turbojet 模型（viewer/map_plots 剥离，Apache-2.0 归属）。

2026-08-21 扩题（append-only，存量 7 题任务契约逐字节冻结）：
  - 新增 21 题（全部 gold 真实跑通，solve_design 收敛域内）：
    设计点网格 9（fn 10k-16k / t4 2300-2900 / opr 11-16，避开存量 3 组）+
    油门 T4 变体 3（t2300/t2500/t2700，命名沿存量 pc_od_throttle_* 惯例，本质同为 SL
    设计解——引擎仅暴露 solve_design，无参数化 OD 入口，如实降级记录于 PROVENANCE）+
    敏感性扫描 3（OPR 基点换 15k/2800、T4 扫描 dTSFC/dT4、Fn 扫描 dWfuel/dFn）+
    油耗比 3（三组 (t4_low,t4_high) 对）+ 参数修复 3（corrupted OPR + t4/fn 新数值）；
  - gold 脚本路径可移植性修复（含存量 7 题重写）：模板不再内嵌仓库绝对路径
    （建集日后仓库搬迁使旧绝对路径失效），引擎定位 = gold 同目录（沙箱 companion）/
    上溯一级（仓库内）；存量任务的 YAML/MD/references 逐字节冻结不重写，
    旧 gold 修复后逐一重跑对锁定 references 等效验证（见 PROVENANCE 扩题节）；
  - hidden/ 评审件（answers.b64）已在库即冻结不重算；
  - seed / REL_TOL / ASSETS_REVISION / 判分口径均不变。

用法：.venv/bin/python -m runners.gen_tasks_pycycle [--check] [--force-refs]
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import random
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

import yaml

warnings.filterwarnings("ignore")

BENCH = Path(__file__).resolve().parent.parent
DATA = BENCH / "data/pycycle/engine_cycle"
TASKS_DIR = BENCH / "tasks/pycycle.engine_cycle"
ASSETS_REVISION = "pycycle-pack@selfbuilt-2026-08-19+ompycycle_src"

REL_TOL = 0.01

_VENV_PY = BENCH / ".venv/bin/python"

# gold 引擎：官方 simple_turbojet（viewer/map_plots no-op patch）
# 归属：om-pycycle Apache-2.0，github.com/openmdao/pycycle example_cycles/simple_turbojet.py
# 2026-08-21 起路径可移植：不再内嵌仓库绝对路径（建集日后仓库搬迁使旧绝对路径失效）。
# 引擎定位：gold 同目录（沙箱 companion 场景，turbojet_engine.py 随行落盘）优先，
# 否则上溯一级（仓库内 gold/ → data/pycycle/engine_cycle/turbojet_engine.py）。
_GOLD_TEMPLATE = '''"""gold 解（pycycle turbojet）。判分参考预计算用；模型不可见。"""
import json
import sys
import warnings

warnings.filterwarnings("ignore")
import matplotlib
matplotlib.use("Agg")

import os
_here = os.path.dirname(os.path.abspath(__file__))
_engine = None
for _cand in (os.path.join(_here, "turbojet_engine.py"),
              os.path.join(_here, "..", "turbojet_engine.py")):
    if os.path.exists(_cand):
        _engine = os.path.abspath(_cand)
        break
if _engine is None:
    raise RuntimeError("turbojet_engine.py not found next to gold or in parent dir")
sys.path.insert(0, os.path.dirname(_engine))
import turbojet_engine as te

if __name__ == "__main__":
    r = {body}
    json.dump(r, open("result.json", "w"), indent=1)
'''


def _slug(s: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


_ENGINE_PATH = DATA / "turbojet_engine.py"


def run_gold(gold_code: str, workdir: Path, venv_py: Path) -> dict:
    """在 venv 子进程里跑 gold（cwd=workdir）。

    gold 模板已路径可移植（不内嵌绝对路径）：workdir 内随行落盘一份引擎
    turbojet_engine.py 作 companion，gold 的「同目录」定位分支即命中。
    """
    script = workdir / "gold.py"
    script.write_text(gold_code, encoding="utf-8")
    (workdir / "turbojet_engine.py").write_text(_ENGINE_PATH.read_text(), encoding="utf-8")
    import os
    env = dict(os.environ)
    env["MPLCONFIGDIR"] = "/tmp"
    r = subprocess.run([str(venv_py), str(script)], cwd=workdir,
                       capture_output=True, text=True, timeout=600, env=env)
    if r.returncode != 0:
        raise RuntimeError(f"gold 失败: {r.stderr[-500:]}")
    return json.loads((workdir / "result.json").read_text())


def task_defs() -> list[dict]:
    T = []
    # T1-T3 设计点（SL，参数域内）
    for tid, fn, t4, opr in (
        ("pc_design_fn12k_t2450", 12000, 2450, 14.0),
        ("pc_design_fn15k_t2800", 15000, 2800, 15.0),
        ("pc_od_throttle_t2200", 11800, 2200, 13.5),
    ):
        T.append({
            "tid": tid, "kind": "design", "params": {"fn_target": fn, "t4_target": t4, "opr": opr},
            "keys": ["Fn_lbf", "TSFC", "OPR", "Wfuel_lbm_s"],
            "title": f"设计点：SL 静止，Fn_target={fn} lbf，T4={t4}°R，OPR={opr}",
            "ask": (f"Using pycycle (installed as om-pycycle), build the simple turbojet cycle "
                    f"(Inlet + AXI5 Compressor + Combustor + LPT2269 Turbine + CD Nozzle + Shaft, "
                    f"TABULAR thermo AIR_JETA_TAB_SPEC, SL design at alt 0 ft MN~0) and solve the "
                    f"DESIGN point: Fn_target {fn} lbf, T4_target {t4} degR, compressor OPR {opr}. "
                    f"Write result.json with keys Fn_lbf (net thrust), TSFC, OPR, Wfuel_lbm_s. "
                    f"Numeric tolerance 1%."),
        })
    # T4 OPR 敏感性
    T.append({
        "tid": "pc_opr_sweep", "kind": "multi",
        "params": {"base": {"fn_target": 12000, "t4_target": 2450}, "oprs": [11.0, 13.5, 16.0]},
        "keys": ["tsfc_opr110", "tsfc_opr135", "tsfc_opr160", "dtsfc_dopr"],
        "title": "OPR 扫描与 TSFC 敏感性（SL）",
        "ask": ("Solve the SL turbojet design point at Fn_target 12000 lbf, T4 2450 degR for "
                "OPR 11 / 13.5 / 16. Write result.json with tsfc_opr110, tsfc_opr135, tsfc_opr160 "
                "and dtsfc_dopr = least-squares slope of TSFC vs OPR. Numeric tolerance 1%."),
    })
    # T5 T4 油耗比
    T.append({
        "tid": "pc_fuel_ratio", "kind": "multi",
        "params": {"base": {"fn_target": 11800, "opr": 13.5}, "t4s": [2200, 2600]},
        "keys": ["fuel_ratio_t2600_over_t2200"],
        "title": "T4 油耗比（SL）",
        "ask": ("Solve the SL turbojet design point at Fn_target 11800 lbf, OPR 13.5 for T4 2200 "
                "degR and T4 2600 degR. Write result.json with fuel_ratio_t2600_over_t2200 = "
                "Wfuel(2600)/Wfuel(2200). Numeric tolerance 1%."),
    })
    # T6-T7 参数修复
    for tid, bad_param, bad_val, good_val, others in (
        ("pc_repair_t4", "t4_target", 3200, 2370, {"fn_target": 11800, "opr": 13.5}),
        ("pc_repair_fn", "fn_target", 9999, 11800, {"t4_target": 2370, "opr": 13.5}),
    ):
        T.append({
            "tid": tid, "kind": "repair",
            "params": {"bad_param": bad_param, "bad_val": bad_val, "good_val": good_val, "others": others},
            "keys": ["corrupted_param", "restored_value"],
            "title": f"循环参数修复：{bad_param}",
            "ask": (f"A SL turbojet design solve (OPR 13.5) was run with a corrupted target: "
                    f"{bad_param} = {bad_val} (physically implausible for this engine class; the true "
                    f"value is one of the standard values for this cycle family). The reference TSFC "
                    f"of the TRUE configuration is given in the prompt. Identify the corrupted parameter "
                    f"and its true value by testing restorations with pycycle. Write result.json with "
                    f"corrupted_param (exact string: 'fn_target' or 't4_target') and restored_value "
                    f"(true numeric value). Exact-match grading."),
        })

    # ================= 2026-08-21 扩题（+21，append-only）=================
    # F1 设计点网格补密（+9）：域内取值，避开存量 (12k,2450,14)/(15k,2800,15)/(11.8k,2200,13.5)
    for tid, fn, t4, opr in (
        ("pc_design_fn10k_t2300_opr12", 10000, 2300, 12.0),
        ("pc_design_fn11k_t2550_opr11", 11000, 2550, 11.0),
        ("pc_design_fn13k_t2650_opr13", 13000, 2650, 13.0),
        ("pc_design_fn14k_t2900_opr16", 14000, 2900, 16.0),
        ("pc_design_fn16k_t2350_opr155", 16000, 2350, 15.5),
        ("pc_design_fn10p5k_t2750_opr145", 10500, 2750, 14.5),
        ("pc_design_fn13p5k_t2400_opr115", 13500, 2400, 11.5),
        ("pc_design_fn14p5k_t2850_opr125", 14500, 2850, 12.5),
        ("pc_design_fn15p5k_t2500_opr135", 15500, 2500, 13.5),
    ):
        T.append({
            "tid": tid, "kind": "design", "params": {"fn_target": fn, "t4_target": t4, "opr": opr},
            "keys": ["Fn_lbf", "TSFC", "OPR", "Wfuel_lbm_s"],
            "title": f"设计点：SL 静止，Fn_target={fn} lbf，T4={t4}°R，OPR={opr}",
            "ask": (f"Using pycycle (installed as om-pycycle), build the simple turbojet cycle "
                    f"(Inlet + AXI5 Compressor + Combustor + LPT2269 Turbine + CD Nozzle + Shaft, "
                    f"TABULAR thermo AIR_JETA_TAB_SPEC, SL design at alt 0 ft MN~0) and solve the "
                    f"DESIGN point: Fn_target {fn} lbf, T4_target {t4} degR, compressor OPR {opr}. "
                    f"Write result.json with keys Fn_lbf (net thrust), TSFC, OPR, Wfuel_lbm_s. "
                    f"Numeric tolerance 1%."),
        })
    # F2 油门 T4 变体（+3）：引擎仅暴露 solve_design（SL 设计解），无参数化 OD 入口——
    # 命名沿存量 pc_od_throttle_t2200 惯例，本质为 T4 降/升油门对应的设计点重解（如实降级）
    for tid, t4 in (("pc_od_throttle_t2300", 2300), ("pc_od_throttle_t2500", 2500),
                    ("pc_od_throttle_t2700", 2700)):
        T.append({
            "tid": tid, "kind": "design",
            "params": {"fn_target": 11800, "t4_target": t4, "opr": 13.5},
            "keys": ["Fn_lbf", "TSFC", "OPR", "Wfuel_lbm_s"],
            "title": f"设计点：SL 静止，Fn_target=11800 lbf，T4={t4}°R，OPR=13.5",
            "ask": (f"Using pycycle (installed as om-pycycle), build the simple turbojet cycle "
                    f"(Inlet + AXI5 Compressor + Combustor + LPT2269 Turbine + CD Nozzle + Shaft, "
                    f"TABULAR thermo AIR_JETA_TAB_SPEC, SL design at alt 0 ft MN~0) and solve the "
                    f"DESIGN point: Fn_target 11800 lbf, T4_target {t4} degR, compressor OPR 13.5. "
                    f"Write result.json with keys Fn_lbf (net thrust), TSFC, OPR, Wfuel_lbm_s. "
                    f"Numeric tolerance 1%."),
        })
    # F3 敏感性扫描（+3）
    T.append({
        "tid": "pc_opr_sweep_hi", "kind": "multi",
        "params": {"base": {"fn_target": 15000, "t4_target": 2800}, "oprs": [11.5, 14.0, 16.0]},
        "keys": ["tsfc_opr115", "tsfc_opr140", "tsfc_opr160", "dtsfc_dopr"],
        "title": "OPR 扫描与 TSFC 敏感性（SL，高推力基点）",
        "ask": ("Solve the SL turbojet design point at Fn_target 15000 lbf, T4 2800 degR for "
                "OPR 11.5 / 14 / 16. Write result.json with tsfc_opr115, tsfc_opr140, tsfc_opr160 "
                "and dtsfc_dopr = least-squares slope of TSFC vs OPR. Numeric tolerance 1%."),
    })
    T.append({
        "tid": "pc_t4_sweep", "kind": "t4sweep",
        "params": {"base": {"fn_target": 12500, "opr": 14.0}, "t4s": [2350, 2550, 2750]},
        "keys": ["tsfc_t42350", "tsfc_t42550", "tsfc_t42750", "dtsfc_dt4"],
        "title": "T4 扫描与 TSFC 敏感性（SL）",
        "ask": ("Solve the SL turbojet design point at Fn_target 12500 lbf, OPR 14.0 for "
                "T4 2350 / 2550 / 2750 degR. Write result.json with tsfc_t42350, tsfc_t42550, "
                "tsfc_t42750 and dtsfc_dt4 = least-squares slope of TSFC vs T4 (1/degR). "
                "Numeric tolerance 1%."),
    })
    T.append({
        "tid": "pc_fn_sweep", "kind": "fnsweep",
        "params": {"base": {"t4_target": 2450, "opr": 13.5}, "fns": [10500, 12000, 13500]},
        "keys": ["wfuel_fn10500", "wfuel_fn12000", "wfuel_fn13500", "dwfuel_dfn"],
        "title": "Fn 扫描与油耗斜率（SL）",
        "ask": ("Solve the SL turbojet design point at T4 2450 degR, OPR 13.5 for Fn_target "
                "10500 / 12000 / 13500 lbf. Write result.json with wfuel_fn10500, wfuel_fn12000, "
                "wfuel_fn13500 (burner fuel flow, lbm/s) and dwfuel_dfn = least-squares slope of "
                "Wfuel vs Fn_target (lbm/s per lbf). Numeric tolerance 1%."),
    })
    # F4 油耗比（+3）
    for tid, fn, opr, t4_lo, t4_hi, lo_s, hi_s in (
        ("pc_fuel_ratio_t2700_over_t2300", 11800, 13.5, 2300, 2700, "t2300", "t2700"),
        ("pc_fuel_ratio_hi", 13000, 14.0, 2400, 2800, "t2400", "t2800"),
        ("pc_fuel_ratio_lo", 11000, 12.0, 2250, 2550, "t2250", "t2550"),
    ):
        T.append({
            "tid": tid, "kind": "ratio",
            "params": {"base": {"fn_target": fn, "opr": opr}, "t4s": [t4_lo, t4_hi],
                       "key": f"fuel_ratio_{hi_s}_over_{lo_s}"},
            "keys": [f"fuel_ratio_{hi_s}_over_{lo_s}"],
            "title": f"T4 油耗比（SL，Fn={fn} lbf，OPR={opr}）",
            "ask": (f"Solve the SL turbojet design point at Fn_target {fn} lbf, OPR {opr} for "
                    f"T4 {t4_lo} degR and T4 {t4_hi} degR. Write result.json with "
                    f"fuel_ratio_{hi_s}_over_{lo_s} = Wfuel({t4_hi})/Wfuel({t4_lo}). "
                    f"Numeric tolerance 1%."),
        })
    # F5 参数修复（+3）：corrupted OPR + t4/fn 新数值组
    for tid, bad_param, bad_val, good_val, others, cands in (
        ("pc_repair_opr", "opr", 22, 15.0, {"fn_target": 11800, "t4_target": 2370},
         "'fn_target', 't4_target' or 'opr'"),
        ("pc_repair_t4_v2", "t4_target", 1500, 2600, {"fn_target": 12000, "opr": 14.0},
         "'fn_target' or 't4_target'"),
        ("pc_repair_fn_v2", "fn_target", 25000, 13500, {"t4_target": 2500, "opr": 12.5},
         "'fn_target' or 't4_target'"),
    ):
        T.append({
            "tid": tid, "kind": "repair",
            "params": {"bad_param": bad_param, "bad_val": bad_val, "good_val": good_val,
                       "others": others},
            "keys": ["corrupted_param", "restored_value"],
            "title": f"循环参数修复：{bad_param}（新数值组）",
            "ask": (f"A SL turbojet design solve was run with a corrupted parameter: "
                    f"{bad_param} = {bad_val} (physically implausible for this engine class; the true "
                    f"value is one of the standard values for this cycle family). The reference TSFC "
                    f"of the TRUE configuration is given in the prompt. Identify the corrupted parameter "
                    f"and its true value by testing restorations with pycycle. Write result.json with "
                    f"corrupted_param (exact string: {cands}) and restored_value "
                    f"(true numeric value). Exact-match grading."),
        })
    return T


def gold_body(t: dict) -> str:
    """生成 gold __main__ 主体：必须是可赋值的单表达式或语句块。"""
    p = t["params"]
    if t["kind"] == "design":
        return f"r = te.solve_design({p['fn_target']}, {p['t4_target']}, {p['opr']})"
    if t["kind"] == "multi":
        if "oprs" in p:
            base = p["base"]
            return f"""_out = {{}}
for _opr in {p['oprs']}:
    _r = te.solve_design({base['fn_target']}, {base['t4_target']}, _opr)
    _out[f"tsfc_opr{{str(_opr).replace('.', '')}}"] = _r["TSFC"]
_xs = {p['oprs']}
_ys = [_out[f"tsfc_opr{{str(x).replace('.', '')}}"] for x in _xs]
_n = len(_xs)
_out["dtsfc_dopr"] = (_n * sum(x*y for x, y in zip(_xs, _ys)) - sum(_xs)*sum(_ys)) / (_n*sum(x*x for x in _xs) - sum(_xs)**2)
r = _out"""
        if "t4s" in p:
            base = p["base"]
            return f"""_r1 = te.solve_design({base['fn_target']}, {p['t4s'][0]}, {base['opr']})
_r2 = te.solve_design({base['fn_target']}, {p['t4s'][1]}, {base['opr']})
r = {{"fuel_ratio_t2600_over_t2200": _r2["Wfuel_lbm_s"] / _r1["Wfuel_lbm_s"]}}"""
    if t["kind"] == "t4sweep":
        base = p["base"]
        return f"""_out = {{}}
for _t4 in {p['t4s']}:
    _r = te.solve_design({base['fn_target']}, _t4, {base['opr']})
    _out[f"tsfc_t4{{int(_t4)}}"] = _r["TSFC"]
_xs = {p['t4s']}
_ys = [_out[f"tsfc_t4{{int(x)}}"] for x in _xs]
_n = len(_xs)
_out["dtsfc_dt4"] = (_n * sum(x*y for x, y in zip(_xs, _ys)) - sum(_xs)*sum(_ys)) / (_n*sum(x*x for x in _xs) - sum(_xs)**2)
r = _out"""
    if t["kind"] == "fnsweep":
        base = p["base"]
        return f"""_out = {{}}
for _fn in {p['fns']}:
    _r = te.solve_design(_fn, {base['t4_target']}, {base['opr']})
    _out[f"wfuel_fn{{int(_fn)}}"] = _r["Wfuel_lbm_s"]
_xs = {p['fns']}
_ys = [_out[f"wfuel_fn{{int(x)}}"] for x in _xs]
_n = len(_xs)
_out["dwfuel_dfn"] = (_n * sum(x*y for x, y in zip(_xs, _ys)) - sum(_xs)*sum(_ys)) / (_n*sum(x*x for x in _xs) - sum(_xs)**2)
r = _out"""
    if t["kind"] == "ratio":
        base = p["base"]
        return f"""_r1 = te.solve_design({base['fn_target']}, {p['t4s'][0]}, {base['opr']})
_r2 = te.solve_design({base['fn_target']}, {p['t4s'][1]}, {base['opr']})
r = {{"{p['key']}": _r2["Wfuel_lbm_s"] / _r1["Wfuel_lbm_s"]}}"""
    if t["kind"] == "repair":
        return f'r = {{"corrupted_param": "{p["bad_param"]}", "restored_value": float({p["good_val"]})}}'
    raise ValueError(t["kind"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--force-refs", action="store_true")
    args = ap.parse_args()

    (DATA / "gold").mkdir(parents=True, exist_ok=True)
    (DATA / "references").mkdir(parents=True, exist_ok=True)
    (DATA / "hidden").mkdir(parents=True, exist_ok=True)
    TASKS_DIR.mkdir(parents=True, exist_ok=True)

    tasks = task_defs()
    from .common import sha256_file

    drift = []
    frozen = 0
    for t in tasks:
        _body = gold_body(t)
        _body_ind = "\n    ".join(_body.split("\n"))
        gold_code = _GOLD_TEMPLATE.format(body=_body_ind)
        gold_path = DATA / "gold" / f"{t['tid']}.py"
        ref_path = DATA / "references" / f"{t['tid']}.json"
        yaml_path = TASKS_DIR / f"{t['tid']}.yaml"
        # gold 全量重写为路径可移植版（含存量 7 题：旧版内嵌建集时仓库绝对路径，
        # 搬迁后失效；模板不再含绝对路径，--check 严格逐字节比对。
        # 存量 refs/YAML/MD 冻结不重写，等效性由重跑对锁定 references 验证）。
        if not args.check:
            gold_path.write_text(gold_code, encoding="utf-8")
        elif not gold_path.exists() or gold_path.read_text() != gold_code:
            drift.append(t["tid"])
        if args.check:
            continue
        # 存量任务（YAML 已在库）逐字节冻结：跳过 refs/prompt/YAML/MD 全部再生
        if yaml_path.exists():
            frozen += 1
            print(f"[frozen] {t['tid']} (存量不重写)")
            continue
        if args.force_refs or not ref_path.exists():
            with tempfile.TemporaryDirectory() as td:
                refs = run_gold(gold_code, Path(td), _VENV_PY)
            ref_path.write_text(json.dumps(refs, indent=1, sort_keys=True), encoding="utf-8")
        refs = json.loads(ref_path.read_text())

        # repair 任务需要参考 TSFC 上下文
        extra_note = ""
        if t["kind"] == "repair":
            p = t["params"]
            good = {**p["others"], p["bad_param"]: p["good_val"]}
            with tempfile.TemporaryDirectory() as td:
                ctx_code = _GOLD_TEMPLATE.format(body=(
                    f"te.solve_design({good['fn_target']}, {good['t4_target']}, {good['opr']})"))
                ctx = run_gold(ctx_code, Path(td), _VENV_PY)
            extra_note = f"\nReference TSFC of the TRUE configuration: {ctx['TSFC']:.5f}\n"
        prompt = (f"# {t['title']}\n\n{t['ask']}{extra_note}\n\n"
                  "Environment: om-pycycle (source install) + openmdao are importable as "
                  "`import pycycle.api as pyc`. Write result.json to the current working directory.\n"
                  "Respond with a single ```python code block and nothing else.\n")
        prompt_sha = hashlib.sha256(prompt.encode()).hexdigest()
        spec = {
            "id": t["tid"],
            "registry_id": "pycycle.engine_cycle",
            "domain": "propulsion",
            "task_type": "simulation_agent",
            "model_profile": "plain_llm",
            "assets_revision": ASSETS_REVISION,
            "environment_digest": "computed-at-runtime",
            "hidden": False,
            "allowed_tools": ["python", "pycycle"],
            "input": {"prompt_file": f"tasks/pycycle.engine_cycle/{t['tid']}.md",
                      "prompt_sha256": prompt_sha, "assets": []},
            "output_contract": ["result.json"],
            "reference": {
                "source": "gold 脚本预计算（官方 simple_turbojet 模型，om-pycycle Apache-2.0）",
                "revision": ASSETS_REVISION, "values": refs, "rel_tol": REL_TOL,
                "uncertainty_note": "确定性循环求解；容差覆盖数值口径差",
            },
            "grader": {
                "answer_format": "code",
                "exec_kind": "pycycle_cycle",
                "validity_gate": True,
                "result_keys": t["keys"],
                "numeric_rel_tol": REL_TOL,
                "exact_keys": ["corrupted_param", "restored_value", "best_alt_ft"],
                "solver_backend": "pycycle-analysis-venv",
                "oracle_source": f"data/pycycle/engine_cycle/gold/{t['tid']}.py",
                "sandbox": {"banned": "network/process/ctypes", "isolated_interpreter": True},
            },
            "scoring": {
                "weights": {"physics": 0.6, "requirements": 0.4, "objective": 0.0, "robustness": 0.0},
                "note": "physics=数值字段命中均值（1% 容差）；requirements=result.json 键完备",
            },
            "limits": {"cpu": 4, "memory_gb": 8, "wall_clock_s": 900, "attempts": 3},
            "license_provenance": {
                "source": "自建任务 + om-pycycle (Apache-2.0) 官方示例模型",
                "license": "Apache-2.0 (pycycle 及示例)；任务文本自建",
                "status": "confirmed-repo", "revision": ASSETS_REVISION, "mirror_allowed": True,
                "attribution": "om-pycycle, github.com/openmdao/pycycle",
            },
        }
        (TASKS_DIR / f"{t['tid']}.yaml").write_text(
            yaml.safe_dump(spec, sort_keys=False, allow_unicode=True), encoding="utf-8")
        (TASKS_DIR / f"{t['tid']}.md").write_text(prompt, encoding="utf-8")
        print(f"[gen] {t['tid']}: refs={sorted(refs.keys())}")

    # 隐藏动态（评审件）——2026-08-21 起冻结：answers.b64 已在库即不重算
    if not args.check:
        hidden = DATA / "hidden"
        if not (hidden / "answers.b64").exists():
            rng = random.Random(20260819)
            fn = rng.choice([10000, 11000, 12000, 13000, 14000])
            t4 = rng.choice([2300, 2450, 2600])
            opr = rng.choice([12.0, 13.5, 15.0])
            body = f"te.solve_design({fn}, {t4}, {opr})"
            with tempfile.TemporaryDirectory() as td:
                ans = run_gold(_GOLD_TEMPLATE.format(body=body), Path(td), _VENV_PY)
            blob = {"seed": 20260819, "combo": {"fn": fn, "t4": t4, "opr": opr},
                    "answers": ans}
            (hidden / "answers.b64").write_text(
                base64.b64encode(json.dumps(blob).encode()).decode(), encoding="utf-8")
            (hidden / "README.md").write_text(
                "# pycycle 隐藏动态题（评审件）\n\n"
                "- 参数空间：Fn_target∈{10k..14k}、T4∈{2300,2450,2600}、alt∈{30k,35k,40k}、OPR∈{12,13.5,15}\n"
                "- 种子 20260819；试点 1 例已预计算（answers.b64 base64 隔离）\n"
                "- 评审点：采样密度、轮换策略、泄漏监控阈值\n", encoding="utf-8")
            print(f"[hidden] 1 例试点 (fn={fn},t4={t4},opr={opr}) 已隔离落盘")
        else:
            print("[hidden] answers.b64 已在库，冻结不重算")

    if args.check:
        if drift:
            print(f"[check] gold 不一致: {drift}")
            return 1
        print(f"[check] {len(tasks)} 个任务一致")
        return 0
    print(f"[gen] {len(tasks)} tasks ({frozen} frozen) -> {TASKS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
