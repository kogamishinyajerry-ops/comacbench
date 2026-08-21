# 航程扫描与燃油敏感度（3000-3600 NM @ M0.8）

Run forward mission analyses (run_driver=False, cruise Mach 0.8) for the four range-variant CSVs provided (3000/3200/3400/3600 NM). Write result.json with keys fuel_3000_lbm, fuel_3200_lbm, fuel_3400_lbm, fuel_3600_lbm and dfuel_drange_lbm_per_nm = least-squares slope of fuel vs range (lbm per NM). Numeric tolerance: 1% relative.


Aviary 1.0.1 + numpy are installed. IMPORTANT environment constraints:
- call run_aviary(..., run_driver=False, optimizer="SLSQP", verbosity=0, make_plots=False)
  (pyoptsparse/IPOPT is NOT installed; pass optimizer explicitly or import fails)
- cruise Mach is set via phase_info['cruise']['user_options']['mach_cruise'] (deepcopy the default phase_info from aviary.models.missions.two_dof_default first).
Output variables (OpenMDAO promoted names, colon style): 'mission:total_fuel_mass' (lbm), 'mission:final_mass' (lbm), 'mission:range' (NM); read via prob.get_val('mission:total_fuel_mass', units='lbm')[0].
Write the result file to the current working directory as result.json.
Respond with a single ```python code block and nothing else.
