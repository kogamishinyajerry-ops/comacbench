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
    r = _out = {}
    for _opr in [11.0, 13.5, 16.0]:
        _r = te.solve_design(12000, 2450, _opr)
        _out[f"tsfc_opr{str(_opr).replace('.', '')}"] = _r["TSFC"]
    _xs = [11.0, 13.5, 16.0]
    _ys = [_out[f"tsfc_opr{str(x).replace('.', '')}"] for x in _xs]
    _n = len(_xs)
    _out["dtsfc_dopr"] = (_n * sum(x*y for x, y in zip(_xs, _ys)) - sum(_xs)*sum(_ys)) / (_n*sum(x*x for x in _xs) - sum(_xs)**2)
    r = _out
    json.dump(r, open("result.json", "w"), indent=1)
