# 循环参数修复：fn_target（新数值组）

A SL turbojet design solve was run with a corrupted parameter: fn_target = 25000 (physically implausible for this engine class; the true value is one of the standard values for this cycle family). The reference TSFC of the TRUE configuration is given in the prompt. Identify the corrupted parameter and its true value by testing restorations with pycycle. Write result.json with corrupted_param (exact string: 'fn_target' or 't4_target') and restored_value (true numeric value). Exact-match grading.
Reference TSFC of the TRUE configuration: 0.85065


Environment: om-pycycle (source install) + openmdao are importable as `import pycycle.api as pyc`. Write result.json to the current working directory.
Respond with a single ```python code block and nothing else.
