# 任务分析：航程 2600 NM、巡航马赫 0.75

Using the aircraft model CSV provided and Aviary (installed), run a forward mission analysis (run_driver=False) at cruise Mach 0.75. Write result.json with keys fuel_burn_lbm (total mission fuel, lbm) and final_mass_lbm (landing mass, lbm). Numeric tolerance: 1% relative.

Aircraft model CSV (absolute path, read-only): `/Users/Zhuanz/projects/jerry-personal/JerryDSH-COMACBench/data/aviary/transport_mission/derived/av_range_2600_m75.csv`

Aviary 1.0.1 + numpy are installed. IMPORTANT environment constraints:
- call run_aviary(..., run_driver=False, optimizer="SLSQP", verbosity=0, make_plots=False)
  (pyoptsparse/IPOPT is NOT installed; pass optimizer explicitly or import fails)
- cruise Mach is set via phase_info['cruise']['user_options']['mach_cruise'] (deepcopy the default phase_info from aviary.models.missions.two_dof_default first).
Output variables (OpenMDAO promoted names, colon style): 'mission:total_fuel_mass' (lbm), 'mission:final_mass' (lbm), 'mission:range' (NM); read via prob.get_val('mission:total_fuel_mass', units='lbm')[0].
Write the result file to the current working directory as result.json.
Respond with a single ```python code block and nothing else.
