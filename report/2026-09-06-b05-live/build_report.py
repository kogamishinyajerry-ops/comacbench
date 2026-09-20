"""Render the review report from verified result artifacts, without API access."""
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def read(path):
    return json.loads(path.read_text())


verified = read(HERE/'verification.json')
assert verified['status']=='passed'
protocol = read(HERE/'protocol.json')
prior = HERE.parent/'2026-09-05-live-smoke-minimax'
table = []
for group in protocol['groups']:
    for tid in group['expected_task_ids']:
        name = 'result_'+tid+'.json'
        rows = [read(prior/'runs'/group['name']/name),
                read(HERE/'minimax/runs'/group['name']/name),
                read(HERE/verified['models']['glm']['result_directory']/'runs'/group['name']/name)]
        values = [f'{r["score"]:g}（gate {r["validity_gate"]}）' for r in rows]
        table.append('| '+tid+' | '+' | '.join(values)+' |')
stats = []
for alias,info in verified['models'].items():
    stats.append('| '+info['model']+' | '+str(info['requests'])+' | '+
        str(info['usage']['prompt_tokens'])+' | '+str(info['usage']['completion_tokens'])+' | '+
        str(info['usage']['total_tokens'])+' | '+str(info['gate_passed'])+'/8 | '+str(info['full_score'])+'/8 |')
text = '''# B05 输入契约修复与双模型真实小样本验证

日期：2026-09-06。两处输入契约修复已完成；相同 8 道样本分别完成 MiniMax-M3
和 glm-5.3-flash 的真实调用。相对上轮修复前周期使用新身份和独立输出目录，
超时恢复继承本周期的相同身份。
以每题 gate、分项得分和请求证据为准，不作模型排名。

## 本次变更

- 修订题：共用生成器明确四个 canonical JSON key；同步 5 道公开题面、YAML 题面哈希，
  以及隐藏池 15 道修订题的题面哈希。全部 45 条隐藏记录的参考答案和 exact_keys 不变。
- 表格题：`runners/design_artifact.py` 从 `input.assets` 提取实际暂存文件名，
  加入有效题面；明确由模型脚本读取输入并保存 `output.xlsx`，保留所有工作表。
  不向模型提供 golden/oracle，未改工作簿、判分权重或 B03 判分逻辑。
- GLM：复用现有 `glm` provider，显式传入 `--model glm-5.3-flash`。
  默认模型不变；实际官方 API 响应中的 model、response ID、用量均已落盘核验。
- 新增修订题契约测试，扩展表格 CLI/GLM 测试；协议说明见
  [B05 输入契约](../../docs/specs/b05-input-contract-v1.md)。

## 固定样本结果

| 样本 | 上轮 MiniMax | 本轮 MiniMax | 本轮 GLM-5.3-Flash |
| --- | --- | --- | --- |
'''+ '\n'.join(table)+'''

两道修订题的 MiniMax 得分从 0.7143 恢复至 1；两道表格题均已越过上轮文件读取失败。
MiniMax 的 `ssb_17_35` 为 1445/1445 单元格匹配；`ssb_22_47` 为 4/27，
工作簿契约满分，内容项 0.1481，按原权重得到总分 0.57405。
GLM 在该排序题同样为 4/27 匹配、总分 0.57405，两者保存的错位单元格明细一致。
本轮两道抽取题的 MiniMax 丢分均为 `clause_no` 缺少原文 `§`，其他八字段命中。

`ssb_22_47` 的剩余差异需要单独审查：原题同时描述 helper 优先顺序与 H 列升序，
gold 的 H 列为升序。当前模型输出与 gold 不一致已被记录，
不在本轮改写题面语义、gold 或评分规则，也不将全部差异直接归结为模型能力。

## 请求与协议

| 模型 | 实际请求 | 输入 token | 输出 token | 合计 token | gate 通过 | 满分题 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
'''+ '\n'.join(stats)+'''

用户已取消 MiniMax/GLM 总费用、总 token 和请求次数预算限制，protocol.budget=null。
本轮范围仍为每模型 8 个固定样本，seed=20260905，H0，无 scaffold、无判分反馈迭代。
MiniMax 保持上轮 temperature=0 / max_tokens=16384；GLM 使用现有原生预设
temperature=0 / thinking enabled / max_tokens=32768。单次输出长度限制不等于总预算。

MiniMax 第 8 次请求以 finish_reason=length 结束，16384 个输出 token 全为 reasoning，
没有可解析答案；原 provider 自动进行第 9 次解析重试后得到第二道表格结果。
该请求未被丢弃，消耗计入上表。没有因得分低而重跑。

GLM 初次实验第 8 次请求在 600 秒超时，其用量未知，上表 token 仅为已返回的已知用量，
不把未知消耗当成零。[原始停止记录](glm/summary.json)保持不变。
[恢复协议](glm-recovery/protocol.json)将 7 份已完成结果原样复制至新目录，
验证原身份后仅续跑缺失题；单次等待延长为 1800 秒，模型、题面、seed、生成参数不变。
首次恢复请求与原超时请求的请求体 SHA256 相同；解析失败仍遵循原 provider 重试策略。
恢复后再次验证全部 8 份结果的缓存复用，7 份继承结果字节不变。
最后一次 GLM 响应耗时 784.582 秒，正常 stop，输出 24674 token，其中 reasoning 23622；
复杂题的等待时间与思考策略仍需后续独立优化。

官方模型名及端点依据：[智谱模型切换指南](https://docs.bigmodel.cn/cn/coding-plan/latest-model)。
当前 GLM 使用 `https://open.bigmodel.cn/api/coding/paas/v4/chat/completions`。
验证范围是文本/代码任务，不包括 GLM 多模态，也不是无限额度/账单的审计。

## 验证证据

- [回归测试](tests.log)：24/24 通过；[修复前失败证据](tests-red.log)。
- [记录器测试](ledger-tests.log)：3/3 通过，证明原请求/响应透传、缓存阶段禁止 HTTP、模型身份异常拒绝。
- [oracle 自检](oracle-selfcheck.json)：15 道公开题与 45 道隐藏题全部满分，仅为离线判分自检。
- [机器核验结果](verification.json)：两个模型各 8 份结果可按原身份缓存复用且字节不变；
  各 4 组错误 seed 拒绝且无落盘变化；缓存验证新增 HTTP=0。
- [冻结协议](protocol.json)：记录源码、任务、参考文件的哈希及相同样本 ID；新旧身份不同。
  上轮 12 份运行 JSON 证据校验一致；旧周期的当前源码校验应因 B05 源码变化而拒绝复跑。
- [执行环境](environment.json)：记录 Python、LibreOffice、依赖版本和 Git 基点。
- [MiniMax 请求记录](minimax/requests.json)、[GLM 请求记录](glm/requests.json)：
  保留响应 ID、实际模型、请求/响应哈希和 usage；密钥及隐藏题正文不落盘。
  这些是客户端实测证据，不是服务端签名的真实性证明或收费账单。
- [GLM 恢复请求记录](glm-recovery/requests.json)：单独记录续跑调用；原超时调用不覆盖。

## 复核命令

在仓库根目录执行（均为离线验证）：

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python report/2026-09-06-b05-live/test_response_ledger.py -v
.venv/bin/python report/2026-09-06-b05-live/verify_artifacts.py
git diff --check
```

冻结目录已准备且执行完毕，不应再次 `--prepare`。
如执行以下命令，只允许在源码/协议哈希仍相同时复用缓存；源码变化将拒绝并要求新目录。

```sh
.venv/bin/python report/2026-09-06-b05-live/run_experiment.py --execute minimax
.venv/bin/python report/2026-09-06-b05-live/recover_glm.py
```

## 后续小步

先单独核验 `ssb_22_47` 原题排序语义与 gold 的一致性，决定是否需要一个独立任务修订周期。
然后按任务族预先抽样扩大验证，记录格式错误、算法错误、题面歧义、解析截断各自占比。
本轮仅为 8 道便利样本，且两个模型单次生成设置不同，不能外推总体能力或据此排名。
本轮未提交 commit，未推送；原工作区的 SciCode LFS 删除和 CFDB 修改均保留。
'''
(HERE/'README.md').write_text(text)
print(HERE/'README.md')
