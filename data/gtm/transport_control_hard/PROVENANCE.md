# gtm.transport_control_hard 数据溯源（PROVENANCE，自建加硬任务集）

> assets_revision: `gtm-hard@selfbuilt-2026-08-23+matlabR2026a`
> 建集日期: 2026-08-23 · batch-2 会话（dev 终端）

## v1→v2 动机（难度归因）

- v1 `gtm.transport_control`（25 题）双模型近饱和：minimax-m3 0.9800（24/25 满分
  1 部分分）、glm-4.6 0.8900（21/25，gate 23/25：2 code_not_executable）。
- **饱和归因**：v1 题面直接把 A 矩阵（或等价参数）给足，判分键都是
  `eig`/`place`/`fzero` 一步出——教科书级数值计算，等于考「会用计算器」。模型装好
  语法→执行→写 result.json 即满分。
- v2 加硬轴：把「给矩阵→算模态」换成「给数据/给耦合结构/给不确定性→做工程判断与
  数据处理」，判分仍 100% 本地数值可复现、无 LLM judge。目标双模型 ≤0.7 区分带。

## 验收基线（2026-08-23 实测）

| 门 | 结果 |
| --- | --- |
| gold 全量预计算 + --check 幂等 | 17/17 通过，`--check` 全量逐字节一致 |
| stub 地板 | 17/17 `missing_output`（gate 全败） |
| oracle 判分管线自检 | 17/17 score=1.0 满分 |
| minimax-m3 区分度 | 均分 **0.7059**（10 满分 / 4 零分 / 3 部分分），自 0.98 → 0.71 |

minimax-m3 逐族（均分 / 每题）：

| 族 | 均分 | 每题 | 失分模式 |
| --- | --- | --- | --- |
| H1 含噪辨识 | 0.25 | 1.0 / 0 / 0 / 0 | 3/4 `code_not_executable`（LS+离散→连续管线脚本错） |
| H2 鲁棒裕度 | 0.875 | 0.75 / 1.0 / 0.75 / 1.0 | 2/4 把 w_gc（增益穿越）与 w_pc（相位穿越）**对调** |
| H3 增益调度 | 1.0 | 1.0×3 | 无失分（v1 F4 的 3-FC 扩展，仍偏易） |
| H4 非线性配平 | 1.0 | 1.0×3 | 无失分（模型能正确写 3x3 耦合 Newton） |
| H5 蒙特卡洛 | 0.5 | 1.0 / 0 / 0.5 | 1 脚本错 + 1 循环逻辑错（pass_fraction=0） |

区分度归因（与 v1 对照）：v1 0.98 的失分是在「给 A 求模态」上的 code_not_executable
噪声；v2 0.71 的失分转移到「数据处理/工程判断」语义层——H1 的辨识管线结构、H2 的
crossover 频率语义（margin 输出 wcg/wcp 顺序）、H5 的 seeded 采样循环。H3/H4 仍贴
v1 能力（place/Newton），是 v2 内偏易的两族——按「区分带是目标不是红线」如实记录，
不硬凑难度。glm-4.6 基线跑完落结果目录（首轮 minimax 为判定基线）。

## 五族设计（17 题）

| 族 | 数量 | tid | 判分键 | 与 v1 难度轴差异 |
| --- | --- | --- | --- | --- |
| H1 含噪系统辨识 | 4 | id_01..04 | omega_sp_id/zeta_sp_id | v1 F1 给 A 求模态；H1 给 PRBS 响应数据，须 LS 辨识 + 离散→连续映射 |
| H2 鲁棒裕度 | 4 | margin_01..04 | gm_db/pm_deg/w_gc/w_pc | v1 无裕度族；H2 给已设计 K 求裕度，两题内环+外环级联闭合 |
| H3 增益调度 | 3 | gs_01..03 | 每 FC cl_omega_sp_i/cl_zeta_sp_i | v1 F4 单 FC place；H3 三 FC 并行、目标各异 |
| H4 非线性配平 | 3 | trimnl_01..03 | alpha/thrust/delta_e/load_factor | v1 F2 L=W,D=T 闭式；H4 推力-阻力-升力-安装角互锁的耦合 3 元 |
| H5 蒙特卡洛筛选 | 3 | mc_01..03 | pass_fraction/failing_case_count | v1 无 MC；H5 200 点 seeded 盒不确定性采样需真跑循环统计 |

## gold 协议

- 与 v1 完全同路径：`python3 -m runners.gen_tasks_gtm_hard [--check] [--force-refs]`
  → gold/<tid>.m → `runners/solvers/matlab.py::run_matlab`（临时目录 model.m +
  `matlab -batch model`，串行）→ references/<tid>.json + YAML reference.values 内嵌。
- numpy 侧独立复算逐键断言 <1e-6（H1 额外断言 LS 辨识误差 <0.3%；H2 无 numpy margin
  等价，gold 单源并自检闭环稳定；H5 与 gold 同 seeded 采样口径）。
- 依赖函数面：`eig`/`logm`(H1 用 log)/`place`/`margin`(Control System Toolbox)/
  `fzero`/`rand`/`jsonencode`。无 Optimization Toolbox 依赖（fsolve 仅探针确认存在、
  gold 不用）。

## 记录在案的偏差

- **H1 噪声级**：规格口头 1e-3~1e-2，实取 2e-4~4e-4。原因：SP-ζ 辨识对噪声极敏感，
  1e-3 时 ζ 误差 >2%（违反「gold 复算 <0.3% 且键 1% 可判」）；取噪声上限使 ωn/ζ
  双键在 1% 容差内稳定复现。加硬点从「噪声量级」转为「完整辨识管线结构」（离散化
  →带输入回归的 LS→离散→连续 eig 映射→选 SP 对）。实测：噪声 2e-4~4e-4、N=600-1000、
  独立 seeds 下 SP-ωn 误差 <0.3%、SP-ζ <1.2%（30 seeds 量级）。
- **H1 只判 SP 对**：长周期（phugoid）离散极点 |λ|≈1.0 紧贴单位圆，任意噪声都使其
  塌到实轴，8-20s 数据不可辨识——与 v1 记录的 phugoid ωn 窗偏差同源（char(0)=g·Zu·Mw
  结构必然），结构解只能判 SP。
- **H4 判 4 键含 delta_e_trim_deg/load_factor**：把 v1 F2 的二键扩展到四键并引入
  推力安装角力偶，真正的耦合三方程。gold 用解析式（α 由垂直平衡锁定后代入）而非
  fsolve，保证 gold 与任何正确的 fzero/Newton 求解同解。

## hidden/ 评审件

- 仿 data/aviary/transport_mission/hidden/ 模式：H 族参数空间的 seeded 采样器 +
  3 例试点（generator.py + answers.b64 + README.md）。正式轮扩容由生成器重跑。

## 重取/复算

```bash
cd benchmarks && python3 -m runners.gen_tasks_gtm_hard --check   # 幂等校验
# 参考重算（--force-refs）：重跑生成器即新评测周期
