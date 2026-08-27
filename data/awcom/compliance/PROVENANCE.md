# PROVENANCE — awcom.compliance（适航审定工程族，P1 主攻，2026-08-26）

> 立项依据：report/2026-08-26-civil-aviation-fit-assessment.md P1（含 M10 前置）。
> 生成器 `runners/gen_tasks_awcom.py`；**单一事实源** = `hidden/generator.py`
> （公开题 seed 1001-1005/族，隐藏池 seed 独立段，sha 交叉验证零重题）。

## 1. 任务协议与判分

- 三族（ACX 虚构规章框架，KB 恢复后按 doc_id 重锚真实条款——civair-kb 本会话
  三端点仍不返回内容，如实降级同 awext）：
  - **acam**：条款卡+可用证据 → 主/次符合性方法（MC0-MC9 决策表**在题面**，
    纯规则应用非领域记忆）+ witnesses/documented_only 布尔；
  - **rev**：两版条款 diff → changed_params（old/new）+适用性增删+severity+
    compliance_recheck（规则：值变或适用性变=major）；
  - **trc**：SPEC/CLAUSE/TR/AN 节选 → 证据映射+verified/test_only 参数+
    coverage_complete。
- 判分：json_extract 字段级；**exact_keys 口径**（深审 M1 修复后）：
  clause_id/primary_method/changed_param_count/old/new/severity/requirement_id/
  clause_ref 及全部 bool 精确匹配；列表排序 casefold。

## 2. 受控隐藏层（M10 接线首发——本条目为 P1 前置的兑现）

- **机制**：`runners/hidden_runtime.py` + `qa_grounded --hidden N`——
  data/awcom/compliance/hidden/{generator.py, answers.b64} 运行时物化，
  按 seed 抽 N 题（轮换），题面**不进静态任务目录**；
- **answers.b64 冻结校验**：池 id/prompt_sha256/reference/exact_keys 逐条
  与生成器输出比对，漂移即 fail-fast；
- **防泄漏纪律（实测验证）**：hidden result 落盘前剥除 answer/raw/code/logs
  回显与字段 got/ref 值（仅保 field/ok/exact + prompt_sha256 + 聚合）——
  残留扫描（ACX-/SPEC-/Amendment/TR-）零命中；调试粒度降级为聚合是受控层代价；
- **hidden-public 分差**（scoring §5 首次兑现）：同级 `<provider>` 公开目录
  存在时输出 hidden_public_gap.json（总体+分族）；
- **诚实边界**：hidden ≠ 对人保密（生成器与 answers 在 git，同 gold 信任模型）；
  其价值=静态题库零暴露+可轮换+分差可监控。

## 3. 自检记录（2026-08-26）

- 公开 oracle 判分 15/15 满分；stub 地板；
- hidden 池 45 题加载+冻结校验+抽检 3 题 oracle 满分；公开/隐藏重题 0；
- hidden oracle 端到端（--hidden 3）：gap +0.0000（h=1.0/p=1.0），防泄漏
  残留检查通过。

## 4. 校准记录（2026-08-26 首轮 hidden-public 分差实测）

- 分层抽样修正（实测教训）：裸 sample 曾致 8 题仅 1 rev 且恰为零变更题
  （hidden=1.0 抽样伪影）→ 改按族前缀轮转均衡；
- 首轮分差：M3 +0.0635 / GLM +0.0450，**全部来自 rev 族**（+0.18/+0.16）——
  hidden 池零变更题占比 5/15 而公开 5/5 全有变更；**池难度配比对齐为后续
  校准项**（generator 权重调整），分差监控机制本身即为发现此类失衡而建；
- awext 同口径重跑（M1 exact_keys 修复后）：0.8704→0.8889 / 0.9074→0.9074。

## 5. 复现

```bash
.venv/bin/python -m runners.gen_tasks_awcom                       # 生成+自检
.venv/bin/python -m runners.qa_grounded --tasks tasks/awcom.compliance \
    --out results/awcom.compliance/<date>/<provider> --provider <p> --seed 0
.venv/bin/python -m runners.qa_grounded --tasks tasks/awcom.compliance \
    --out results/awcom.compliance/<date>/<provider>-hidden \
    --provider <p> --seed 0 --hidden 8                            # 隐藏层
```
