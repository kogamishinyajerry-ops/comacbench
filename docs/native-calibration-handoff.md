# 原生结构变更校准：本地接手规格

> 维护者材料：含参考流程或验收期望，不提供给受试 Agent。受试入口见 [公开操作合同](public-workbench-contract.md)；权限边界见 [受限试验说明](restricted-public-trial.md)。

状态：**代码与非物理控制测试已交付；CalculiX 原生验收待本地执行。**

基线为 PR #7 `59f3dbe659b750964f5a81c99eb619352657c2ae`，分支
`review/change-workbench-product-scope-20261002`。2026-10-02 核对时 #7 仍 open/未合并。
本增量不依赖未合并的 PR #6 配对报告。没有创建或自动合并新的远程 PR；本地验收后提交 Draft PR。

## 本轮已经写好的内容

仍用同一个 `python -m comacbench.workbench`，增加内置
`comacbench.structures-change.v1` 任务族与 `solve` 行动。没有新增 Harness、训练框架或通用仿真平台。

- `workbench_ccx.py`：固定 C3D20 模板、已有 ccx 二进制发现和身份绑定、受控进程、原始文件归档、独立复读。
- `workbench_structures.py`：两工况依赖图、载荷/限值变更与基于原生结果的报告检查。
- `native_reference.py`：确定性参考策略，读取环境反馈，不读取 reviewer 参考答案，不调用模型。
- `local_acceptance.py`：非破坏性环境记录、专项测试、三个原生控制流程、迁移复查、篡改副本负例、证据 ZIP。
- Catalog 新入口为 experimental，明确目标机未验证，不进入 pilot 或 Campaign 成绩。

## 场景与验收

固定尺寸 100×10×5 mm；E=210000 MPa，nu=0.3；20×4×2 个 C3D20。
几何连接顺序沿用原 `packs/aviation-structures-v2/private/beam_static_01.py` 的思路，新增 FRD 输出。
**未改动该旧 pack 的参考程序、真值、容差或权重**。这里是一个独立校准任务族。
输入不接受任意 INP 或脚本，避免把任意代码执行误写成已隔离的求解环境。

| 阶段 | 输入 | 正确行为 |
|---|---|---|
| baseline | service=-100 N，limit=-120 N，位移限值0.6 mm | 两次独立求解，检查两个原生结果，完成 review |
| load-b | 仅 limit 改为-140 N，note 同时变化 | 只重算 limit，保留 service 的原始任务及校验记录 |
| requirement-b | 仅位移限值收紧为0.45 mm | 不重算；重新解释既有结果，最终应为 needs_review |

参考路径预期15次行动、3次求解请求。每个 session 上限32行动、6次求解请求，每次最多120秒；失败仍计数。
三个参考/负例流程合计预期8次原生请求，实际以记录为准，不允许跳过失败只交最好结果。

求解和复查分开：

1. `solve` 根据冻结模板和当前载荷生成 INP，启动 `ccx -i model`，归档日志、状态及所有输出。
2. 求解结果节点为 broker-owned；Agent 的 `put` 不能伪造 native result。
3. `.dat` 必须包含最终时间的完整 NTIP 位移和 NROOT 外力节点列表；缺项、重复、非有限数值失败。
4. 复读时校验原始文件/请求/输入模板/进程状态，重新计算检查，不运行 solver。
5. 载荷变更后旧结果失效；验收限值变更只使 review 失效。
6. 数值有效但不满足当前位移限值，是 `needs_review`，不等于求解崩溃，也不能称为合格设计。

## 物理检查边界

梁理论交叉检查为 δ=F L³/(3 E I)，I=5×10³/12 mm⁴；-100 N 的理论值约 -0.380952 mm。
这是理论量级，**不是本轮实跑数据**。模型是线性静力校准梁，无连接、局部细节、应力/疲劳验收。
位移交叉检查暂定3%相对容差，支承外力平衡暂定1e-5相对容差，绝对项1e-6。
这些是新任务的开发检查阈值，仍需目标机/专家确认；不得为了测试变绿私自放宽。

CalculiX RF 表示节点外力；本模板载荷施于远端，固定端无 CLOAD/DLOAD，才用 NROOT RF 合计核对反力。
依据：Guido Dhondt，《CalculiX CrunchiX USER’S MANUAL 2.23》，2025-10-19：
https://dhondt.de/ccx_2.23.pdf ，§6.2.4（印刷页97，C3D20节点顺序）、§7.99（印刷页568，NODE PRINT / RF）。
原始网页/手册已核对，不随交接包再分发整个第三方手册。

## 本机执行

选择项目现有 Python 3.11+；使用已有、经授权的 CalculiX 2.23。
优先读取 `CCX_BIN` 或 PATH，Mac 可检查 `/opt/homebrew/bin/ccx`。
不要把未知的 ccx.exe 路径、未验证版本或 Python 测试脚本当作 solver。
二进制不存在或版本不符合时，输出 BLOCKED 和日志；本工具不联网安装。

```bash
# 只记录现场，不执行原生求解
python examples/workbench/local_acceptance.py --repo /absolute/source/root --out /new/outside/preflight

# 完整验收：源码必须干净，输出在工作区之外；--ccx 可由已明确配置的 CCX_BIN 替代
python examples/workbench/local_acceptance.py --repo /absolute/source/root --out /new/outside/native-check --ccx /absolute/path/to/ccx --run-native
```

在 Windows PowerShell 中同样传绝对路径（ccx.exe）并用引号包住带空格路径。
默认检出涉及含冒号的研究资产；遇到 Windows 非法路径时，不关闭 `core.protectNTFS`。
可先运行交接包内的 `scoped-source`，该目录只含本阶段源码和测试，不含大型研究资产。
其 `SOURCE_SNAPSHOT.json` 区分 **PR7基线＋本轮覆盖文件**，不伪称这些修改已经属于PR7远程提交。
该目录无需 Git checkout 即可验收，但不是全量仓库、wheel或内网发行包。

单独运行时：

```bash
python examples/workbench/native_reference.py --out /new/reference --ccx /path/to/ccx
python examples/workbench/native_reference.py --negative stale --out /new/stale --ccx /path/to/ccx
python examples/workbench/native_reference.py --negative false-ready --out /new/false-ready --ccx /path/to/ccx
```

行动 JSON 例：`{"op":"solve","target":"solution_limit"}`。使用
`python -m comacbench.workbench act SESSION --action-file ACTION.json`。
其余 `put/check/advance/submit` 沿用已有机制。行动文件应在 session 外。
完整字段来自 `observe.contract` 和示例，不向 Agent 提供额外隐藏答案。

## 本地接手后的顺序

A. 核对本机 repo 根目录、remote、branch、HEAD、status，不 reset/clean/stash/force push；保留所有本地改动。
PR7未合并时，从其已核对提交建立隔离开发分支，先 `git apply --check` 再应用本轮补丁。
已经合并或有后续提交时先对照，不重复覆盖。源码在提交后才做正式验收（工具拒绝 dirty worktree）。

B. 完成纯控制测试。预期目前106项中105通过、1个真实求解测试明确跳过；安装问题与回归失败分开。
不可把 skipped 改成 pass。当前环境实际为 Linux/Python3.13.5，未运行新代码的线上CI。

C. 用真实 ccx 执行三个流程、拷贝后复查和篡改副本负例。检查退出码之外，还检查 `.dat` 原始数值、节点集合、载荷和反力方向。
如终止标记、版本输出格式与实际2.23不一致，保留原日志，依据真实输出修 parser 并补负例；不改物理阈值掩盖问题。

D. 用本机浏览器实际打开三个 `report/report.html`，检查报告没有把原生已运行写为未运行、没有把 needs_review 写为合格。
本轮未验收原生报告的 Windows 双击显示或本机浏览器行为。

E. 原生校准通过后，再进行一场**公开开发任务**的真实 Agent 工具调用试验。
先探查现有 DSH/Codex 接口；没有已验证接口时只写清阻塞，不假定 CLI 命令存在。
该试验最多一个配置、一个 session，不开展大规模A/B或下载模型。不读取真实型号数据。

F. 返回证据并提交 Draft PR；不合并。若仍 BLOCKED，保留 Draft 状态与阻塞信息。
PR7存在时可暂以其分支作为base，防止把PR7整份改动重复列入新增PR。

## 需要返回的证据

`local_acceptance.py` 无论失败或成功，都生成 `handoff-result.json`、逐命令日志、`evidence-manifest.json` 和同级 ZIP。
通过时还含全部原始 session/native 目录、三种报告、迁移副本、故意篡改副本。
不要只交截图或“测试全部通过”一句话。证据不公开自动上传，先检查日志和本机路径。

额外提交：真实模型/Agent试验有则提交其请求/工具轨迹/人工介入记录；无则标NOT_RUN。
模型或API凭据不得进Git、日志、ZIP。公开场景没有隐藏测试隔离，不得声称迁移能力已验证。

## 已知工程限制

版本/二进制/库环境变量摘要不是远程证明，也没有锁定每个动态库文件；操作者掌控整个归档可重写摘要。
只允许可信本地使用，不是安全沙箱。不计会话外工具、模型token或人工时间。
单线程为进程环境请求；内存没有OS硬配额；文件限额是轮询保护而非硬文件系统配额。
进程中断在 native 目录留下保留记录，未完成job会阻止静默重试。不要删除其目录重置预算。
外层交接脚本若超时，先检查本机仍运行的父/子进程，再决定结束；不得盲目循环启动。
完整安装、旧pack与商业求解器回归、网格收敛研究、正式工程审查和隔离迁移均留待后续。
