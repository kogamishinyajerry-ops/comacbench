"""Render the verified repair evidence; never changes scores or calls a provider."""
from pathlib import Path
import json

HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent/'2026-09-06-expanded-24-v2'


def read(p):return json.loads(p.read_text())


def main():
    verified=read(HERE/'verification.json');assert verified['status']=='passed'
    old=read(PRIOR/'verification.json');offline=read(HERE/'offline/summary.json')
    overall=[];groups=[];cells=[];fields=[];usage=[];replays=[]
    for alias in ['minimax','glm']:
        m=verified['models'][alias];p=old['models'][alias]
        overall.append(f'| {m["model"]} | {p["gate_passed"]}/24，{p["full_score"]}/24 | {m["gate_passed"]}/24，{m["full_score"]}/24 | {m["requests"]} |')
        for g in m['groups']:
            groups.append(f'| {alias} | {g["group"]} | {g["gate_passed"]}/6 | {g["full_score"]}/6 |')
        for d in m['table_diagnostics']:
            hits=f'{d["changed_matched"]}/{d["changed_total"]}' if d['changed_matched'] is not None else '未生成可测工作簿'
            damage=d['unchanged_damaged'] if d['unchanged_damaged'] is not None else '不可测'
            cells.append(f'| {alias} | {d["task_id"]} | {d["score"]:g} | {hits} | {damage} |')
        for d in m['field_diagnostics']:
            fields.append(f'| {alias} | {d["task_id"]} | {", ".join(d["failed_fields"])} |')
        u=m['usage'];usage.append(f'| {m["model"]} | {u["prompt_tokens"]} | {u["completion_tokens"]} | {u["total_tokens"]} |')
    for r in offline['prior_code_replays']:
        replays.append(f'| {r["model"]} | {r["task_id"]} | {r["prior_score"]:g} | {r["score"]:g} |')
    controls=[f'| {r["task_id"]} | {r["correct"]:g} | {r["unchanged"]:g} | {r["partial"]:g} | {r["damaged"]:g} |' for r in offline['controls']]
    text='''# B03 判分修复、B05 输入澄清与相同样本真实复跑

先修判分，再澄清输入；以相同 24 题、seed=20260906 和原生 provider 设置验证。
新旧成绩各自保留。表格旧代码离线重判单独记录，用来观察 B03 的影响；新真实调用使用 B05 澄清后的输入。
模型满分数只描述这批修复验证样本，不能据此发布模型排名或推断总体能力。

## 本轮实测

| 模型 | 上轮有效、满分 | 本轮有效、满分 | 本轮 HTTP 请求 |
| --- | --- | --- | ---: |
'''+ '\n'.join(overall)+'''

| 模型 | 分组 | 有效 | 满分 |
| --- | --- | ---: | ---: |
'''+ '\n'.join(groups)+'''

## B03 变更

`runners/design_artifact.py` 在答题范围内比较 input/gold 非空坐标的并集。
gold 的空值是清空要求；原本空白处新增内容会扣分。空白背景不贡献命中。
正确的全清空任务可提交空答题区域；如果 gold 仍有内容，候选全空仍被 gate 拦截。
四舍五入不能把存在错误的结果变成满分。保留权重、数值容差及非表格适配器行为。

新的比较发现旧 oracle 只写 gold 非空值，也遗漏了清空步骤。
25 份 oracle 脚本只增加清空步骤，内嵌参考值列表不变；生成器同步修复，并支持带工作表前缀的区域。
参考工作簿、原始输入与上游数据均未修改。

## B05 变更

- 模型实际收到的表格契约明确要求执行数据操作，输出处理后的 output.xlsx；VBA 说明不写入数据区域，保留无关值和公式。
- ssb_279_23 明确移除括号本身；ssb_455_35 明确保留第 1 行表头、从第 2 行筛选。
- family 只取 Category 括号内的族名；clause_id 只取 Document 标识符；clause_no/clause_ref 保留 §。
- 24 道公开题仅改题面与 SHA256；45 道隐藏题的参考答案与 exact_keys 不变。
  新身份包含源码与有效题面摘要，旧输出目录不能被新身份复用。
- ssb_22_47 的主排序/列职责冲突仍隔离，本轮未选择一种解释改写 gold。

## 正负控与旧答案重判

以下为真实生产判分路径上的离线构造样本，新增模型请求为 0。
正确参考输出必须满分，原样复制、只完成部分变更、正确输出再破坏一格都必须低于满分。

| 题目 | 正确 | 原样复制 | 部分完成 | 破坏一格 |
| --- | ---: | ---: | ---: | ---: |
'''+ '\n'.join(controls)+'''

ssb_455_35 原样复制由上轮 1.0 降为 0.50005。约 0.5 来自原权重中的工作簿结构项，
并不表示完成了一半删除操作；该题关键数据删除率为 0。
其他大表仍可能因未变单元格多而取得接近 1 的分数，因此同时报告关键变更命中，未擅自调整权重。

| 旧代码来源 | 题目 | 历史原分 | 相同旧代码按新规则离线重判 |
| --- | --- | ---: | ---: |
'''+ '\n'.join(replays)+'''

重判使用上轮公开完整响应提取的原代码及不变的 gold，未再次请求模型，也不覆盖历史原分。
“新规则对旧代码的影响”与“新输入下模型重新作答的表现”由两份证据分别支持。

## 本轮表格关键变更

| 模型 | 题目 | 当前总分 | 关键变更命中 | 未变单元格损坏 |
| --- | --- | ---: | ---: | ---: |
'''+ '\n'.join(cells)+'''

## 本轮未满分 QA

'''+ ('| 模型 | 题目 | 未通过字段 |\n| --- | --- | --- |\n'+'\n'.join(fields) if fields else '本轮 QA 全部满分。')+'''

## 已定位的 MiniMax 表格失败

ssb_269_43 收集了应删除的行号，随后使用 `sorted(rows_to_delete)` 按升序删除。
行号移位造成 I6 的 95704.64 残留。关键变更 10/11，原本不需改变的内容没有损坏，总分 0.98。
唯一未通过位置是 gold 要求为空的格子，正是旧判分会漏掉的错误类型。

ssb_290_27 的最终答复仅提交打印列 B 的探查脚本，没有保存 output.xlsx。
完整原始响应 finish_reason=stop，最终答复之外的思考段含代码草稿，但不作为提交答案执行。
因此这是本轮最终交付失败，gate 正确置零；未把思考草稿选作答案，也未按分数补跑。

以上是实际生成代码/产物的归因，不是对模型总体算法能力的推断。

## 证据与复现

- 35 项仓库测试、4 项请求记录器测试通过；25/25 canonical 表格 oracle 和 24/24 本协议 oracle 满分。
- 24 份正负控、12 份旧代码重放均为离线；初次 oracle 缺失清空与区域前缀失败的校准目录保留。
- 511 份既有报告/结果文件哈希保持不变；canonical YAML 除已声明的 prompt_sha256 外全部语义不变。
- 两模型各 24 份缓存结果字节一致，各 4 组错误 seed 续跑被拒绝，验证阶段新增 HTTP=0。
- 沿用上轮的表格实验容差副本：5 题为 0；ssb_341_40 为 1e-12，处理重算浮点尾差。
- 两模型 temperature=0、max_tokens=32768，MiniMax 默认思考、GLM thinking enabled；单请求超时 1800 秒。
  没有总预算上限，没有按分数补跑；解析失败沿用 provider 原有有限重试。

| 模型 | 输入 token | 输出 token | 总 token |
| --- | ---: | ---: | ---: |
'''+ '\n'.join(usage)+'''

[协议](protocol.json)、[机器核验](verification.json)、[离线控制与重判](offline/summary.json)、
[MiniMax 请求记录](minimax/requests.json)、[GLM 请求记录](glm/requests.json)。
公开完整响应保存在各模型 responses/，表格原始/重算工作簿在 workbooks/；隐藏模型正文不落盘。
这是客户端实测记录，不是服务端签名或费用账单。

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python report/2026-09-06-b03-b05-v2/test_ledger.py -v
.venv/bin/python report/2026-09-06-b03-b05-v2/verify_evidence.py
git diff --check
```

源码/任务未变时，可用 run_experiment.py --execute minimax 或 --execute glm 复用现有缓存；
身份变化必须使用新目录。开发阶段修改前的快照、负控失败记录和修订说明均保留在本目录。

## 尚未关闭的边界

当前表格指标主要覆盖声明范围内的值与已有工作簿 gate，不代表全部样式、格式、其他区域内容均已验收。
结构分与大量未变值仍会抬高总分；应继续用关键变更/负控作为题库准入条件。
标识符类型化比较及排序题的独立版本修订仍待处理。本轮未提交、推送或部署。
'''
    (HERE/'README.md').write_text(text)


if __name__=='__main__':main()
