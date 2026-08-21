# 总重权衡：三种设计总重下的燃油（179400/180400/182400 lbm）

Run forward mission analyses (run_driver=False, cruise Mach 0.80) for the three aircraft CSVs provided (design gross mass 179400 / 180400 / 182400 lbm). Write result.json with keys fuel_179400_lbm, fuel_180400_lbm, fuel_182400_lbm and min_fuel_grossmass_lbm (the gross-mass value of the lowest-fuel variant, lbm). Numeric tolerance: 1% relative (min key: exact value match).


Aviary 1.0.1 + numpy are installed. IMPORTANT environment constraints:
- call run_aviary(..., run_driver=False, optimizer="SLSQP", verbosity=0, make_plots=False)
  (pyoptsparse/IPOPT is NOT installed; pass optimizer explicitly or import fails)
- cruise Mach is set via phase_info['cruise']['user_options']['mach_cruise'] (deepcopy the default phase_info from aviary.models.missions.two_dof_default first).
Output variables (OpenMDAO promoted names, colon style): 'mission:total_fuel_mass' (lbm), 'mission:final_mass' (lbm), 'mission:range' (NM); read via prob.get_val('mission:total_fuel_mass', units='lbm')[0].
Write the result file to the current working directory as result.json.
Respond with a single ```python code block and nothing else.
