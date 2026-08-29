# cfdb case_setup — 工程任务书

## 交付形式（严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建 `case/` 子目录，
写入完整可运行的 OpenFOAM 算例（至少 `0/`、`constant/`、`system/`，含
`system/controlDict` 且其 `application` 条目声明所用求解器）。不要自行
运行求解器——判分侧会在 OpenFOAM v2312 环境按案例声明步骤真实执行，
再用冻结 QoI 脚本从算例产物降算指标与留出参考对账（自报数值不进判分）。

---

# 算例任务：圆柱绕流（定常层流）

## 物理问题

均匀来流绕过一个静止圆柱（二维、不可压、定常层流）：

- 来流速度：U_inf = 1 m/s，沿 +x 方向；
- 流体运动粘度：ν = 0.025 m²/s（密度可按不可压常用的单位化处理）；
- 圆柱直径 D 见图纸 `drawing.png`；
- 由以上条件，基于圆柱直径的雷诺数 Re = U_inf · D / ν = 40，流动为定常层流，
  尾流中存在稳定的对称分离泡。

## 几何与边界条件

**计算域的几何信息以图纸 `drawing.png` 为唯一完整来源**（本文件不重复全部尺寸）：
圆柱位置、外流场域的范围、各边界的类型（柱面 / 远场 / 前后面）均按图纸标注设置。
算例为二维，展向取单位深度。

## 提交要求

提交一个完整的 OpenFOAM 案例目录，包含 `0/`、`constant/`、`system/` 三个子目录。评测系统将：

1. 若存在 `system/blockMeshDict`，先运行 `blockMesh` 生成网格；
2. 从 `system/controlDict` 的 `application` 条目解析求解器并运行（请选用适合本问题的定常求解器）；
3. 运行冻结的 QoI 提取脚本读取结果。

**输出约定（QoI 提取脚本按此读取，务必遵守）**：在 `system/controlDict` 中配置
`forceCoeffs` 类型的函数对象，对象名必须为 `forceCoeffs1`，作用 patches 为圆柱壁面，
从而求解结束后存在 `postProcessing/forceCoeffs1/<时间步>/coefficient.dat`；
阻力系数 Cd 取该文件最后一个数据行的 Cd 列。Cd 按
Cd = F_x / (0.5 · ρ · U_inf² · A_ref) 定义，参考面积 A_ref = D × 单位展长。

## 待求量（QoI）

- `drag_coeff_cd`：圆柱总阻力系数 Cd（上述定义）。
