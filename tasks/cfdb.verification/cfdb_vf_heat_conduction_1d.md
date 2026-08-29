# cfdb verification — 1D Steady Heat Conduction with Uniform Heat Source (laplacianFoam)

Lightest-weight verification case: 1D steady heat conduction in a plane wall (L=1 m, 100x1x1 cells), OpenFOAM laplacianFoam, both faces fixedValue T=300 K, uniform volumetric source S=100 K/s (fvOptions scalarSemiImplicitSource, volumeMode specific), DT=alpha=0.1 m^2/s. Reference: closed-form parabola T(x)=300+500*x*(1-x) K (q/k=S/alpha=1000 K/m^2; Incropera & DeWitt plane wall with generation), evaluated point-by-point by reference/generate.py into reference/t_profile.csv. QoI midplane_T = T(L/2) = 425.0 K. Tolerance 1% is a documented domain decision: a v2312 smoke run of this exact case (2026-08-11, opencfd/openfoam-default:2312) showed max profile deviation 0.0125 K and interpolated midplane error 2.7e-7 relative (limited by the transient tail), so 1% is deliberately loose to absorb coarser meshes and shorter endTime variants — not a hidden fudge.

## 交付形式（严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建 `case/` 子目录，
写入完整可运行的 OpenFOAM 算例（至少 `0/`、`constant/`、`system/`，含
`system/controlDict` 且其 `application` 条目声明所用求解器；需要 blockMesh
的算例写 `system/blockMeshDict`）。不要自行运行求解器——判分侧会在
OpenFOAM v2312 环境按案例声明的步骤（blockMesh → 求解器 → 后处理）真实执行，
然后用案例冻结的 QoI 脚本从算例产物提取指标并与留出参考值对账。

## 物理与工况
- flow=None, turbulence=None, dim=None, steady=None
- 工况: (见上)
- 评测 QoI（判分脚本从你的算例产物提取）: midplane_T
- 参考类型: analytical；容差为上游文档化决策（网格/格式耗散），不自报数值。

注意：采样/后处理 functionObject（probes、forces 等）必须按上方描述正确配置，
否则判分脚本将因找不到产物而判 0 分（它不会编造数值）。
