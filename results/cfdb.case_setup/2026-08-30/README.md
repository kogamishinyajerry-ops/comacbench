# cfdb.case_setup 2026-08-30 首批基线（17 任务：16 有 oracle，1 待编写）

> 来源：GLM-CFD-Benchmark（MIT，b26799e）case_setup 域；判分 = managed（判分侧真跑
> v2312）或 evidence 工具通道（两阶段候选协议，Judge runs NO solver）。
> 撤换/排除/踩坑总记录见 data/cfdb/PROVENANCE.md 与 data/cfdb/exclusions.json。

## 结果矩阵

| provider | 任务数 | gate | mean | 备注 |
| --- | --- | --- | --- | --- |
| oracle | 16 | **16/16** | **1.0000** | 全部满分 ✅（managed 2 + evidence 14 两阶段组装） |
| stub | 17 | 0/17 | 0.0000 | 全灭于结构门 ✅（含 cylinder_from_drawing——可执行、无 oracle 背书） |
| glm/minimax | — | — | 待补 | LLM 基线待跑 |

## Oracle 覆盖说明

- **16/16 有 oracle 的任务全部满分**：managed 3（poiseuille/cavity_from/——cylinder 除外）
  + evidence 13（blasius/backward_step/heat/couette/pipe/sod/oblique/taylor_couette/
  taylor_green/natural_convection/naca0012_force/turbulent_channel/turbulent_plate）。
- **cylinder_from_drawing：oracle 待编写**（需按图纸 D 建算例并核对 cd=1.49；
  stub 已证明该任务可被管线执行）。LLM 基线跑全量时其结果无 oracle 背书，需单独标注。

## 踩坑定案（evidence 通道，8 类采样配置实测）

1. ESI v2312 需显式 source /usr/lib/openfoam/openfoam2312/etc/bashrc（Debian 布局）。
2. **coded functionObject 拒绝 root** → 容器必须 --user uid:gid（parabolicInlet 等
   coded BC 同理）；copytree 携带的 stale dynamicCode 必须清除重编译（backward_step）。
3. steps 模板双变量：{{ run_dir }}（挂载根）与 {{ case_dir }}（算例目录）。
4. 零参考 QoI 用绝对容差、其余相对容差（per-key 双容差）。
5. 壁面剪切符号约定：-y 法向壁面上 ESI tau_x 与"阻力方向为正"惯例相反，oracle 按
   标准约定取 -tau_x（backward_step 再附着 2.87 vs 2.922，1.7% @10%）。
6. 竖直台阶面的质心 x≈0 会产生假再附着符号翻转——按面质心 y==0 过滤水平底面。
7. sets 采样输出 = <setname>_<field>.xy（cellPoint + raw），glob 勿假设 .raw。
8. taylor_green 的 KE 历史需前置 t=0 行（0/U 初始场实测，网格精确 KE0）。
