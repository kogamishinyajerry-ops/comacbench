# gtm.transport_control 数据溯源（PROVENANCE，自建任务集）

> assets_revision: `gtm-flight@selfbuilt-2026-08-22+matlabR2026a`
> 建集日期: 2026-08-22 · batch-2 会话（dev 终端）

## 自建声明

- **未镜像 GTM_DesignSim**：其本体是 Simulink 工程（工程级依赖）且整体许可
  needs-verification 未核——本任务集不复制其任何文件、参数表或题面。仅"运输机飞控
  定位"受其启发（registry `self_built: true`）。
- **稳定性导数量级取自公开运输机文献典型值**（Heffley NASA CR-2144 DC-8 类巡航量级：
  V 600-820 ft/s、Xu∈[-0.02,-0.005]、Xw∈[0.02,0.06]、Zu∈[-0.05,-0.01]、Zw∈[-0.9,-0.5]、
  Mw∈[-0.008,-0.002]、Mq∈[-1.2,-0.5]；横航向按模态窗口反解最终系数）。任务文本、
  参数组合、判分口径全部自建。
- **判分 100% 本地数值可复现**：每题参考值 = 自建 gold MATLAB 脚本（`gold/<tid>.m`）
  以 `matlab -batch model` 预计算落盘 `references/<tid>.json` 并内嵌任务 YAML；
  numpy 侧独立复算（<1e-6 相对差）防口径漂移。无 LLM judge。

## 环境事实（2026-08-22 实测）

- MATLAB `/Applications/MATLAB_R2026a.app/bin/matlab`（R2026a Update 3，Sponsored
  License）；batch 启动 ~28s/次（任务规格给定事实；本机建集实测单次调用
  10-30s 量级，含许可横幅写 stderr，不影响退出码）。
- 依赖函数面：`eig`/`expm`/`fzero`/`jsonencode` 核心函数 + `place`/`ctrb`
  （Control System Toolbox）。无 Optimization Toolbox 依赖（fsolve 不用）。
- 判分管线：runners/simulation_agent.py `grader.exec_kind=gtm_matlab` 分支
  （模型代码以 model.m 隔离目录执行，写 result.json 判分，口径同 aviary 分支：
  result_keys + numeric_rel_tol=0.01 + exact_keys）。

## 任务族清单（8 族 25 题，`tasks/gtm.transport_control/`）

| 族 | 数量 | tid | 判分键 |
| --- | --- | --- | --- |
| F1 纵向模态 | 5 | lon_01..05 | omega_sp/zeta_sp/omega_ph/zeta_ph |
| F2 配平 | 3 | trim_01..03 | alpha_trim_deg/thrust_lbf |
| F3 静稳定裕度 | 2 | sm_01..02 | static_margin/h_n |
| F4 控制律设计 | 4 | kdesign_01..04 | cl_omega_sp/cl_zeta_sp（判闭环极点不判 K） |
| F5 时域指标 | 3 | tdm_01..03 | rise_time_s/overshoot_pct/settling_time_s |
| F6 模型修复 | 2 | repair_01..02 | corrupted_param(exact)/restored_value(1%) |
| F7 包线鲁棒 | 3 | env_01..03 | 每飞行条件 omega_sp_i/zeta_sp_i（6 键） |
| F8 横航向模态 | 3 | lat_01..03 | dutch_roll_omega/zeta + roll/spiral λ |

## 模态自检与记录在案的偏差

- 生成器对写出的每个 A 强制自验（numpy eig）：纵向恰两对共轭极点、SP
  ωn∈[1.2,2.8] ζ∈[0.25,0.65]；横航向荷兰滚 ωn∈[0.8,1.8] ζ∈[0.05,0.25]、滚转
  实根∈[-2.5,-1.2]、螺旋实根∈[-0.10,-0.05]（全稳定）。
- **phugoid ωn 窗口偏差**：任务规格要求 [0.08,0.25] 且同时给定参数盒——但本结构
  char(0)=g·Zu·Mw ⇒ wn_sp·wn_ph=√(g·|Zu·Mw|)，二者数学不相容（参数盒全域 +
  SP 窗下 wn_ph≤0.06，4 万点 LHS 扫描 max 0.0496）。按"保持规格参数量级"优先，
  自检窗取物理可达包络 [0.025,0.06]（周期 105-250s），模态分离比 >40×，判分
  稳定性不受影响。F8 之 Lβ 量级（-3.9..-8.5）为满足全稳定螺旋窗所需，超出
  文献典型值——规格明示"最终系数直接写死、生成器验证模态"，模态窗口优先。
- F6 判别唯一性逐题验证：对每个候选参数在物理邻域扫 1-D 根（匹配参考 SP ωn 或
  ζ），仅真参数的复原值能同时复现参考 SP ωn 与 ζ。
- F4 判分口径（规格明示）：判闭环极点不判 K——cl_omega_sp/cl_zeta_sp 参考即
  目标值本身（place 精确配置后 eig 复核误差 <1e-6）。

## gold 预计算协议

- `python3 -m runners.gen_tasks_gtm`：渲染 gold/<tid>.m → 逐题
  `runners/solvers/matlab.py::run_matlab`（与判分 oracle 完全同路径：临时目录
  model.m + `matlab -batch model`，串行）→ result.json 即 references/<tid>.json
  → YAML reference.values 内嵌。numpy 复算逐键断言 <1e-6 相对差。
- 幂等：`--check` 对 gold/YAML/MD/references 存在性/PROVENANCE 全量逐字节比对。
- 题面仿真口径（F5）：精确零阶保持离散 Ad=expm(A·dt)、Bd=A\((Ad−I)B)、
  dt=0.01 s、T=30 s；10-90% 上升时间线性插值、2% 带取末次违例采样时刻。

## 重取/复算

```bash
cd benchmarks && python3 -m runners.gen_tasks_gtm --check   # 幂等校验
# 参考重算（--force-refs）：重跑生成器即新评测周期
```
