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
    r = _r1 = te.solve_design(11000, 2250, 12.0)
    _r2 = te.solve_design(11000, 2550, 12.0)
    r = {"fuel_ratio_t2550_over_t2250": _r2["Wfuel_lbm_s"] / _r1["Wfuel_lbm_s"]}
    json.dump(r, open("result.json", "w"), indent=1)
