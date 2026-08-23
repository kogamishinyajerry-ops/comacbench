# PROVENANCE — calculix.fea_basic（structures 维自建基准）

> 创建：2026-08-24。任务与 gold 生成脚本 `runners/gen_tasks_ccxfea.py`（幂等重跑覆盖重写）。
> 本文件记录数据来源、判分口径、gold 锁定方式与已知偏离——判分纪律见 `scoring/README.md`。

## 1. 来源与许可

- **任务全部自建**（受 SimJEB 支架域与 cadgen L 支架族启发；未镜像 SimJEB 数据——
  其判分复算原计划 ANSYS MAPDL 商业栈，dev 终端不可得，且许可 needs-verification）。
- 执行后端 **CalculiX ccx 2.23**（GPL-2.0，brew calculix-ccx，`/opt/homebrew/bin/ccx`），
  仅作求解器，不随仓库分发其二进制；`CCX_BIN` 可覆写（内网版本锁定用）。
- 单位约定：mm-N-MPa-tonne（钢 E=210000 MPa, ν=0.3, ρ=7.85e-9 tonne/mm³）。

## 2. 任务族（5 族 21 题，全部本地确定性生成）

| 族 | 题数 | 分析 | 解析交叉验证（gold vs 解析，实测偏差） |
| --- | --- | --- | --- |
| cb 悬臂静力 | 5 | *STATIC | δ=PL³/3EI：0.03%~0.79%；反力 ΣRF2=-P：0.00% |
| ssb 简支中载 | 4 | *STATIC | δ=PL³/48EI：0.62%~2.16%（knife-edge RBC 剪切效应）；支反力 P/2：0.00% |
| modal 悬臂模态 | 4 | *FREQUENCY | EB f=β²/2π·√(EI/ρAL⁴)，弱轴 f1 0.33%~0.51%、强轴 f2 0.01%~0.29%（剪切校正余量） |
| bkl 悬臂屈曲 | 4 | *BUCKLE | 欧拉 Pcr=π²EI/4L²，弱轴 0.31%~0.51%、强轴 0.00%~0.35% |
| lb L 支架静力 | 4 | *STATIC | 无解析参照（静不定）；gold=ccx 参考网格自洽 |

## 3. gold 锁定与判分口径

- **gold 生成协议**：`run_gold()` 在临时目录实跑「gold make_case.py → ccx → parse_dat」，
  解析值逐题写入任务 YAML `reference.values`；gold 脚本存 `gold/<tid>.py`。
- **oracle 自检（2026-08-24 实测）**：21/21 gate 通过、physics 1.0、max rel_err = 0.00e+00
  （gold 逐字节复现）；stub 21/21 地板（missing_output）。判分管线双向验证。
- **判分**：模型写 `make_case.py`（生成 `model.inp`，不执行求解器；python 沙箱静态检查）
  → runner `ccx -i model` → `.dat` 按 `grader.extract` 规格抽值 → 数值对 gold 相对误差。
  容差：静力/L 支架 5%、模态 3%、屈曲 5%——覆盖模型网格离散化差
  （题面钉死 C3D20 + 最小网格 16/4/2）。
- **失败语义**：脚本不可执行=code_not_executable；未写 model.inp=missing_output；
  ccx 非零退出=simulation_failed；集合名/打印请求不符=.dat 缺块→missing_output
  （遵守输出契约是任务的一部分，合法失败信号）。

## 4. 已知偏离与陷阱（工程记录）

- **ccx 16 项/行上限**：C3D20 连接表（21 项）与 NSET 行必须折行——题面明示该纪律，
  gold 脚本内建；模型违反时 ccx 报 `*ERROR in splitline`（simulation_failed）。
- **C3D20 节点序**：13-16 为顶面棱中点、17-20 为竖棱中点（Abaqus 约定）——
  顺序颠倒致 `nonpositive jacobian`。烟测期间实证修正。
- **模态表列位**：`.dat` 第 4 列才是 CYCLES/TIME（Hz），第 5 列为虚部（实模态恒 0）。
- **屈曲表头跨行**：`MODE NO BUCKLING` 与 `FACTOR` 分两行；标题行字母间有空格不可匹配。
- **ssb 2.16% 偏差**：粗截面梁剪切变形使 EF 位移略高于 EB 理论（理论预期方向），
  gold 取 ccx 值（与被测模型同口径），解析值仅作交叉验证记录。
- **lb 族**：全域结构化网格 + L 域外单元剔除，角点节点共享（conformal），无 tie。

## 5. 复现

```bash
.venv/bin/python -m runners.gen_tasks_ccxfea        # 重新生成任务+gold（确定性）
.venv/bin/python -m runners.simulation_agent \
    --tasks tasks/calculix.fea_basic \
    --out results/calculix.fea_basic/<date>/<provider> --provider <p> --seed 0
```
