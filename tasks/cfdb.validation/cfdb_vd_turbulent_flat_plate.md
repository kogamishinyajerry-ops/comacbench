# cfdb validation — Turbulent Flat Plate (kOmegaSST, Re_x up to 2e6)

Zero-pressure-gradient turbulent flat plate, OpenFOAM simpleFoam + kOmegaSST, 2D steady RANS (L=2 m plate, U_inf=10 m/s, nu=1e-5 so Re_x=1e6/m, plate spans Re_x=0..2e6). Reference: engineering 1/7-power-law correlation Cf=0.0592*Re_x^(-1/5) (valid 5e5<Re_x<1e7), generated pointwise by reference/generate.py — an engineering correlation, NOT raw experimental data (declared openly in provenance). Inlet turbulence: intensity 5% + mixing length 0.01 m (turbulentIntensityKineticEnergyInlet / turbulentMixingLengthFrequencyInlet). y+ control: y-grading ratio 18 over Ny=60 gives first-cell-centre y+ ~ 28-33 (wall-function regime, nutkWallFunction/omegaWallFunction); ~18 cells inside the trailing-edge boundary layer. QoI: station Cf at Re_x=5e5 (x=0.5 m) and Re_x=1e6 (x=1.0 m), from wallShearStress on the plate patch. Tolerance 15% reflects the coarse 6000-cell demo mesh (documented domain decision, not a hidden fudge).

## 交付形式（严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建 `case/` 子目录，
写入完整可运行的 OpenFOAM 算例（至少 `0/`、`constant/`、`system/`，含
`system/controlDict` 且其 `application` 条目声明所用求解器；需要 blockMesh
的算例写 `system/blockMeshDict`）。不要自行运行求解器——判分侧会在
OpenFOAM v2312 环境按案例声明的步骤（blockMesh → 求解器 → 后处理）真实执行，
然后用案例冻结的 QoI 脚本从算例产物提取指标并与留出参考值对账。

## 物理与工况
- flow=incompressible, turbulence=rans_kwsst, dim=2d, steady=True
- 工况: reynolds=2000000.0
- 评测 QoI（判分脚本从你的算例产物提取）: cf_rex_5e5, cf_rex_1e6
- 参考类型: analytical；容差为上游文档化决策（网格/格式耗散），不自报数值。

注意：采样/后处理 functionObject（probes、forces 等）必须按上方描述正确配置，
否则判分脚本将因找不到产物而判 0 分（它不会编造数值）。
