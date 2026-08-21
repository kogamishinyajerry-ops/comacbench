# pycycle.engine_cycle 数据溯源（PROVENANCE，自建任务集）

> assets_revision: `pycycle-pack@selfbuilt-2026-08-19+ompycycle_src`
> 建集日期: 2026-08-19 · batch-2 会话（dev 终端）

## 构成（自建，registry self_built: true）

- **vendored gold 引擎**：`turbojet_engine.py` = om-pycycle 官方示例
  `example_cycles/simple_turbojet.py`（Apache-2.0）+ harness 参数化封装
  `solve_design(fn_target, t4_target, opr)`（viewer/map_plots 剥离——numpy 标量打印兼容；
  官方完整初值序列保证收敛：DESIGN SL 静止 + OD 初值）；
- **7 静态任务**（SL 设计点收敛域内）：3 设计点（Fn/T4/OPR 参数化）+ OPR 敏感性扫描 +
  T4 油耗比 + 2 参数修复；
- 参考：`references/*.json`（gold 预计算锁定，rel_tol 1%）；
- **隐藏动态**：`hidden/answers.b64`（参数空间 Fn∈{10k..14k}/T4∈{2300,2450,2600}/
  OPR∈{12,13.5,15}，种子 20260819，试点 1 例隔离）。

## 环境事实（2026-08-19；2026-08-20 venv 重建并钉版本）

- **PyPI `pycycle` 是抢注空壳包**（仅 cli/utils，无发动机模型）——真包 2026-08-20
  起可直接 `pip install om-pycycle`（4.4.0 已上架，本次 venv 即用）；旧文档的
  `pip install -e /path/to/pycycle` 源码装法仅作历史记录；
- **兼容栈钉子（Python 3.12.13）**：`om-pycycle==4.4.0` + `openmdao==3.34.2` +
  `numpy==1.26.4` + `scipy==1.13.1`——om-pycycle 4.4.0 的 `ThermoAdd.compute` 在
  numpy≥2 下抛 "setting an array element with a sequence"，而 openmdao≥3.35 /
  scipy≥1.14 又要求 numpy≥2，故整套钉在 2024 时代组合（oracle 7/7 实测通过；
  参考解重算勿盲目升级）；
- 收敛域：SL（alt≈0, MN≈0.000001）设计点 + 官方初值 → Fn_target∈[9k,16k]、
  T4∈[2200,2900]、OPR∈[11,16] 稳定收敛（实测 3 组参数全部精确命中 Fn_target）；
  **巡航高度参数化会使 OD 点发散**（官方 od_Fn/od_MN 固定 SL 相邻点）——高度权衡类
  任务未纳入首批（待议：需参数化 OD 点序列）。

## 判分口径（simulation_agent / pycycle_cycle）

与 aviary_mission 同分支：gate = 脚本跑通 + result.json 可解析；physics = 数值字段
相对误差带（1%）；requirements = 键完备；exact_keys（corrupted_param/restored_value）精确匹配。

## 判分器缺陷修正记录（2026-08-19）

- 沙箱裸 `system(`/`popen(` 子串模式误伤 `prob.model.add_subsystem(...)`（OpenMDAO 标准调用）
  ——已移除裸子串模式，`os.system` 全名仍拦。pycycle M3 基线因此重跑。

## 重取/复算

```bash
cd benchmarks && MPLCONFIGDIR=/tmp .venv/bin/python -m runners.gen_tasks_pycycle --check
# 参考重算（--force-refs）：重跑生成器即新评测周期
```

## 2026-08-21 扩题（7 → 28，append-only）

### 新任务清单（+21，全部 gold 在 solve_design 收敛域内真实跑通）

- **设计点网格补密（+9）**：`pc_design_fn10k_t2300_opr12` / `pc_design_fn11k_t2550_opr11` /
  `pc_design_fn13k_t2650_opr13` / `pc_design_fn14k_t2900_opr16` / `pc_design_fn16k_t2350_opr155` /
  `pc_design_fn10p5k_t2750_opr145` / `pc_design_fn13p5k_t2400_opr115` /
  `pc_design_fn14p5k_t2850_opr125` / `pc_design_fn15p5k_t2500_opr135`
  （Fn 10k-16k / T4 2300-2900 / OPR 11-16 域内，避开存量 3 组组合）；
- **油门 T4 变体（+3）**：`pc_od_throttle_t2300` / `pc_od_throttle_t2500` / `pc_od_throttle_t2700`
  （命名沿存量 `pc_od_throttle_t2200` 惯例；**如实降级**——vendored 引擎仅暴露
  `solve_design`（SL 设计解），无参数化 OD 点入口，PROVENANCE 前文已记录巡航/OD
  参数化会发散，故该族为 T4 变体的 SL 设计点重解，非真 OD 求解）；
- **敏感性扫描（+3）**：`pc_opr_sweep_hi`（OPR 11.5/14/16 @ Fn 15k/T4 2800 换基点）、
  `pc_t4_sweep`（T4 2350/2550/2750 @ Fn 12.5k/OPR 14，出 dtsfc_dt4）、
  `pc_fn_sweep`（Fn 10.5k/12k/13.5k @ T4 2450/OPR 13.5，出 dwfuel_dfn；
  SL 设计点下 TSFC 对 Fn 退化不变，故取 Wfuel 为响应量）；
- **油耗比（+3）**：`pc_fuel_ratio_t2700_over_t2300`（11.8k/13.5）、`pc_fuel_ratio_hi`
  （13k/14，T4 2400→2800）、`pc_fuel_ratio_lo`（11k/12，T4 2250→2550）；
- **参数修复（+3）**：`pc_repair_opr`（corrupted OPR=22 → 15.0）、`pc_repair_t4_v2`
  （corrupted T4=1500 → 2600 @ 12k/OPR14）、`pc_repair_fn_v2`（corrupted Fn=25000 →
  13500 @ T4 2500/OPR 12.5）。

### gold 数与路径可移植性修复

- gold 共 **28** 个（21 新增预计算 + 7 存量重写）；references 新增 21 个
  （`references/<tid>.json`，rel_tol=1% 锁定）；
- **存量 gold 路径修复**：旧 gold 内嵌建集时仓库绝对路径
  （`JerryDSH/benchmarks` → 建集后仓库搬迁至 `JerryDSH-COMACBench`）已失效；
  新模板不再内嵌绝对路径（引擎定位 = gold 同目录（沙箱 companion 场景）优先，
  否则上溯一级 `gold/../turbojet_engine.py`），新增 gold 同样全部相对定位；
- **旧 gold 路径修复 + 等效验证 7/7 通过**：修复后逐个重跑，对锁定 references
  全部字段 |Δ|/|ref| ≤ 1.5e-10（多为 ~1e-15，确定性求解复现），exact_keys
  （corrupted_param/restored_value）全部精确一致——等效验证替代字节比对作为完整性证明。

### 不变项声明

- **seed / REL_TOL / ASSETS_REVISION / 判分口径 / 解释器均不变**：`.venv/bin/python`
  （om-pycycle 4.4.0 + openmdao 3.34.2 钉子栈），stub/oracle 均以 `--seed 0`；
- **存量 7 题任务契约逐字节冻结**：`tasks/pycycle.engine_cycle/*.yaml|*.md` 与
  `references/*.json` 未重写（git diff 为空）；hidden/（answers.b64）冻结不重算。

### 全量回归（2026-08-21，`--seed 0`）

- stub：`results/pycycle.engine_cycle/2026-08-21/stub/` —— 28/28 gate fail
  （missing_output），**全 0 分地板确认**；
- oracle：`results/pycycle.engine_cycle/2026-08-21/oracle/` —— **28/28 全 score=1.0**
  （physics 命中 100%，含 4 个 sweep/ratio 单键题与 3 个 repair exact 题）。
