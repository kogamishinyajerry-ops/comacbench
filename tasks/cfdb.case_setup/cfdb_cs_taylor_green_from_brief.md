# cfdb case_setup（evidence 工具通道）— Case Setup: Taylor-Green Decaying Vortex from Engineering Brief (evidence mode)

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
- evidence/samples/ke_history.csv
- evidence/samples/line_end.csv

证据文件用 `open()` 逐文件读写（不要 import shutil——沙箱静态检查禁止）。
`manifest.json` 为 JSON 对象（至少含 solver 标识与说明字段）。

---

# 工程任务书：Taylor-Green 衰减涡算例搭建（evidence 模式）

## 任务

根据本任务书与附图 `drawing.png`（带尺寸标注的计算域示意图），用**你环境中可用的任意求解器**（商业 CFD 软件、自研代码、开源求解器均可——评分环境不预装任何求解器，由你自己驱动计算）搭建并求解一个**二维 Taylor-Green 衰减涡**问题，然后按下方"证据包合同"提交证据包。

评分系统不运行你的求解器：它校验证据包的完整性与一致性，并用冻结的归约脚本从你提交的原始数据（动能历史 + 采样线速度）重新计算 QoI。自报的最终数值不进入评分。

## 物理问题

- 二维计算域 **(x, y) ∈ [0, 2π] × [0, 2π]**（约 6.2832 m 见方），**两个方向均为周期边界**。
- 不可压缩牛顿流体，层流，运动粘度 **ν = 0.01 m²/s**。
- 初始速度场（t = 0，波数 k = 1 1/m，U0 = 1 m/s）：

  u(x, y, 0) = U0 · sin(kx) · cos(ky)
  v(x, y, 0) = −U0 · cos(kx) · sin(ky)

- 对应的雷诺数 Re = U0/(kν) = 100。
- 无外力、无压力驱动：涡在粘性作用下自由衰减。

## 求解要求

- 二维层流**非定常**求解，从 t = 0 积分到 **t = 5 s**。
  提示：显式/半显式格式注意库朗数限制；网格建议 64×64 或更密的均匀网格（周期方向节点数匹配周期长度）。
- 记录**全域动能历史**：KE(t) = 计算域内 ½|u|² 的算术平均（均匀网格下即单元平均；非均匀网格请用体积加权平均并在 mesh_report 里说明），至少包含 **t = 0 与 t = 5 s** 两个时刻，建议每 0.5 s 或更密写出一次。
- 在 **t = 5 s** 时刻，沿水平采样线 **y = 11π/64 ≈ 0.5399613 m**（x 从 0 到 2π）输出速度分量 (u, v)，采样点约 64 个、沿 x 大致均布。

## 证据包合同（submission 目录布局 v1）

```
submission/
  manifest.json
  evidence/
    solver.log
    mesh_report.txt
    samples/
      ke_history.csv
      line_end.csv
```

### `manifest.json`（必需）

JSON object，至少含非空字符串字段 `solver`（求解器名称与版本，溯源锚点）。推荐完整形态：

```json
{
  "solver": "<求解器名称 版本>",
  "mesh_cells": 4096,
  "timing": {"wall_time_sec": 42.0},
  "notes": "自由文本备注"
}
```

`timing.wall_time_sec` 为自报求解墙钟（秒），用于预算门；缺省时预算门语义降级（只门宿主机归约耗时）。

### `evidence/solver.log`（必需，非空）

求解器原生日志文本，应包含时间步推进与残差信息（原样拷贝求解器输出即可，不要手工编辑）。

### `evidence/mesh_report.txt`（必需，非空）

网格摘要文本：单元总数、网格类型、周期边界的配对方式、质量指标。

### `evidence/samples/ke_history.csv`（必需）

全域动能历史，UTF-8 CSV，首行表头，恰好两列：

| 列 | 含义 | 单位 | 要求 |
|----|------|------|------|
| `time` | 物理时刻 | s | 全数值、单调非降；首行必须为 t = 0，末行必须为 t = 5 s（容差 ±0.01 s）；至少 2 行 |
| `ke` | 全域平均动能 ½⟨|u|²⟩ | m²/s² | 有限数值，不得为 NaN/Inf |

示例（前 3 行）：

```csv
time,ke
0,0.25
0.5,0.24505
```

### `evidence/samples/line_end.csv`（必需）

t = 5 s 时刻采样线上的速度，UTF-8 CSV，首行表头，恰好三列：

| 列 | 含义 | 单位 | 要求 |
|----|------|------|------|
| `x` | 采样点 x 坐标 | m | 沿采样线（y = 11π/64）单调递增，覆盖 [0, 2π]，至少 16 个点 |
| `u` | x 方向速度分量 | m/s | 有限数值 |
| `v` | y 方向速度分量 | m/s | 有限数值 |

示例（前 2 行）：

```csv
x,u,v
0.049087,0.037873,-0.464021
```

## 通用一致性校验（评分系统强制）

- 所有必需文件存在且非空；
- `manifest.json` 可解析且含非空 `solver` 字段；
- 所有 CSV 可解析，数值单元格不得为 NaN/Inf；
- 表头为 time/t/iter/iteration/step/timestep 的列（本任务中即 `ke_history.csv` 的 `time` 列）必须全数值且单调非降。

## 验收

归约脚本从你提交的证据重新计算两个 QoI：**ke_ratio_end** = KE(t=5)/KE(t=0)，以及 **u_line_l2_rel_end** = t = 5 s 采样线上 (u, v) 相对参考解的相对 L2 误差，与留出的参考值对账；QoI 误差均值作为连续分（越小越好），另设 QoI 完整性与预算两道门。
