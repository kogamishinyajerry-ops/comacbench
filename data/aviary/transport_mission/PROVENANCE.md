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
