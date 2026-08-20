"""gold 解（aviary 分析模式）。判分参考预计算用；模型不可见。"""
import json
import os
import warnings
from copy import deepcopy

warnings.filterwarnings("ignore")

from aviary.interface.run_aviary import run_aviary
from aviary.models.missions.two_dof_default import phase_info
from aviary.variable_info.variables import Mission

BASE = '/Users/Zhuanz/projects/jerry-personal/JerryDSH/benchmarks/data/aviary/transport_mission/derived/av_grossmass_trade_175400.csv'


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
    for gm, csv in [(165400, '/Users/Zhuanz/projects/jerry-personal/JerryDSH/benchmarks/data/aviary/transport_mission/derived/av_grossmass_trade_165400.csv'), (175400, '/Users/Zhuanz/projects/jerry-personal/JerryDSH/benchmarks/data/aviary/transport_mission/derived/av_grossmass_trade_175400.csv'), (185400, '/Users/Zhuanz/projects/jerry-personal/JerryDSH/benchmarks/data/aviary/transport_mission/derived/av_grossmass_trade_185400.csv')]:
        fuels[gm] = solve(csv, 0.80)["fuel_burn_lbm"]
    r = {
        "fuel_165400_lbm": fuels[165400],
        "fuel_175400_lbm": fuels[175400],
        "fuel_185400_lbm": fuels[185400],
        "min_fuel_grossmass_lbm": float(min(fuels, key=fuels.get)),
    }
    json.dump(r, open("result.json", "w"), indent=1)
