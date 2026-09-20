#!/usr/bin/env python3
"""gen_tasks_awcom.py — awcom.compliance 适航审定工程轴（P1，2026-08-26 立项）。

三族（自建 ACX 虚构规章框架——与 awext 同 DNA，KB 恢复后按 doc_id 重锚）：
  acam  符合性方法矩阵（决策表在题面）
  rev   条款修订影响
  trc   审定文档链追溯

首批带受控隐藏层接线（M10）：公开 15 题（每族 5，seed 1001-1005）+ hidden 池
45 题（generator.py+answers.b64，运行时经 runners.hidden_runtime 动态物化，
题面不落盘，summary 附 hidden-public 分差）。单一事实源：族生成器在
data/awcom/compliance/hidden/generator.py，本脚本经 importlib 调用。

判分：qa_grounded json_extract（exact_keys：MC 码/计数/old-new/severity 精确）。

用法：.venv/bin/python -m runners.gen_tasks_awcom   （幂等；生成后内嵌自检）
"""
from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
RID = "awcom.compliance"
TASKS_DIR = BENCH / "tasks" / RID
HIDDEN_DIR = BENCH / "data" / "awcom" / "compliance" / "hidden"
REV = "awcom@selfbuilt-2026-08-26"


def _load_gen_module():
    spec = importlib.util.spec_from_file_location(
        "awcom_hidden_gen", HIDDEN_DIR / "generator.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def emit_public(mod) -> int:
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    n = 0
    for fam, gen in mod.GENS.items():
        for i in range(1, 6):
            tid = f"awc_{fam}_{i:02d}"
            prompt, ref = gen(1000 + i)
            exact = mod.EXACT[fam]
            psha = hashlib.sha256(prompt.encode()).hexdigest()
            (TASKS_DIR / f"{tid}.md").write_text(prompt, encoding="utf-8")
            exact_txt = "\n".join(f"  - {k}" for k in exact)
            ref_json = json.dumps(ref, ensure_ascii=False).replace("'", '"')
            yml = f"""id: {tid}
registry_id: {RID}
domain: airworthiness
task_type: qa_grounded
model_profile: plain_llm
assets_revision: {REV}
environment_digest: computed-at-runtime
hidden: false
allowed_tools: []
input:
  prompt_file: tasks/{RID}/{tid}.md
  prompt_sha256: {psha}
  assets: []
output_contract:
- json
reference:
  source: 自建 ACX 规章框架（决策表在题面；KB 恢复后重锚真实条款）
  revision: {REV}
  reference_json: {ref_json}
  rel_tol: 0.02
  uncertainty_note: json_extract 字段级（exact_keys 精确；列表排序 casefold）
grader:
  answer_format: json_extract
  validity_gate: true
  numeric_rel_tol: 0.02
  exact_keys:
{exact_txt}
  sandbox:
    banned: shell/network/process
    isolated_interpreter: false
scoring:
  weights:
    requirements: 1.0
    physics: 0.0
    objective: 0.0
    robustness: 0.0
  note: requirements=JSON 字段命中比例
limits:
  cpu: 1
  memory_gb: 2
  wall_clock_s: 180
  attempts: 3
license_provenance:
  source: 自建（适航审定工程族 P1；ACX 虚构规章）
  license: self-built
  status: confirmed-selfbuilt
  mirror_allowed: true
  revision: {REV}
"""
            (TASKS_DIR / f"{tid}.yaml").write_text(yml, encoding="utf-8")
            n += 1
    return n


def freeze_answers(mod) -> int:
    out = mod.gen()
    recs = [{"id": it["id"],
             "prompt_sha256": hashlib.sha256(it["prompt"].encode()).hexdigest(),
             "reference_json": it["reference_json"],
             "exact_keys": it["exact_keys"]} for it in out["pool"]]
    (HIDDEN_DIR / "answers.b64").write_bytes(
        base64.b64encode(json.dumps(recs, ensure_ascii=False).encode()))
    return len(recs)


def _oracle_text(ref):
    return "```json\n" + json.dumps(ref, ensure_ascii=False, indent=2) + "\n```"


def selfcheck(mod):
    from runners.qa_grounded import extract_json_object, grade_json_extract
    from runners.hidden_runtime import load_hidden_pool
    ok = 0
    for fam, gen in mod.GENS.items():
        for i in range(1, 6):
            prompt, ref = gen(1000 + i)
            got = extract_json_object(_oracle_text(ref))
            score, _ = grade_json_extract(ref, got, 0.02, mod.EXACT[fam])
            assert score == 1.0, f"公开 {fam}_{i} oracle 自检 {score}"
            ok += 1
    tasks, prompts, rev = load_hidden_pool(BENCH, RID)
    assert len(tasks) == mod.POOL_PER_FAM * 3
    for t in tasks[:3]:
        ref = t["reference"]["reference_json"]
        got = extract_json_object(_oracle_text(ref))
        score, _ = grade_json_extract(ref, got, 0.02, t["grader"]["exact_keys"])
        assert score == 1.0
    pub_shas = {hashlib.sha256(gen(1000 + i)[0].encode()).hexdigest()
                for g in mod.GENS.values() for i in range(1, 6)}
    hid_shas = {hashlib.sha256(p.encode()).hexdigest() for p in prompts.values()}
    assert not (pub_shas & hid_shas), "公开/隐藏题面重叠"
    return ok, len(tasks), rev, len(pub_shas & hid_shas)


def main() -> int:
    mod = _load_gen_module()
    n_pub = emit_public(mod)
    n_pool = freeze_answers(mod)
    ok, pool_n, rev, overlap = selfcheck(mod)
    print(f"public {n_pub} 题；hidden 池 {n_pool} 题（rev {rev}）")
    print(f"自检：公开 oracle 判分 {ok}/15 满分；hidden 池加载+校验+抽检 3 题 OK；"
          f"公开/隐藏重题 {overlap}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
