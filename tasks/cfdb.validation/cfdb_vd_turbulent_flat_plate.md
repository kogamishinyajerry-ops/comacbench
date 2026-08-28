# cfdb validation — Turbulent Flat Plate (kOmegaSST, Re_x up to 2e6)

Zero-pressure-gradient turbulent flat plate, OpenFOAM simpleFoam + kOmegaSST, 2D steady RANS (L=2 m plate, U_inf=10 m/s, nu=1e-5 so Re_x=1e6/m, plate spans Re_x=0..2e6). Reference: engineering 1/7-power-law correlation Cf=0.0592*Re_x^(-1/5) (valid 5e5<Re_x<1e7), generated pointwise by reference/generate.py — an engineering correlation, NOT raw experimental data (declared openly in provenance). Inlet turbulence: intensity 5% + mixing length 0.01 m (turbulentIntensityKineticEnergyInlet / turbulentMixingLengthFrequencyInlet). y+ control: y-grading ratio 18 over Ny=60 gives first-cell-centre y+ ~ 28-33 (wall-function regime, nutkWallFunction/omegaWallFunction); ~18 cells inside the trailing-edge boundary layer. QoI: station Cf at Re_x=5e5 (x=0.5 m) and Re_x=1e6 (x=1.0 m), from wallShearStress on the plate patch. Tolerance 15% reflects the coarse 6000-cell demo mesh (documented domain decision, not a hidden fudge).

## 要求
- 求解器族: OpenFOAM（上游基准使用 ESI v2312 语义）；从零搭建完整可运行案例（0/ constant/ system/ + Allrun），真实求解到 case 指定的终止时刻。
- 物理设定: flow=incompressible, turbulence=rans_kwsst, dim=2d, steady=True
- 工况: reynolds=2000000.0
- 输出 QoI: cf_rex_5e5, cf_rex_1e6
- 参考类型: analytical（容差见任务 YAML reference.tolerances；判分用冻结 QoI 脚本）

## 交付
写 result.json，字段为上述 QoI 名（数值，与 QoI 定义单位一致）。
