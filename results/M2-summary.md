# M2 总结报告（2026-08-19）

> 运行环境：`dev` 终端（外网开发机，OpenFOAM+FoamAgent，Python 3.12.13，pip 直连）。
> 本报告所有结论均在 dev 层产出；内网移植时（env-matrix §0）需替换沙箱为容器执行。

## 1. Registry 状态变化

| registry_id | 之前 | 之后 | 依据 |
| --- | --- | --- | --- |
| cfdllm.cfdcode | proposed | **integrated** | 镜像（BSD-3 核验，9/24 任务 gold 不可用如实排除）→ code_exec 五层判分跑通 + oracle 15/15 + stub + M3 基线落盘（GLM 429 限流未完成，见 §6） |
| scicode.physics | proposed | **integrated** | 镜像（Apache-2.0 核验，52 题 AI 辅助标注 subject 子集）→ code_exec 跑通 + oracle dev 10/12（2 题环境依赖偏差如实记录）+ stub + M3 基线落盘（GLM 429 限流未完成，见 §6） |

## 2. 镜像与许可核验

### cfdllm.cfdcode
- 源：GitHub `NREL-Theseus/cfdllmbench` @ `3b46d30`（LICENSE=BSD-3-Clause）+ Kaggle
  `nithinsekhar/cfdcodebench` v1（paper arXiv:2509.20374 声明整个 benchmark BSD-3-Clause）；
- 镜像内容：`prompt/PDE_TASK_QUESTION_ONLY.json` + `prompt/prompts.json` + `solution/`（26 文件）
  + `gold_outputs/`（31 npy，gold 运行离线预计算 + 逐文件 sha256 锁定）；
- **9/24 任务 gold 不可用排除**（详见 `data/cfdllm/cfdcode/PROVENANCE.md`）：
  - 5 个依赖 `dedalus`（谱方法包）：`1D_KdV_Burgers`、`2D_Rayleigh_Benard`、
    `2D_Shear_Flow_With_Tracer`、`Lane_Emden`、`Pipe_Flow_Disk_EVP`（FFTW 系统依赖不可得）
  - `2D_Navier_Stokes_Cavity`：gold 自身压力泊松不收敛（>2e6 迭代仍发散）
  - `2D_Unsteady_Heat_Equation`：gold 运行 >1800s 超时
  - `2D_Diffusion`：上游 prompt 要求存 `p`，gold 只存 `u`（数据不一致）
  - `Fully_Developed_Turbulent_Channel_Flow`：上游 prompt 要求存 `u`，gold 存 `u1..u5`（数据不一致）
- 恢复条件：dedalus 需装 FFTW+fftw-dev（brew 目录无写权限卡住）可救回 5 题；其余 4 题需上游修复。
- 任务口径：15 任务（24-9）。

### scicode.physics
- 源：GitHub `scicode-bench/SciCode` @ `e3158ea`（LICENSE=Apache-2.0）+ HF `SciCode1/SciCode`
  + Google Drive 官方 `test_data.h5`（1.05GB，md5 锁定，338 步数值期望）；
- 镜像内容：`problems_test.jsonl`（65）+ `problems_dev.jsonl`（15，含公开 gold）+ `test_data.h5`；
- **M2 子集 52 主问题 / 209 子步 / 207 步可判分**（排除 2 特判步 13.6/62.1 无数值目标）：
  - 划定依据 `data/scicode/physics/subject_map.md`（AI 辅助标注 + 论文逐子域计数校验，5 项偏差如文档）；待人工复核；
  - 子集 = Physics 37 + NLA 8 + CompMech 5 + 量子数值边界对 {15, 52}（按 registry「物理与数值计算」口径）；
- 恢复条件：subject 映射人工复核可定 subfield 边界（偏差 1）；上游修正 multip-step 协议缺口可对比官方榜单。

## 3. code_exec adapter（v0.1）

五类标准 adapter 之二（adapters/README.md §2）。YAML 驱动，5 层判分：

| 层 | 子分 | 规则 |
| --- | --- | --- |
| gate | — | executability + 缺 output_contract 产物（missing_output）/ NaN/Inf（non_physical_values）/ 沙箱违规（sandbox_escape_attempt）/ 越界（timeout）|
| executability | requirements | 代码可导入可调用（harness 跑通） |
| hidden_tests + numerical_tolerance | physics | scicode：逐 case 通过率（assert 语义 = 数据集原始断言，h5 期望值）；cfdcode：mean(clamp01(Cosine), clamp01(R²)) 按变量均值（官方插值对齐 + sklearn 指标） |
| stability | objective | 数据集无边界输入测试 => N/A（权重 0，YAML 声明） |
| determinism | robustness | 两次执行结果一致（scicode 步内通过模式 / cfdcode npy allclose） |

**沙箱强度（dev 终端，如实声明）**：静态 AST 审查（黑名单：network/process/ctypes/sys.path）+ `python -I` 隔离解释器 + 临时工作目录 + 墙钟超时；macOS 无 RLIMIT_AS，内存限额以超时兜底。**非 OS 级强制隔离**——intranet 移植应换容器执行（env-matrix §2 python_sandbox）。零范数余弦守卫（`v` 全零场，官方实现返回 Cosine=0 属退化）。

## 4. 判分器工程发现（如实记录，影响后续维护）

scicode 判分（`data/scicode/physics/PROVENANCE.md` 详述）：
1. case 命名空间**步内共享**（官方语义，与最初独立实现相反）——7.1/10.1 的 case4 依赖 case1 变量。
2. 官方 `scicode.compare.cmp` 包 vendor shim（`runners/vendor_shim/scicode/`，Apache-2.0 逐行拷贝）。
3. scipy 1.14 改 `simps→simpson`——数据集 `required_dependencies` 沿用老 API，harness 加可信侧兼容别名（2/52 题受影响）。
4. 78.3（混沌摆）gold 用 `time.time()` 选时间步——**上游机器计时依赖**，本机 oracle 0/3（已知，不可修）。
5. 70.8 case4（`s13=0` 退化构型）gold 输出与 h5 target 最大差 1.8e-4（物理一致）——**科学库版本漂移**（已知，不可修）。

cfdcode 判分：
- `cavity`、`unsteady_heat` 失败为上游 gold 缺陷，**2D_Diffusion`/`Fully_Developed` 失败为上游数据不一致**。
- 7 个 gold 含 `plt.show()` 无头挂死——预计算用 wrapper 中和；Cylinder/Lid 写死相对路径 ../../PDE_Benchmark/...——预计算用 `/tmp/bm_x/a/b/cwd` + `/tmp/bm_x/PDE_Benchmark/...` 对齐。

## 5. 协议偏差（与官方榜单**不可直接对比**）

- **scicode**：整题一次生成（官方为逐步骤多轮自回归）。分数为「整题生成能力」指标，**不与官方 SciCode leaderboard 直接对比**。
- **cfdcode**：金标准注入（oracle）= 注入预计算 npy，**不执行 gold 源码**——验证 grader 而非模型执行路径（gold 源码执行路径已在预计算阶段验证）。

## 6. 基线（dev 终端，种子 0）

### 6.1 cfdllm.cfdcode（15 任务）

| 指标 | GLM-4.6 | MiniMax-M3 | stub |
| --- | --- | --- | --- |
| ValidityGate | **限流未完成**（429；3/15） | **8/15** | 0/15（`pass\n` 不产出 npy）|
| 任务均分（gate 通过子集） | — | **0.881**（8 题） | — |
| 物理层均值（gate 通过） | — | **0.937** | — |
| 鲁棒性 | — | 8/10 = 1.0 | — |
| 单题延迟 median | — | ~30s | <1s |

**双模型对比**（仅 cfdcode）：M3 在 gate 通过的 8 题上，物理层均值 0.937，R²/余弦很高；gate 失败的 7 题中 4 个 `code_not_executable`（生成的 solver 缺导入或语法错）+ 2 个 `non_physical_values`（NaN，浮点不稳）+ 1 个 `missing_output`。GLM 429 限流（同一 coding API 端点与 M3 共享，本会话内未能复跑）——**建议稍后单跑 GLM 补齐**（cancelled 重试后 3 题仍 429）。

### 6.2 scicode.physics（52 任务，test 40 / dev 12）

| 指标 | GLM-4.6 | MiniMax-M3 | stub |
| --- | --- | --- | --- |
| ValidityGate | **限流未完成**（1/52） | **42/52** | 52/52 |
| 任务均分 | — | **0.674** | 0 |
| 物理层均值 | — | **0.540** | 0 |
| gate 失败原因 | — | sandbox_escape ×1, code_not_executable ×8, timeout ×1 | — |
| 单题延迟 median | — | ~80s（含 sandbox 二次执行）| <2s |

**gate 失败明细（M3）**：`p011 sandbox_escape`（模型写了 banned_import:os.path 之类）；`p020/022/037/043/054/067/069/073 code_not_executable`（模型代码语法/导入错）；`p062 timeout`（单题 1800s 仍未完成）。**与 stub 对照**（stub 52/52 gate pass 但 physics=0）：判分器对「无函数定义」的容错正确；模型代码缺函数时 gate 仍 pass、physics 0，与设计语义一致。

### 6.3 复现性声明

stub / oracle 离线确定可逐字节复现；API 基线受推理模型非确定性影响（temperature=0 下思考型仍可能给出不同答案），重跑同命令可复现管线与判分，**不保证逐题答案一致**——这正是 scoring/README.md §7「Agent 侧采样声明次数并报告方差」要求的差异点。

## 7. 偏差与待议清单（不静默扩 scope）

1. **GLM 双基线因 API 429 限流未完成**（cfdcode 3/15、scicode 1/52）——非 harness bug，是共享 coding API
   端点（本会话与 M3 并发后）的限流。复跑命令保留、单跑可补。
2. **scicode 整题协议与官方多步差异**（§5）——分数不可与官方榜单直接对比；M2 数字作为本 harness
   自有基线，进入九维度汇总时按 knowledge 维度的「coding 子能力」登记。
3. **subject 映射待人工复核**（5 项偏差见 `subject_map.md`）：35/39 若人工改判 Optics 子集
   +2 题；其余子域内拆分问题对子集边界无影响。
4. **cfdcode gold 恢复条件**：5 题 dedalus 依赖（待 FFTW 系统包 + 重装）、Cavity/Unsteady_Heat/
   2D_Diffusion/Fully_Developed 共 4 题待上游修复。
5. **scicode 整题 prompt 中 step 函数返回的 value 校验**——对 `None` 默 0 分的策略需明确
   （当前 NaN/非物理 已在 gate 守，非 None 异常值通过 0 分计入）。
6. **code_exec 沙箱**（dev 终端实现，§3）—— intranet 移植须换容器（env-matrix §2 python_sandbox）；
   Mac 上 RLIMIT_AS 不支持，内存限额以超时兜底。
7. **oracle 自检范围**（scicode）：dev 12 题 10 满分 + 2 环境依赖偏差（p078.3 计时 / p070.8 s13=0
   退化），不可达 12/12（已知）。

## 8. 产出文件（2026-08-19 目录统合后布局：results/<registry_id>/<date>/<provider>/）

```
benchmarks/
├── runners/{__init__,common,providers,qa_grounded,code_exec,sandbox}.py + _scicode_h5.py
│          + vendor_shim/scicode/{__init__,compare/{__init__,cmp.py}} + ATTRIBUTION.md
│          + gen_tasks_{cfdquery,aeroengqa,scicode,cfdcode}.py
├── tasks/scicode.physics/     52 yaml + 52 md
├── tasks/cfdllm.cfdcode/      15 yaml + 15 md
├── data/scicode/physics/      镜像 + PROVENANCE.md（含判分工程发现）+ subject_map.md + m2_subset_ids.json
├── data/cfdllm/cfdcode/       镜像 + gold_outputs/（31 npy，sha256 锁定）+ PROVENANCE.md
├── results/scicode.physics/2026-08-19/{README.md, stub/, oracle/, minimax-m3/}
├── results/cfdllm.cfdcode/2026-08-19/{README.md, stub/, oracle/, minimax-m3/}
├── results/M2-summary.md（本文件）
└── registry/{registry.yaml, license-notes.md}
```

迁移备注：scicode/cfdcode 首跑 GLM 并发与 M3 触发 429——GLM 后续会话单跑补齐；
cfdcode/scicode 严格遵循 `results/<registry_id>/<date>/<provider>/` 布局（results/§5）。
