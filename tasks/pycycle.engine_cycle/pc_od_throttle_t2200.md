# 设计点：SL 静止，Fn_target=11800 lbf，T4=2200°R，OPR=13.5

Using pycycle (installed as om-pycycle), build the simple turbojet cycle (Inlet + AXI5 Compressor + Combustor + LPT2269 Turbine + CD Nozzle + Shaft, TABULAR thermo AIR_JETA_TAB_SPEC, SL design at alt 0 ft MN~0) and solve the DESIGN point: Fn_target 11800 lbf, T4_target 2200 degR, compressor OPR 13.5. Write result.json with keys Fn_lbf (net thrust), TSFC, OPR, Wfuel_lbm_s. Numeric tolerance 1%.

Environment: om-pycycle (source install) + openmdao are importable as `import pycycle.api as pyc`. Write result.json to the current working directory.
Respond with a single ```python code block and nothing else.
