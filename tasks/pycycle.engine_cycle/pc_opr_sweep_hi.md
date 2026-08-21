# OPR 扫描与 TSFC 敏感性（SL，高推力基点）

Solve the SL turbojet design point at Fn_target 15000 lbf, T4 2800 degR for OPR 11.5 / 14 / 16. Write result.json with tsfc_opr115, tsfc_opr140, tsfc_opr160 and dtsfc_dopr = least-squares slope of TSFC vs OPR. Numeric tolerance 1%.

Environment: om-pycycle (source install) + openmdao are importable as `import pycycle.api as pyc`. Write result.json to the current working directory.
Respond with a single ```python code block and nothing else.
