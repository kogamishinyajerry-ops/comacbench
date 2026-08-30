# cfdb case_setup（evidence 工具通道）— Case Setup: Planar Couette Flow from Engineering Brief (evidence mode)

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

# 工程任务书：平面 Couette 剪切流算例搭建(evidence 模式)

## 任务

根据本任务书与附图 `drawing.png`(带尺寸标注的几何示意),在你自己的计算环境里用**任意 CFD 求解器**(商业软件、自研程序或开源求解器均可)从零搭建并求解一个平面 Couette 剪切流算例,然后按本任务书第 4 节的合同提交一个**证据包**。评审方不运行任何求解器:评分系统只校验证据包的一致性,并用冻结脚本从你提交的原始采样数据重新归约出 QoI 打分。**自报的最终 QoI 数字不进入评分。**

## 1. 几何与流动

- 两块无限大平行平板,间距 **H = 0.01 m**(y 方向)。下板静止,上板以 **U_lid = 0.1 m/s** 沿 +x 方向匀速滑动。
- 建议计算域取二维直通道:流向长度 L = 0.01 m(= H),流向两端设周期边界;等价的充分发展通道建模也可接受,但必须在 manifest 的 notes 里说明。
- 介质:不可压缩牛顿流体,运动粘度 **ν = 5e-5 m²/s**,层流。基于间距的雷诺数 Re_H = U_lid·H/ν = 20。
- 初始状态:流体静止。t = 0 时刻上板突然起动,粘性时间尺度 H²/ν = 2 s,瞬态积分至定常(建议 t ≥ 10 s,即 5 个粘性时间;定常判据:剖面不再随时间变化)。
- 定常解析解为线性剖面 u(y) = U_lid·y/H(本任务书不给出该结论以外的任何数值答案)。

## 2. 网格要求

- 二维网格,建议跨隙方向均布不少于 40 个单元;流向若干单元即可(流向均匀流)。
- 网格规模与质量摘要需写入证据包(见第 4 节 mesh_report.txt)。

## 3. 采样要求

- 在最终(定常)时刻,沿一条从静止壁到运动壁的竖直采样线提取流向速度剖面(因流向均匀,采样线的 x 位置任意)。
- 采样点**必须覆盖整条间隙**:第一个点在静止壁面上(y = 0),最后一个点在运动壁面上(y = H),总数不少于 10 个点,按 y 升序。
- 采样值为求解器原生的剖面取值(节点值或单元中心插值均可,但壁面端点必须取壁面边界值——正确无滑移壁面上 u = 0 与 u = U_lid)。

## 4. 证据包合同(交付物)

提交一个名为 `submission/` 的目录,布局如下(v1 统一布局):

```
submission/
  manifest.json              # 证据包清单(JSON object)
  evidence/
    solver.log               # 求解器原生日志,须含残差历史
    mesh_report.txt          # 网格报告:单元总数、类型、质量摘要
    samples/
      profile.csv            # 定常时刻壁法向速度剖面(见下列格式)
```

### manifest.json

JSON object,字段:

- `solver`(字符串,必填):求解器名称与版本,例如 "SomeSolver 2024 R1"。这是证据模式的可追溯锚。
- `mesh_cells`(整数):网格单元总数。
- `timing.wall_time_sec`(数值):求解阶段的自报墙钟秒数。评审的时限门消费这个自报值(语义减弱,靠诚信与生产环境锚定),请务必如实填写。
- `notes`(字符串,可选):建模补充说明(周期边界实现方式、定常判据等)。

### evidence/samples/profile.csv(核心数据文件)

- 表头恰好为 `y,u` 两列:
  - `y`:距**静止壁**的壁法向距离,单位 m;首行必须为 0,末行必须为 0.01。
  - `u`:该处流向速度,单位 m/s。
- 纯数值、UTF-8、英文小数点;不得出现 NaN/Inf;不得空行缺值。
- 注意:评审的通用 CSV 检查要求任何名为 time/t/iter/iteration/step/timestep 的列全数值且单调非降——本文件不要使用时间/迭代列,稳定状态只提交最终剖面。

### evidence/solver.log 与 evidence/mesh_report.txt

- `solver.log`:求解器原生文本日志,须能看出求解器身份、时间推进过程和逐步入残差;不接受手写伪造摘要。
- `mesh_report.txt`:文本,至少含单元总数(须与 manifest 的 mesh_cells 一致)与网格质量摘要(如正交性/纵横比,按求解器原生报告)。

## 5. 验收

评分系统依次:① 校验上述文件齐备且非空;② 解析 manifest 与全部 CSV(任何 CSV 解析失败、NaN/Inf、时间列非单调即判 invalid);③ 用冻结脚本从 `profile.csv` 归约 QoI **bottom_wall_shear_normalized** = 静止壁处剖面斜率 (du/dy|₀) 除以 U_lid/H,与留出参考值对账。解析参考值为 1.0(线性剖面在任意网格上精确成立)。评分只看从证据归约出的数字。
