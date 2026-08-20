# OPR 扫描与 TSFC 敏感性（SL）

Solve the SL turbojet design point at Fn_target 12000 lbf, T4 2450 degR for OPR 11 / 13.5 / 16. Write result.json with tsfc_opr110, tsfc_opr135, tsfc_opr160 and dtsfc_dopr = least-squares slope of TSFC vs OPR. Numeric tolerance 1%.

Environment: om-pycycle (source install) + openmdao are importable as `import pycycle.api as pyc`. Write result.json to the current working directory.
Respond with a single ```python code block and nothing else.
