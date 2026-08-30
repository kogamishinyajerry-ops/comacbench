# cfdb case_setup（evidence 工具通道）— Case Setup: Sod Shock Tube from Engineering Brief (evidence mode)

## 两阶段交付协议（严格遵守）
你的脚本会被判分环境执行**两次**，以工作目录下的标记文件 `.cfdb_assemble` 区分：

**阶段 1（首次执行，无标记）**：在当前目录创建 `case/` 子目录，写入完整可运行的
OpenFOAM 算例（`0/` `constant/` `system/`，`system/controlDict` 的 `application`
声明求解器，并按任务书配置采样/监测 functionObject）。判分环境会在 OpenFOAM
v2312 真实执行该算例（blockMesh → 求解器）：`case/` 内落运行场与
`postProcessing/` 采样输出，各步骤日志（`log.block_mesh`、`log.solve` 等）
落在**工作目录根**。

**阶段 2（二次执行，存在 `.cfdb_assemble` 标记）**：从 `case/` 的**运行产物**提取
原始数据，组装证据包写入当前目录（不得编造/篡改数值——判分将用冻结脚本从证据包
原始数据降算指标并与留出参考对账，自报最终值永不进入判分）：
- manifest.json
- evidence/solver.log
- evidence/mesh_report.txt
- evidence/samples/density_profile.csv

证据文件用 `open()` 逐文件读写（不要 import shutil——沙箱静态检查禁止）。
`manifest.json` 为 JSON 对象（至少含 solver 标识与说明字段）。

---

# 工程任务书：Sod 激波管算例搭建（evidence 模式）

## 任务

根据本任务书与附图 `drawing.png`（带尺寸标注的激波管示意图），用**你环境中可用的任意求解器**（商业 CFD 软件、自研代码、开源求解器均可——评分环境不预装任何求解器，由你自己驱动计算）搭建并求解一个**可压缩激波管（Sod 问题）**，然后按下方"证据包合同"提交证据包。

评分系统不运行你的求解器：它校验证据包的完整性与一致性，并用冻结的归约脚本从你提交的原始密度剖面重新计算 QoI。自报的最终数值不进入评分。

## 物理问题

- 一维直管，**x ∈ [0, 1] m**，膜片位于 **x = 0.5 m**，t = 0 时刻膜片瞬时移除。
- 控制方程：**无粘可压缩 Euler 方程**（不计粘性、不计热传导、无湍流模型）。
- 气体：理想气体，比热比 **γ = 1.4（精确）**。
- 初始状态（两侧气体均静止，u = 0）：

| 区域 | 压力 p | 密度 ρ |
|------|--------|--------|
| 左侧 x < 0.5 | 1 Pa | 1 kg/m³ |
| 右侧 x > 0.5 | 0.1 Pa | 0.125 kg/m³ |

- 管两端（x = 0 与 x = 1）：零法向梯度/透射边界即可——在求解时间内波系不会到达端部。
- 严格一维：横向均匀（二维/三维计算时横向取一层并对称）。

## 求解要求

- **非定常**可压缩求解，从 t = 0 积分到 **t = 0.2 s**。
  提示：注意激波捕捉格式的库朗数限制（显式格式建议 Co ≤ 0.2）；网格建议沿管长 1000 个均匀单元（不得粗于 200 个）。
- 取 **t = 0.2 s** 时刻沿管长的**密度剖面**作为证据数据。

## 证据包合同（submission 目录布局 v1）

```
submission/
  manifest.json
  evidence/
    solver.log
    mesh_report.txt
    samples/
      density_profile.csv
```

### `manifest.json`（必需）

JSON object，至少含非空字符串字段 `solver`（求解器名称与版本，溯源锚点）。推荐完整形态：

```json
{
  "solver": "<求解器名称 版本>",
  "mesh_cells": 1000,
  "timing": {"wall_time_sec": 3.1},
  "notes": "自由文本备注"
}
```

`timing.wall_time_sec` 为自报求解墙钟（秒），用于预算门；缺省时预算门语义降级（只门宿主机归约耗时）。

### `evidence/solver.log`（必需，非空）

求解器原生日志文本，应包含时间步推进与残差/守恒量信息（原样拷贝求解器输出即可，不要手工编辑）。

### `evidence/mesh_report.txt`（必需，非空）

网格摘要文本：单元总数、网格类型、质量指标。

### `evidence/samples/density_profile.csv`（必需）

t = 0.2 s 时刻的密度剖面，UTF-8 CSV，首行表头，恰好两列：

| 列 | 含义 | 单位 | 要求 |
|----|------|------|------|
| `x` | 采样点坐标（沿管长） | m | 严格递增，覆盖 [0, 1]，至少 200 个点 |
| `rho` | 该点密度 | kg/m³ | 有限数值，不得为 NaN/Inf |

采样点取单元中心或节点均可。示例（前 3 行）：

```csv
x,rho
0.0005,1.0
0.0015,1.0
```

## 通用一致性校验（评分系统强制）

- 所有必需文件存在且非空；
- `manifest.json` 可解析且含非空 `solver` 字段；
- 所有 CSV 可解析，数值单元格不得为 NaN/Inf；
- 表头为 time/t/iter/iteration/step/timestep 的列（本任务不需要此类列）必须全数值且单调非降。

## 验收

归约脚本从你提交的密度剖面重新计算两个 QoI：**shock_x_t02**（t = 0.2 s 激波位置 = 密度跳变最大的相邻采样点对的中点坐标，单位 m）与 **rho_plateau_t02**（最接近探针 x = 0.6 m 处的采样点密度，即星区密度平台，单位 kg/m³），与留出的精确 Riemann 参考值对账；QoI 相对误差均值作为连续分（越小越好），另设 QoI 完整性与预算两道门。
