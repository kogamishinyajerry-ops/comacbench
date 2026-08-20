"""gold 解（pycycle turbojet）。判分参考预计算用；模型不可见。"""
import json
import sys
import warnings

warnings.filterwarnings("ignore")
import matplotlib
matplotlib.use("Agg")

ENGINE = '/Users/Zhuanz/projects/jerry-personal/JerryDSH/benchmarks/data/pycycle/engine_cycle/turbojet_engine.py'
sys.path.insert(0, __import__("os").path.dirname(ENGINE))
import turbojet_engine as te

if __name__ == "__main__":
    r = _r1 = te.solve_design(11800, 2200, 13.5)
    _r2 = te.solve_design(11800, 2600, 13.5)
    r = {"fuel_ratio_t2600_over_t2200": _r2["Wfuel_lbm_s"] / _r1["Wfuel_lbm_s"]}
    json.dump(r, open("result.json", "w"), indent=1)
