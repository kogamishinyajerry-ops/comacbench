# cfdb.validation 2026-08-29 首批基线（8 任务，7 排除）

> 来源：GLM-CFD-Benchmark（MIT，b26799e）validation 域；判分 = docker opencfd v2312
> 按案例冻结 steps 真实求解 → 宿主冻结 compute_qoi.py 降算 QoI → held_out 逐键容差对账
> （相对+绝对双容差）。排除 7 案例见 data/cfdb/exclusions.json（dam_break /
> naca0012_sa_tmr 按 oracle 满分纪律排除，重纳路径已写明）。

## 结果矩阵

| provider | 任务数 | gate | mean | 备注 |
| --- | --- | --- | --- | --- |
| oracle | 8 | **8/8** | **1.0000** | 判分管线自检满分 ✅（参考算例逐字复制全链路真跑） |
| stub | 8 | 0/8 | 0.0000 | 确定性垃圾脚本全灭于结构门（missing_output）✅ |

## Oracle 逐案明细（全部 QoI 对账命中）

| 案例 | QoI 命中 | 说明 |
| --- | --- | --- |
| backward_facing_step_laminar | 1/1 | 再附长度等 |
| cylinder_re100 | 3/3 | St=0.164 / Cd=1.33 / Cl_rms（涡脱落统计） |
| cylinder_re40 | 2/2 | Re40 定常尾迹 |
| lid_driven_cavity_re400 / re1000 | 1/1+1/1 | 中心线速度剖面 |
| natural_convection_cavity | 1/1 | Nu/温度场 |
| turbulent_channel_retau180 | 1/1 | 摩擦速度/剖面 |
| turbulent_flat_plate | 2/2 | Cf 分布 |

## 排除记录（7，重纳路径见 exclusions.json）

- flat 类 4 例 naca0012/a5/a10/a15：snappy 链几何未镜像（镜像时无 0/constant/system）。
- lid_driven_cavity（族母）：参考算例不完整；族由 re400/re1000 覆盖。
- dam_break：瞬态前锋位置 QoI 取"最近写出时间"场，跨运行 FP/时间步漂移敏感
  （oracle 复现 15.5% vs 上游 15% 容差边界）——违反 oracle 满分纪律。
- naca0012_sa_tmr：上游冻结 solve timeout 600s 在本机 arm64 原生不足（endTime=2000
  实测 55%@600s，block_mesh/solve 本身工作正常）。**最高民机相关案例**——上游上调
  预算后优先重纳（本 harness 判分链路已就绪）。

## 判分链路踩坑（与 verification README 同款记录）

1. coded functionObject 在 root 下拒绝编译 → 容器必须 `--user $(uid:gid)`。
2. 上游 steps 模板有两种变量：`{{ run_dir }}`（挂载根）与 `{{ case_dir }}`（算例目录，
   naca0012_sa_tmr 用）——runner 两者都替换。
3. 零参考 QoI 用上游声明的绝对容差，其余相对容差（per-key 双容差语义）。
