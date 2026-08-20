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

## 环境事实（2026-08-19）

- **PyPI `pycycle` 是抢注空壳包**（仅 cli/utils，无发动机模型）——真包须源码安装：
  `pip install -e /path/to/pycycle`（setup 名 `om-pycycle`）。已装 venv；
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
