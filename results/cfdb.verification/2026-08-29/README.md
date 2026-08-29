# cfdb.verification 2026-08-29 首批基线（9 任务，1 排除）

> 来源：GLM-CFD-Benchmark（MIT，b26799e）verification 域；判分 = docker opencfd v2312
> 按案例冻结 steps 真实求解 → 宿主冻结 compute_qoi.py 降算 QoI → held_out 逐键容差对账。
> 排除：flat_plate_su2（无 SU2 后端镜像），见 data/cfdb/exclusions.json。

## 结果矩阵

| provider | 任务数 | gate | mean | 备注 |
| --- | --- | --- | --- | --- |
| oracle | 9 | **9/9** | **1.0000** | 判分管线自检满分 ✅（参考算例逐字复制 → 全链路真跑） |
| stub | 9 | 0/9 | 0.0000 | 确定性垃圾脚本全灭于结构门（missing_output），冒烟基线 ✅ |

## Oracle 逐案明细（全部 QoI 对账命中）

| 案例 | QoI 命中 | 说明 |
| --- | --- | --- |
| channel_poiseuille | 1/1 | centerline Umax（0.5% @5%） |
| couette_shear | 1/1 | 壁面速度/剪切 |
| flat_plate_blasius_of | 4/4 | 四站 Cf vs Blasius |
| heat_conduction_1d | 1/1 | 温度剖面 |
| oblique_shock | 1/1 | 激波角 |
| pipe_poiseuille | 2/2 | 管流剖面/压降 |
| sod_shock_tube | 2/2 | 激波位置 0.05% @2% + 平台密度 |
| taylor_couette | 1/1 | 剖面采样 |
| taylor_green_vortex | 2/2 | KE 衰减比 0.8% @5% + 线 L2 误差（绝对容差 0.043 ≤ 0.05） |

## 判分链路定案（2026-08-28/29 踩坑记录）

1. ESI v2312 镜像需显式 `source /usr/lib/openfoam/openfoam2312/etc/bashrc`（Debian 布局）。
2. **coded functionObject 在 root 下拒绝编译**（dynamicCode::checkSecurity）——容器必须
   `--user $(uid:gid)` 非root 运行（taylor_green 实测踩坑），顺带消除 root 属主产物。
3. 零参考 QoI（如 taylor_green 线 L2 误差 held_out=0.0）用上游声明的**绝对容差**，
   其余用相对容差——分支按 per-key 双容差语义实现。
4. 判分信任边界：steps 与 compute_qoi.py 为案例冻结材料（镜像 sha256 锚定），宿主执行，
   自报 QoI 永不进入判分——与 cfdb 上游及本仓库九维度纪律同构。
