# PROVENANCE — cfdb.*（GLM-CFD-Benchmark 镜像）

> 上游：github.com/kogamishinyajerry-ops/GLM-CFD-Benchmark（本地克隆
> `~/projects/cfd/runtimes/cfdb`，即用户所指"GLM_Benchmark 项目目录"）。
> 镜像 revision：**cfdb@b26799e**（2026-08-28 镜像时上游 HEAD，
> b26799ebc6d2d931a71a07c911fdb8f699b03fe5）。

## A. 镜像范围（逐字复制，无任何内容改写）

| 上游目录 | 镜像路径 | 案例数 | 内容 |
| --- | --- | --- | --- |
| cases/case_setup | data/cfdb/case_setup | 17 | solver-agnostic 工程任务书（visible/task.md + drawing.png）+ 冻结 QoI 脚本 + held_out 参考 |
| cases/verification | data/cfdb/verification | 10 | 解析/程序化参考的 V&V 案例（完整参考算例 + held_out/qoi.json） |
| cases/validation | data/cfdb/validation | 15 | 实验/跨代码参考的验证案例（NACA0012 系列、圆柱 Re40/100、空腔 Re400/1000 等） |

- 上游 LICENSE（MIT）随镜像存于 data/cfdb/LICENSE；MIT 允许复制与再分发，
  `mirror_allowed: true`，再分发时须保留上游版权声明。
- 上游 trust 机制要点（与本仓库纪律同构，未做语义改动）：判分材料（隐藏 checker /
  normalize 规则）与参考数据一样 sha256 锚定；LLM-as-judge 永不进入任何判分路径；
  held_out 对账防"手写 qoi.json 得分"。

## B. 任务转化（tasks/cfdb.*，2026-08-30 修订：34 任务 + 8 排除）

- 生成器 `runners/gen_tasks_cfdb.py`（--check 可校验漂移）：
  - verification 9 + validation 8 = **17 个 managed 任务，已 integrated**（判分侧
    docker opencfd v2312 按案例冻结 steps 真实求解 → 宿主执行冻结 compute_qoi.py
    降算 QoI → 与 held_out/qoi.json 逐键容差对账；自报 QoI 永不进判分）；
  - case_setup 17 任务：**evidence 工具通道 2026-08-30 实装并全量验收**——oracle
    16/16 满分（14 evidence + 2 managed），cylinder_from_drawing 的 oracle 待编写
    （按图纸 D 建算例核 cd=1.49；其 stub 可执行，结果无 oracle 背书需标注）；
  - 排除 8 案例（原因存 data/cfdb/exclusions.json，先例 cfdcode 9 排除）：
    flat_plate_su2（无 SU2 后端）、lid_driven_cavity（参考算例不完整）、
    naca0012 ×4（snappy 链几何未镜像）、dam_break（瞬态前锋 QoI 跨运行复现
    超容差边界 15.5% vs 15%）、naca0012_sa_tmr（上游冻结 solve 预算 600s 在
    arm64 原生不足 2000 步，实测 55%@600s——最高民机相关案例，上游上调预算后
    优先重纳，harness 判分链路已就绪）。
- oracle：data/cfdb/oracle_scripts/<dom>__<case>.py——把镜像参考算例逐字复制为
  case/（上游 b26799e 已验证全跑通）；仓库根路径生成期固化（沙箱复制脚本，
  __file__ 不可用）。oracle 与 foam oracle 同一 trust 层级：GT verbatim writer。

## B2. evidence 工具通道（2026-08-30 实装）

- **两阶段候选协议**（`.cfdb_assemble` 标记文件区分阶段）：
  1. 阶段 RUN：候选脚本写 `case/` 完整算例（含任务书要求的采样 functionObject）；
  2. 判分 harness 代跑求解（docker v2312 冻结 steps）——即 agent 侧工具执行，
     产物为真实求解输出（场 + postProcessing + 日志在工作目录根）；
  3. 阶段 ASSEMBLE：重放候选脚本（读标记），从 `case/` 运行产物提取原始数据
     组装证据包 `submission/`（manifest.json + evidence/*，逐文件合同见各任务书）；
  4. 判分：清单齐全 + manifest 可解析（fail-closed）→ 冻结 compute_qoi.py 对
     **证据包根**降算 QoI → held_out 对账。自报数值永不进入判分；
     Judge runs NO solver（cfdb 上游 evidence 语义，内网商业 CFD 兼容）。
- **反作弊边界**：参考场/held_out 从不进入沙箱；候选可自由读的只有自己阶段 1 的
  运行产物；采样配置错误 → 证据包缺数据 → 冻结脚本 fail-closed 判 0。

## B2. 判分链路定案记录（2026-08-28/29 冒烟证据）

- 容器：opencfd/openfoam-default:2312（arm64 原生）；需显式
  `source /usr/lib/openfoam/openfoam2312/etc/bashrc`（Debian 布局，
  /opt/openfoam2312 无 bashrc）。
- 端到端冒烟：channel_poiseuille 参考算例 icoFoam 14.3s → probes/U →
  冻结脚本 `{"centerline_umax": 0.149254}` vs held_out 0.15（0.5% < 5%）；
  sod_shock_tube oracle 经完整 runner 分支：gate=1、score=1.0、
  shock_x 误差 0.05%（容差 2%）、三步全 critical 退出 0。

## C. 与既有条目的关系

- 上游 case_setup/verification 的 17+10 案例与本仓库 cfdllm.foam_basic（FoamBench
  110+16）不重叠：cfdb 是"任务书→自建案例"与"经典 V&V 复现"，FoamBench 是"教程级
  案例改写"；两者互补构成 agent-CFD 仿真执行层。
- 上游 coding_tasks/agentic_tasks（文件操作/编码 checker 类）本次未镜像：与本仓库
  humaneval/mbpp/spreadsheetbench 定位重叠，价值密度低；需要时按同一模式扩镜像。
