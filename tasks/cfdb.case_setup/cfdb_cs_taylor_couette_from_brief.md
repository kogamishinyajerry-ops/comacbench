# cfdb case_setup（evidence 工具通道）— Case Setup: Taylor-Couette Circular Couette from Engineering Brief (evidence mode)

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
- evidence/samples/profile.csv

证据文件用 `open()` 逐文件读写（不要 import shutil——沙箱静态检查禁止）。
`manifest.json` 为 JSON 对象（至少含 solver 标识与说明字段）。

---

# 工程任务书:同心圆筒 Taylor-Couette 层流算例搭建(evidence 模式)

## 任务

根据本任务书与附图 `drawing.png`(带尺寸标注的几何示意),在你自己的计算环境里用**任意 CFD 求解器**(商业软件、自研程序或开源求解器均可)从零搭建并求解一个同心圆筒间层流圆 Couette(Taylor-Couette 失稳前)算例,然后按本任务书第 4 节的合同提交一个**证据包**。评审方不运行任何求解器:评分系统只校验证据包的一致性,并用冻结脚本从你提交的原始采样数据重新归约出 QoI 打分。**自报的最终 QoI 数字不进入评分。**

## 1. 几何与流动

- 两个同轴圆筒:内筒半径 **R_i = 0.05 m**,外筒半径 **R_o = 0.10 m**,见 `drawing.png`。
- 取二维环形截面建模(该流动严格二维,轴向均匀);若用三维建模需保证轴向周期/足够长并在 manifest 的 notes 里说明。
- 介质:不可压缩牛顿流体,运动粘度 **ν = 1e-3 m²/s**,层流。
- 边界条件:
  - 内筒(r = R_i):刚体旋转,角速度 **ω = 1 rad/s**(壁面线速度 ω·R_i = 0.05 m/s,沿 +θ 方向)。
  - 外筒(r = R_o):静止,无滑移。
- 雷诺数 Re = ω·R_i·(R_o−R_i)/ν = 2.5,远低于 Taylor 涡失稳临界,流动保持定常轴对称层流。
- 初始状态:流体静止。t = 0 内筒突然起动,间隙扩散时间尺度 (R_o−R_i)²/ν = 2.5 s,瞬态积分至定常(建议 t ≥ 10 s;时间步长注意脉冲起动瞬态的稳定性,建议按壁面库朗数 Co < 0.2 取值)。
- 定常解析剖面为 u_θ(r) = A·r + B/r(A、B 由两壁面无滑移条件定,本任务书不给出数值答案)。

## 2. 网格要求

- 建议量级:径向不少于 20 单元、周向每 90° 不少于 30 单元(均布即可)。
- 网格规模与质量摘要需写入证据包(见第 4 节 mesh_report.txt)。

## 3. 采样要求

- 在最终(定常)时刻,沿一条从内筒到外筒的**径向采样线**提取切向速度剖面。
- 采样线取在 +x 轴射线上(θ = 0 处);此处切向即 +y 方向,笛卡尔分量与切向分量直接对应,便于任何求解器导出。u_θ 符号约定:沿内筒旋转方向为正。
- 采样点不少于 10 个,按 r 升序,全部位于 R_i ≤ r ≤ R_o 内;**必须包含中隙站位 r = 0.075 m** 的采样点(建议均布 1 mm 间距,即 r = 0.051, 0.052, ..., 0.099 m 共 49 点,天然覆盖中隙)。
- 采样值为求解器原生的剖面取值(节点值或单元中心插值均可)。

## 4. 证据包合同(交付物)

提交一个名为 `submission/` 的目录,布局如下(v1 统一布局):

```
submission/
  manifest.json              # 证据包清单(JSON object)
  evidence/
    solver.log               # 求解器原生日志,须含残差历史
    mesh_report.txt          # 网格报告:单元总数、类型、质量摘要
    samples/
      profile.csv            # 定常时刻径向切向速度剖面(见下列格式)
```

### manifest.json

JSON object,字段:

- `solver`(字符串,必填):求解器名称与版本。这是证据模式的可追溯锚。
- `mesh_cells`(整数):网格单元总数。
- `timing.wall_time_sec`(数值):求解阶段的自报墙钟秒数。评审的时限门消费这个自报值(语义减弱,靠诚信与生产环境锚定),请务必如实填写。
- `notes`(字符串,可选):建模补充说明(二维/三维、旋转壁实现方式、定常判据等)。

### evidence/samples/profile.csv(核心数据文件)

- 表头恰好为 `r,u_theta` 两列:
  - `r`:距共同轴线的径向距离,单位 m;必须含 r = 0.075 的行。
  - `u_theta`:该处切向速度(沿内筒旋转方向为正),单位 m/s。
- 纯数值、UTF-8、英文小数点;不得出现 NaN/Inf;不得空行缺值。
- 注意:评审的通用 CSV 检查要求任何名为 time/t/iter/iteration/step/timestep 的列全数值且单调非降——本文件不要使用时间/迭代列,定常状态只提交最终剖面。

### evidence/solver.log 与 evidence/mesh_report.txt

- `solver.log`:求解器原生文本日志,须能看出求解器身份、时间推进过程和逐步残差;不接受手写伪造摘要。
- `mesh_report.txt`:文本,至少含单元总数(须与 manifest 的 mesh_cells 一致)与网格质量摘要(按求解器原生报告)。

## 5. 验收

评分系统依次:① 校验上述文件齐备且非空;② 解析 manifest 与全部 CSV(任何 CSV 解析失败、NaN/Inf、时间列非单调即判 invalid);③ 用冻结脚本从 `profile.csv` 归约 QoI **utheta_midgap**(r = 0.075 m 处的 u_θ,解析参考为闭式解 A·r+B/r 在该半径的值),与留出参考值对账。评分只看从证据归约出的数字。
