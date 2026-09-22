# PR #4 合并复验与 campaign lock v2

日期：2026-09-22。基线：`11ad7be78f9b46e1fb51fc47e4af7ba9be9b2369`，默认分支 `codex/trusted-resume-and-formula`。

## 结论

PR #4 已合并，原有 80 项专项测试可重现通过；它的公开回归、固定分母、参考实现排除和基本结果核验可以保留。本次追加探测发现五项误接收，故不能仅凭旧测试通过认定比较链路已完整。

本次修复不改任何物理真值、容差、权重、TaskSpec 或模型协议，不安装新求解器。审核对象仍是可信本地归档里的判分记录，不是运行中可对抗管理员的证明系统。

## 本次新增探测与修复

| 探测 | `11ad7be` 行为 | v2 行为 |
| --- | --- | --- |
| 正例满分，但 `calibration_passed=false` | 仍可 freeze | 拒绝；缺失 verdict 也拒绝 |
| 所有 raw result 与 suite manifest 一起换环境摘要 | `complete=true`、通过率 100% | 与锚点的稳定 suite contract 对比，阻断对应 cell |
| 复制同一 pack，只重排任务清单，登记为 transfer | 仍可 freeze | 排序后去重；重复配置不产生迁移证据 |
| 同一 suite 多放一份未登记的原始结果 | 仍 `complete=true` | 阻断未登记 runner record |
| 额外运行藏在符号链接目录 | 扫描未发现额外运行，仍 `complete=true` | 不跟随链接，显式标记扫描未完成，禁止比较 |

这些是合成归档反例，用于验证审核器，**不是工程求解或真实模型实验**。同一探测脚本在改动前后执行；修复后五项均拒绝或输出 `complete=false`。

### 校准记录不能只看一个布尔值

`mode=calibrate` 的锚点现在必须：具有严格的成功 verdict；所有任务至少有一个登记的负例；每项负例成功记录必须能找到原始 `controls/<task>-<index>/result_<task>.json` 与 `run_manifest.json`；provider、seed、adapter、environment 等相互一致；从原始诊断重新调用既有 `negative_control_passed()`。

原始负例得到满分、发生运行器崩溃、缺文件，或只在 summary 中伪造 expected diagnosis，均不能成为成功校准。已检查的负例 JSON 摘要写入锁。

普通 `run` 参考正例仍可用于预检锚点，但其状态是 `not_checked`，HTML 明示“仅预检正例，未核对校准负例”。这不会被自动升级成已校准。校准负例清单仍以可信归档中的登记清单为准；没有从独立 TaskSpec 重建全部负例，也没有重新执行物理检查。

### 两层环境身份都需要固定

保留 pack/engine/execution_environment/Agent 身份约束，另在每个 case 锁定 suite 的 `registry_id`、`adapter`、`environment_digest` 和 `assets`。provider、seed、时间、路径和 resumed 计数不属于这个稳定契约：参考锚点与候选 Agent 来源不同，多 seed 自然不同，不能因此产生误拒绝。

### 扫描失败不等于没有额外运行

用有错误反馈的 `os.scandir` 遍历代替只搜索 `rglob('run.json')`。拒绝归档内部符号链接、Windows reparse point 和特殊文件；访问失败、深度限制、条目限制都会使比较率不可用。

默认上限：100,000 个目录/文件条目，64 层深度。上限针对整个归档而非只针对 JSON；大规模实验需要分组归档，不应通过删掉异常记录绕过。

只将 `runs/<suite>/result_*.json` 和同层 `run_manifest.json` 视为直接 runner 记录；不会把更深层工程交付物中合法的 `result_analysis.json` 错当成额外评分结果。

Python 的官方说明明确指出，rglob 会抑制扫描文件系统的 OSError（含 PermissionError）；因此完整性审核需要显式处理这些错误。参考：
- https://docs.python.org/3.13/library/pathlib.html#pathlib.Path.rglob
- https://docs.python.org/3.11/library/stat.html#stat.FILE_ATTRIBUTE_REPARSE_POINT

## 从 v1 迁移

新锁协议为 `comacbench.campaign.lock.v2`；计划格式继续使用 `comacbench.campaign.plan.v1`，原有 freeze/report 命令不变。v1 锁会收到 `legacy_lock_requires_refreeze`，不自动升级，也不覆盖旧锁。

可以使用同一旧引擎生成的完整历史锚点与历史运行，在新审核器中重新冻结。**这不要求为迁移本身重跑模型或求解器**：

```bash
python -m comacbench.campaign freeze examples/campaigns/starter.plan.json --anchors ./anchors --out ./experiment.v2.lock.json
python -m comacbench.campaign report ./experiment.v2.lock.json --runs ./campaign-runs --out ./campaign-report-v2
```

前提是原始 plan/anchors/运行目录仍存在且记录匹配。旧的 calibrate 锚点缺失原始负例时，须恢复完整归档或重新校准，不能补一个 `calibration_passed=true` 糊过去。

若开始**新的** Agent/求解运行，本次源码变更会改变 `engine_identity()`；新运行使用新输出目录和对应的新锚点，不要与旧引擎混算，更不要修改旧记录强行 resume。历史记录保持不变。

## 验证记录与边界

本地网络无法解析 github.com，完整 git clone 失败。本地按 Git blob 核对重建了专项所需的 `campaign.py`、`completion.py`、`__init__.py` 和测试文件；不是全仓库 checkout。

Linux / Python 3.13.5：

- 改动前：80 项专项测试通过（1.517s）。
- 改动后：120 项专项测试通过（原 80 + 新增 40，0 failure/error/skip；2.350s）。原 80 项的校准夹具补齐真实协议要求的原始负例目录，未删除原有断言。
- `compileall` 与 `git diff --check` 通过。
- Chromium 内容渲染：完整/缺项两状态 × 1440px/390px，共四组；0 page error，0 外网请求，无页面整体横向溢出。窄屏表格可独立滚动，准入说明与失败提示可见。
- `file://` 导航受当前浏览器环境策略阻止；改用独立页面 set_content 验证，因此不声称本轮验收了 Windows 双击打开。
- Windows reparse-point 判断在本轮属于模拟测试，未进行原生 Windows junction 实测。

合并前的 **Windows 11 / Python 3.11.8 完整仓库验证** 是维护者在 `11ad7be` 提交的既有记录：340 passed、17 skipped、1 failed；记录将失败定位到既存 superwing LFS 资产漂移；真实运行链路采用确定性本地包装器而非模型。这一记录见 `hydrogym-campaigns-validation.md`，本次没有把它重新声称为自己的全仓库实测。

新增 `.github/workflows/campaign-audit.yml`：在 Linux/Windows、Python 3.11/3.13 运行专项门禁，仅稀疏检出源文件与测试，不安装依赖或下载 LFS、调用模型。Actions 使用已核对的固定 commit。**工作流文件提交不等于 CI 已通过**，以 GitHub 实际运行状态为准。

所有报告继续保留 `publishable=false`、`isolated_transfer_verified=false`、`engineering_artifacts_reverified=false`。未增加模型成绩、隐藏迁移证明、预算强制执行或全工程产物字节复验。

## 下一步只推进一个业务实验

先在目标机器重跑这次专项及现有真实 CLI 闭环，并修复/恢复 superwing 的合法 LFS 资产（不能简单改期望摘要令测试变绿）。然后选择现有 workload 任务族，比较固定模型下的“基础配置”和“增加一个工程 Skill 的配置”，冻结相同任务、种子、工具范围与预算，记录人工介入及所有失败。

本次不再重复开发已经新增的产物归档、可信恢复与离线打包工具；这些实现仍需各自的实机交付验收。下一阶段的新任务族、独立隐藏验收和 HydroGym 后端，应分别立项，不与这一处判分链修复捆绑。
