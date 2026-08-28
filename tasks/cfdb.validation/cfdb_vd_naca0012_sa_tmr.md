# cfdb validation — NACA0012 α=0° SA Turbulence Model — TMR Far-Field Drag Verification

Numerical validation against the NASA Turbulence Modeling Resource (TMR) "2D NACA 0012 Airfoil Validation Case", SA model results. Fully turbulent RANS (simpleFoam + SpalartAllmaras), alpha = 0 deg, Re = 6e6 per chord, incompressible equivalent of TMR's "essentially incompressible" M = 0.15 (U_inf = 1 m/s, nu = 1.66667e-7 m2/s, c = 1 m). Reference QoI cd = 0.00819 is the CFL3D value from the TMR SA summary table (7 independent codes on a 897x257 grid with ~500c farfield; code-to-code drag spread 0.00812-0.00830, ~4%). This case is DISTINCT from naca0012_a0, which validates against the Ladson 1988 wind-tunnel experiment (cd = 0.0086): here the ruler is a numerical inter-code reference for the fully turbulent SA model, not an experiment. Mesh: script-generated structured C-grid (gen_mesh.py -> system/blockMeshDict, 51810 cells, TMR altered airfoil definition with sharp TE), farfield only ~20-40c and y+ ~ 65 (wall functions) — both far coarser than the TMR grids. The 25% Cd tolerance honestly reflects this gap (documented domain decision, not a hidden fudge).

## 要求
- 求解器族: OpenFOAM（上游基准使用 ESI v2312 语义）；从零搭建完整可运行案例（0/ constant/ system/ + Allrun），真实求解到 case 指定的终止时刻。
- 物理设定: flow=rans, turbulence=rans_sa, dim=2d, steady=True
- 工况: reynolds=6.0e6, mach=0.15, alpha_deg=0.0
- 输出 QoI: cd
- 参考类型: dns（容差见任务 YAML reference.tolerances；判分用冻结 QoI 脚本）

## 交付
写 result.json，字段为上述 QoI 名（数值，与 QoI 定义单位一致）。
