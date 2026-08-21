# T4 扫描与 TSFC 敏感性（SL）

Solve the SL turbojet design point at Fn_target 12500 lbf, OPR 14.0 for T4 2350 / 2550 / 2750 degR. Write result.json with tsfc_t42350, tsfc_t42550, tsfc_t42750 and dtsfc_dt4 = least-squares slope of TSFC vs T4 (1/degR). Numeric tolerance 1%.

Environment: om-pycycle (source install) + openmdao are importable as `import pycycle.api as pyc`. Write result.json to the current working directory.
Respond with a single ```python code block and nothing else.
