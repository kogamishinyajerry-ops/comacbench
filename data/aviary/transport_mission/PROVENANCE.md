# aviary.transport_mission 数据溯源（PROVENANCE，自建任务集）

> assets_revision: `aviary-mission@selfbuilt-2026-08-19+aviary1.0.1`
> 建集日期: 2026-08-19 · M3 会话（dev 终端）

## 任务集构成（自建，registry self_built: true）

- 基准模型：NASA Aviary 自带 `aircraft_for_bench_GwGm.csv`（Apache-2.0，venv 1.0.1 内拷贝
  至 `base/`，sha256 随 run_manifest 校验）；
- 派生模型：`derived/*.csv`（参数化改动 range/gross_mass，`_modify_csv` 幂等生成）；
- 8 静态任务：3 任务分析（range×mach）+ 1 总重权衡 + 1 航程扫描敏感度 + 2 模型修复 + 1 燃油比；
- 参考：`references/*.json`（gold 分析模式预计算锁定，rel_tol=1%）；
- gold：`gold/*.py`（run_driver=False 确定性正向分析；本机 venv 无 pyoptsparse，
  IPOPT 不可用 → 全部任务设计在分析模式，不依赖优化器）。

## 环境事实（2026-08-19）

- venv（benchmarks/.venv）：aviary 1.0.1 + openmdao 3.45.0 + pyvista 0.48.4；
- pyoptsparse 不在 PyPI（conda 分发）→ SLSQP 优化模式对 two_dof GwGm 不收敛
  （"Inequality constraints incompatible"，官方真值为 IPOPT 验证）；
- **任务协议取分析模式**（run_driver=False）：确定性、3.5s/次、可离线复算——
  参考值由 gold 预计算锁定，避免优化器可得性差异引入的环境不可复现。

## 隐藏动态题（M3 评审件）

- `hidden/generator.py`：参数空间 range∈[2200,3800]/50 NM × mach∈[0.72,0.82]/0.005 ×
  gross_mass∈[165400,185400]/1000 lbm；种子 20260819；试点 3 例已采样预计算；
- `hidden/answers.b64`：base64 隔离（防明文泄漏的一层；题面只含参数三元组）；
- 评审点：采样密度、种子轮换策略、泄漏监控阈值（scoring/README.md §5）。

## 判分口径（simulation_agent / aviary_mission）

- gate = 脚本跑通 + result.json 可解析（missing_output）；
- physics = 逐数值字段 |Δ|/|ref| ≤ 1% 计 1 取均值（exact_keys 精确匹配）；
- requirements = result.json 必填键存在率；objective/robustness = N/A（静态任务，权重 0）。

## 题面 API 提示的边界（如实记录）

题面披露环境约束（无 pyoptsparse、mach_cruise 键名、mission: 输出变量名）——属任务侧
应披露的接口事实，非答案泄漏；模型幻觉老 API（methods_for_level1、虚构机型路径）
计为被测能力失败，不再额外提示。

## 重取/复算

```bash
cd benchmarks && MPLCONFIGDIR=/tmp .venv/bin/python -m runners.gen_tasks_aviary --check
# 参考重算（--force-refs）或种子轮换后：重跑生成器即新评测周期
```

## 2026-08-21 扩题（8 → 27，append-only）

### 新任务清单（+19，gold 全部真实跑通，`_modify_csv` 幂等派生 + `references/<tid>.json` 预计算锁定，REL_TOL=0.01）

- **任务分析 range×mach 网格（+10）**：`av_range_2400_m72` / `av_range_2600_m75` /
  `av_range_2800_m78` / `av_range_3000_m82` / `av_range_3400_m72` / `av_range_3400_m80` /
  `av_range_3600_m78` / `av_range_2600_m82` / `av_range_2800_m75` / `av_range_3600_m82`
  （2400-3600 NM × M0.72-0.82，避开存量 3 组合）；
- **总重权衡（+2）**：`av_grossmass_trade2`（167400/172400/177400）、
  `av_grossmass_trade3`（179400/180400/182400）；
- **总重扫描敏感度（+1）**：`av_grossmass_sweep`（165400..185400 步 5000 五点 +
  最小二乘斜率 dfuel_dgrossmass_lbm_per_lbm）；
- **燃油比（+2）**：`av_fuel_ratio_3500_over_2500`、`av_fuel_ratio_3300_over_2700`；
- **航程扫描（+2）**：`av_range_sweep_m78`（2400/2600/2800/3000 @ M0.78 换基点）、
  `av_range_sweep_fine`（3000/3200/3400/3600 @ M0.80 加密）；
- **模型修复（+2）**：`av_repair_grossmass_v2`（corrupt gross_mass 180400 → 真 175400，
  真 range 3000）、`av_repair_range_v2`（corrupt range 2500 → 真 3400，真 gm 175400）。

**模型口径事实（如实记录，与存量 8 题同源）**：two_dof GwGm 分析模式
（run_driver=False）下燃油对 `aircraft:design:range` / `mach_cruise` /
`cruise_altitude` 均不敏感（巡航时长冻结于 phase_info initial_guesses；实测
2400→3600 NM、M0.72→0.82 燃油同为 43389.55 lbm——存量 `av_range_sweep` 斜率 0.0、
`av_fuel_ratio` 比值 1.0 即此事实），唯 `aircraft:design:gross_mass` 真实影响燃油
（165400→185400 lbm 燃油 35970→50797 lbm 近线性）。range/mach 族与存量 T1-T3 保持
同一判分口径（各题仍对各自锁定参考判分，oracle 复现满分）；真正非退化族为
总重权衡/扫描/修复。

### 解释器变更（必改点）

- `gen_tasks_aviary.py` 的 `_venv_python()` 由 `.venv/bin/python` 改指
  **`.venv-aviary/bin/python`**：`.venv` 2026-08-21 起为 pycycle 钉子栈（无 aviary），
  `.venv-aviary` = aviary 1.0.1 + openmdao 3.45.0 + numpy 2.5.2 + scipy 1.18.0
  （与 2026-08-19 建集环境同代，基准 CSV 与 venv 内拷贝逐字节一致已核）。
  **本生成器与两条 aviary 回归均须用 `.venv-aviary/bin/python`**；
- 运行环境注意：`runners/simulation_agent.py` 在 run_task 内无条件 import
  `runners.foam_nmse`（依赖 pyvista，NMSE 判分专用），`.venv-aviary` 无 pyvista 且
  两者均为冻结件——本次回归以 `PYTHONPATH=<pyvista import shim>` 启动 runner
  （shim 仅满足 import，aviary_mission 分支不触 NMSE；沙箱子进程 `-E -s` +
  白名单 env，PYTHONPATH 不进入被测/gold 执行环境）。run_manifest 内
  rerun_command 由 runner 硬编码 `.venv/bin/python`，按本节口径替换执行。

### gold 数与路径可移植性修复

- gold 共 **27** 个（19 新增 + 8 存量重写）；新增派生 CSV 37 个
  （`_modify_csv` 幂等生成，存量 16 个派生 CSV 与 base 逐字节不变已核）；
- **存量 gold 路径修复**：旧 gold 内嵌建集时仓库绝对路径（`JerryDSH/benchmarks`，
  建集后仓库搬迁）已失效（实测 FileNotFoundError）。新 `_GOLD_HEADER` 不再内嵌
  绝对路径：CSV 以 `data/aviary/transport_mission` 相对定位，锚点 = gold 文件目录
  （仓库内）/ cwd / aviary 包位置（沙箱内 venv 装于仓库下），逐级上溯定仓库根；
  新增 gold 同样全部相对定位；
- **旧 gold 路径修复 + 等效验证 8/8 通过**：修复后逐个重跑，对锁定 references
  全部字段 |Δ|/|ref| = 0.0（确定性正向分析精确复现），exact_keys
  （corrupted_param/restored_value/min_fuel_grossmass_lbm）全部精确一致——
  等效验证替代字节比对作为完整性证明。

### 不变项声明

- **seed（20260819/`--seed 0`）/ REL_TOL=0.01 / ASSETS_REVISION / 判分口径均不变**；
- **存量 8 题任务契约逐字节冻结**：`tasks/aviary.transport_mission/*.yaml|*.md`、
  `references/*.json`（含 2 个 `_reference_context.json`）、`base/`、`derived/`
  存量 16 文件、`hidden/` 全部未重写（git diff 为空）。

### 全量回归（2026-08-21，`--seed 0`，`.venv-aviary/bin/python`）

- stub：`results/aviary.transport_mission/2026-08-21/stub/` —— 27/27 gate fail
  （missing_output），**全 0 分地板确认**；
- oracle：`results/aviary.transport_mission/2026-08-21/oracle/` —— **27/27 全
  score=1.0**（physics 命中 100%，含 trade/sweep 多键题与 repair exact 题）。
