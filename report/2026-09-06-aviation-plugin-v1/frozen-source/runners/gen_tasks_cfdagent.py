"""gen_tasks_cfdagent.py — 从 cfdagent 语料生成 litbench 任务 YAML + 题面。

语料链路（全部可重入，重跑覆盖且结果一致）：
  data/cfdagent/litbench/papers_raw.json   arXiv Atom API 抓取原文（runners.arxiv_corpus.fetch）
  data/cfdagent/litbench/papers.json       策展层：+分类/venue/代码仓/许可证（摘要与 sha256 原样继承）
  data/cfdagent/litbench/questions.json    题库：每题 evidence 必须是对应摘要的逐字子串
  → tasks/cfdagent.litbench/cfdagent_q###.yaml + .md

防幻觉纪律（生成时强制，任何一条不过即退出非零）：
  1. evidence 引文（去空白归一后）必须是 papers.json 中对应论文摘要的子串；
  2. field:published:<id> 型 evidence 引语料库发布日期字段；
  3. answer 下标合法、4 选项、无重复选项；
  4. 题面 prompt_sha256 与摘要 sha256 写死进任务 YAML（评测时逐题校验）。

用法（仓库根）：
  python3 -m runners.gen_tasks_cfdagent            # 生成/覆盖
  python3 -m runners.gen_tasks_cfdagent --check    # 只校验不写
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

from .common import sha256_file

BENCH = Path(__file__).resolve().parent.parent
DATA = BENCH / "data/cfdagent/litbench"
TASKS_DIR = BENCH / "tasks/cfdagent.litbench"
ASSETS_REVISION = "cfdagent-litbench@2026-08-28"

WEIGHTS_NOTE = (
    "纯 MCQ 无证据语料/拒答/区分层：physics/objective 不适用（result.json 标注 N/A），"
    "权重经 YAML 覆写塌缩到 requirements（adapter 契约的覆写机制，非静默改分）；"
    "题目为 agent-CFD 文献知识客观题，答案锚定摘要逐字引文（见 data/cfdagent/litbench/questions.json）"
)


def _norm(s: str) -> str:
    """空白归一化（保留其余字符），用于引文子串校验。"""
    return re.sub(r"\s+", " ", s).strip()


class ValidationError(RuntimeError):
    pass


def validate(questions: list[dict], papers: list[dict]) -> dict[str, dict]:
    """返回 base_id -> paper；任何引文/结构问题直接 raise。"""
    by_id = {p["base_id"]: p for p in papers}
    errors: list[str] = []
    for q in questions:
        qid = q["qid"]
        if len(q["options"]) != 4 or len(set(q["options"])) != 4:
            errors.append(f"{qid}: 选项必须为 4 个且互不重复")
        if not (0 <= q["answer"] < len(q["options"])):
            errors.append(f"{qid}: answer 下标越界")
        for pid in q["papers"]:
            if pid not in by_id:
                errors.append(f"{qid}: 引用论文 {pid} 不在语料库")
        for ev in q["evidence"]:
            if ev.startswith("field:published:"):
                pid = ev.rsplit(":", 1)[-1]
                if pid not in by_id:
                    errors.append(f"{qid}: field evidence 指向未知论文 {pid}")
                continue
            abstracts = [_norm(by_id[p]["abstract"]) for p in q["papers"] if p in by_id]
            if abstracts and not any(_norm(ev) in a for a in abstracts):
                errors.append(f"{qid}: 引文不是任何被引论文摘要的子串 -> {ev[:60]}...")
    if errors:
        raise ValidationError("题库校验失败:\n  " + "\n  ".join(errors))
    return by_id


def build_prompt(q: dict) -> str:
    lines = [q["question"].strip(), ""]
    for i, opt in enumerate(q["options"], start=1):
        lines.append(f"{i}. {opt}")
    lines += ["", "Answer with only the number (1, 2, 3, or 4)."]
    return "\n".join(lines) + "\n"


def task_yaml(q: dict, paper: dict | None, qidx: int, digest_q: str, digest_p: str,
              evidence_display: list[str]) -> dict:
    src_papers = "; ".join(q["papers"])
    source = (
        f"arXiv 摘要锚定自建题（corpus papers.json abstract_sha256 锁定；主引论文 {src_papers}）"
    )
    return {
        "id": q["qid"],
        "registry_id": "cfdagent.litbench",
        "domain": "cfd",
        "task_type": "qa_grounded",
        "model_profile": "plain_llm",
        "assets_revision": ASSETS_REVISION,
        "environment_digest": "computed-at-runtime",
        "hidden": False,
        "allowed_tools": [],
        "input": {
            "prompt_file": f"tasks/cfdagent.litbench/{q['qid']}.md",
            "prompt_sha256": None,  # 生成后由 main 回填
            "assets": [
                {"path": "data/cfdagent/litbench/questions.json", "digest": digest_q},
                {"path": "data/cfdagent/litbench/papers.json", "digest": digest_p},
            ],
        },
        "output_contract": ["answer"],
        "reference": {
            "source": source,
            "revision": ASSETS_REVISION,
            "question_index": qidx,
            "qtype": q["qtype"],
            "paper_ids": q["papers"],
            "paper_published": paper["published"] if paper and len(q["papers"]) == 1 else None,
            "evidence": evidence_display,
            "correct_option_index": q["answer"] + 1,  # qa_grounded 契约：1 起始
            "n_options": 4,
            "refusal_expected": False,
            "uncertainty_note": "客观题唯一答案，引文锚定摘要原文；无不确定度",
        },
        "grader": {
            "validity_gate": True,
            "objective_layer": "exact_match",
            "parse_rule": "strict_then_tolerant_first_digit_1_to_4",
            "evidence_layer": False,
            "refusal_layer": False,
            "distinction_layer": False,
            "robustness_samples": 1,
        },
        "scoring": {
            "weights": {"physics": 0.0, "requirements": 1.0,
                        "objective": 0.0, "robustness": 0.0},
            "note": WEIGHTS_NOTE,
        },
        "limits": {"cpu": 1, "memory_gb": 2, "wall_clock_s": 600, "attempts": 3},
        "license_provenance": {
            "source": "题面为自建（confirmed-selfbuilt）；引文为 arXiv 摘要（API 公开元数据，逐题署名 arXiv id）",
            "license": "self-built questions; arXiv abstract metadata via public API",
            "status": "confirmed-selfbuilt",
            "revision": ASSETS_REVISION,
            "mirror_allowed": True,
        },
    }



def _read_no_translate(p):
    if not p.exists():
        return ""
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只校验已生成文件的一致性")
    args = ap.parse_args()

    questions = json.loads((DATA / "questions.json").read_text(encoding="utf-8"))["questions"]
    papers = json.loads((DATA / "papers.json").read_text(encoding="utf-8"))
    by_id = validate(questions, papers)  # 校验不过直接 raise -> 非零退出
    digest_q = sha256_file(DATA / "questions.json")
    digest_p = sha256_file(DATA / "papers.json")

    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    drift = []
    for i, q in enumerate(questions, start=1):
        assert q["qid"] == f"cfdagent_q{i:03d}", f"qid 与顺序不一致: {q['qid']}"
        paper = by_id[q["papers"][0]] if len(q["papers"]) == 1 else None
        evidence_display = [
            (by_id[ev.rsplit(":", 1)[-1]]["published"] if ev.startswith("field:published:")
             else ev)
            for ev in q["evidence"]
        ]
        y = task_yaml(q, paper, i, digest_q, digest_p, evidence_display)
        prompt = build_prompt(q)
        import hashlib
        y["input"]["prompt_sha256"] = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        want_yaml = yaml.safe_dump(y, sort_keys=False, allow_unicode=True)
        want_prompt = prompt
        ypath = TASKS_DIR / f"{q['qid']}.yaml"
        ppath = TASKS_DIR / f"{q['qid']}.md"
        if args.check:
            got_y = _read_no_translate(ypath)
            got_p = _read_no_translate(ppath)
            if got_y != want_yaml or got_p != want_prompt:
                drift.append(q["qid"])
        else:
            ypath.write_text(want_yaml, encoding="utf-8")
            ppath.write_text(want_prompt, encoding="utf-8")

    if args.check:
        if drift:
            print(f"[check] 与生成器不一致的任务: {drift}（重跑生成器修复）")
            return 1
        print(f"[check] OK — {len(questions)} 任务全部一致")
        return 0
    print(f"[gen] 写出 {len(questions)} 任务 -> {TASKS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
