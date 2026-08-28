# 工程任务书：平板通道层流算例搭建（plane channel Poiseuille flow）

## 任务

根据本任务书与附图 `drawing.png`（带尺寸标注的通道示意图），从零搭建一个**完整可运行的二维 OpenFOAM 案例目录**，模拟平板通道内的充分发展层流（plane Poiseuille flow），并对速度场进行采样。

交付物为一个标准 OpenFOAM 案例目录，至少包含 `0/`、`constant/`、`system/` 三个子目录，能在 OpenFOAM v2312 环境下依次执行 `blockMesh` 与求解器完成计算。

## 几何与网格要求

- 二维平板通道：通道高 **H = 0.01 m**（y 方向），通道长 **L = 0.12 m**（x 方向），见 `drawing.png`。
- 二维计算：z 方向取一层网格，前后两面设为 `empty`。
- 网格：结构化六面体网格（`blockMesh`），流向与法向均匀剖分即可；建议量级 dx = dy = 5e-4 m（240×20×1）。
- 边界命名建议：`inlet`（x=0）、`outlet`（x=L）、`walls`（上下壁面）、`frontAndBack`。

## 流动介质与边界条件

- 不可压缩牛顿流体，层流，运动粘度 **ν = 5e-5 m²/s**。
- 入口：均匀速度 **U0 = 0.1 m/s**（沿 +x 方向，plug  profile）。
- 出口：压力固定值 0，速度零法向梯度。
- 上下壁面：无滑移。
- 对应的基于通道高的雷诺数 Re_H = U0·H/ν = 20，流动保持层流。

## 求解要求

- 使用二维层流**非定常**求解器（如 `icoFoam`），从 t = 0 积分到流动充分发展并达到定常。
  提示：粘性时间尺度 H²/ν = 2 s，过流时间 L/U0 = 1.2 s，endTime 取 5 s 可保证剖面充分发展；时间步长需保证库朗数 Co < 1。
- `system/blockMeshDict` 需位于 `system/` 下（OpenFOAM v2312 的 `blockMesh` 在此查找）。
- `system/controlDict` 的 `application` 条目必须声明所用求解器。

## 采样要求

- 在 **x/H = 10**（即 x = 0.1 m）处布置一条竖直采样线（probes functionObject），沿 y 方向均布约 20 个采样点，采样速度场 **U**，每个时间步写出。
- 采样输出应落在 `postProcessing/probes/<time>/U`。

## 验收

评分系统将真实运行你提交的案例目录（`blockMesh` → `application` 指定的求解器），然后从采样线最终时刻的数据提取 **centerline_umax**（采样线上 |Ux| 的最大值，单位 m/s），与留出的参考值对账。
