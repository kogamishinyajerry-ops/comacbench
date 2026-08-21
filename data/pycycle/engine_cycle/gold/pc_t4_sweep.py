"""gold 解（pycycle turbojet）。判分参考预计算用；模型不可见。"""
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
    r = _out = {}
    for _t4 in [2350, 2550, 2750]:
        _r = te.solve_design(12500, _t4, 14.0)
        _out[f"tsfc_t4{int(_t4)}"] = _r["TSFC"]
    _xs = [2350, 2550, 2750]
    _ys = [_out[f"tsfc_t4{int(x)}"] for x in _xs]
    _n = len(_xs)
    _out["dtsfc_dt4"] = (_n * sum(x*y for x, y in zip(_xs, _ys)) - sum(_xs)*sum(_ys)) / (_n*sum(x*x for x in _xs) - sum(_xs)**2)
    r = _out
    json.dump(r, open("result.json", "w"), indent=1)
