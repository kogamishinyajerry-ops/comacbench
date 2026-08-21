# Fn 扫描与油耗斜率（SL）

Solve the SL turbojet design point at T4 2450 degR, OPR 13.5 for Fn_target 10500 / 12000 / 13500 lbf. Write result.json with wfuel_fn10500, wfuel_fn12000, wfuel_fn13500 (burner fuel flow, lbm/s) and dwfuel_dfn = least-squares slope of Wfuel vs Fn_target (lbm/s per lbf). Numeric tolerance 1%.

Environment: om-pycycle (source install) + openmdao are importable as `import pycycle.api as pyc`. Write result.json to the current working directory.
Respond with a single ```python code block and nothing else.
