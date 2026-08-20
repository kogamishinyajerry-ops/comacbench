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
    r = r = te.solve_design(15000, 2800, 15.0)
    json.dump(r, open("result.json", "w"), indent=1)
