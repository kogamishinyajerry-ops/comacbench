# 模型修复：aircraft:design:range

You are given ONE corrupted aircraft CSV and ONE clean reference table below. A reference forward analysis (cruise Mach 0.80, run_driver=False) of the TRUE model yields the reference fuel burn already provided in result-reference.json. Exactly one row of the corrupted CSV differs from the true model. Candidates:
- aircraft:design:range: range mislabeled 4000 NM (true 3200 NM)
- aircraft:design:gross_mass: gross mass mislabeled (true 175400 lbm)
Identify the corrupted parameter by testing restorations with Aviary and write result.json with keys corrupted_param (exact CSV key string) and restored_value (the true numeric value as float). Exact-match grading.

Aircraft model CSV (absolute path, read-only): `/Users/Zhuanz/projects/jerry-personal/JerryDSH/benchmarks/data/aviary/transport_mission/derived/av_repair_range_corrupt.csv`

Corrupted CSV (absolute path): `/Users/Zhuanz/projects/jerry-personal/JerryDSH/benchmarks/data/aviary/transport_mission/derived/av_repair_range_corrupt.csv`
Reference fuel burn of the TRUE model (lbm): 43389.55
The true model differs from the corrupted one in exactly the candidate row above.

Aviary 1.0.1 + numpy are installed. IMPORTANT environment constraints:
- call run_aviary(..., run_driver=False, optimizer="SLSQP", verbosity=0, make_plots=False)
  (pyoptsparse/IPOPT is NOT installed; pass optimizer explicitly or import fails)
- cruise Mach is set via phase_info['cruise']['user_options']['mach_cruise'] (deepcopy the default phase_info from aviary.models.missions.two_dof_default first).
Output variables (OpenMDAO promoted names, colon style): 'mission:total_fuel_mass' (lbm), 'mission:final_mass' (lbm), 'mission:range' (NM); read via prob.get_val('mission:total_fuel_mass', units='lbm')[0].
Write the result file to the current working directory as result.json.
Respond with a single ```python code block and nothing else.
