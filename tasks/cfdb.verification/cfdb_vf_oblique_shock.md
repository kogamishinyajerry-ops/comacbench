# cfdb verification — Oblique Shock over a 10° Wedge (M1=2)

Supersonic inviscid flow over a 10° wedge, M1=2, OpenFOAM rhoCentralFoam (transient density-based solver run to its steady long-time limit, ~4 flow-throughs). Reference: exact theta-beta-M weak solution computed by gen_reference.py (beta=39.31384°, M2=1.640526, p2/p1=1.706580; no hand-copied numbers). Gas is the normalised gamma=1.4 gas of the rhoCentralFoam wedge15Ma5 tutorial (T1=1, p1=1, U1=2 => a1≈1). QoI post_shock_mach = |U|/sqrt(gamma*R*T) at the post-shock probe (0.6, 0.15), which sits between the wedge surface (y=0.0705) and the analytical shock (y=0.3276) at x=0.6. Tolerance 5% reflects the coarse 12500-cell demo mesh (shock smeared over a few cells; documented domain decision, not a hidden fudge).

## 交付形式（严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建 `case/` 子目录，
写入完整可运行的 OpenFOAM 算例（至少 `0/`、`constant/`、`system/`，含
`system/controlDict` 且其 `application` 条目声明所用求解器；需要 blockMesh
的算例写 `system/blockMeshDict`）。不要自行运行求解器——判分侧会在
OpenFOAM v2312 环境按案例声明的步骤（blockMesh → 求解器 → 后处理）真实执行，
然后用案例冻结的 QoI 脚本从算例产物提取指标并与留出参考值对账。

## 物理与工况
- flow=compressible, turbulence=none, dim=2d, steady=True
- 工况: mach=2.0
- 评测 QoI（判分脚本从你的算例产物提取）: post_shock_mach
- 参考类型: analytical；容差为上游文档化决策（网格/格式耗散），不自报数值。

注意：采样/后处理 functionObject（probes、forces 等）必须按上方描述正确配置，
否则判分脚本将因找不到产物而判 0 分（它不会编造数值）。
