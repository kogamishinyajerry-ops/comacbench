"""gold 解（aviary 分析模式）。判分参考预计算用；模型不可见。"""
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


if __name__ == "__main__":
    fuels = {}
    for rg, csv in [(2400, 'derived/av_range_sweep_2400.csv'), (2800, 'derived/av_range_sweep_2800.csv'), (3200, 'derived/av_range_sweep_3200.csv'), (3600, 'derived/av_range_sweep_3600.csv')]:
        fuels[rg] = solve(_p(csv), 0.80)["fuel_burn_lbm"]
    xs = [2400, 2800, 3200, 3600]
    ys = [fuels[x] for x in xs]
    n = len(xs)
    slope = (n * sum(x * y for x, y in zip(xs, ys)) - sum(xs) * sum(ys)) / (
        n * sum(x * x for x in xs) - sum(xs) ** 2)
    r = {f"fuel_{rg}_lbm": fuels[rg] for rg in (2400, 2800, 3200, 3600)}
    r["dfuel_drange_lbm_per_nm"] = slope
    json.dump(r, open("result.json", "w"), indent=1)
