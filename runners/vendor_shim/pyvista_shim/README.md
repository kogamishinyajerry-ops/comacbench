# pyvista import shim（aviary 回归运行口径）

`runners/simulation_agent.py` 无条件 `from .foam_nmse import ...`（foam_nmse 顶层
import pyvista），而 `.venv-aviary`（aviary 1.0.1 钉子栈）不含 pyvista（vtk 太重，
装它会扰动 numpy 2.5 钉子）。aviary/pycycle 分支判分不触任何 pyvista 属性——
本空壳只满足模块级 import，任何真实属性访问会 raise（不静默伪装）。

用法（aviary 回归 / 基线起跑）：
  PYTHONPATH=runners/vendor_shim/pyvista_shim .venv-aviary/bin/python -m runners.simulation_agent ...
（foam NMSE 判分仍必须在 .venv 下跑，shim 会拦住误用。）
