"""gen_tasks_cfdquery.py — 从镜像 CFDQuery.json 生成任务 YAML + 题面 prompt 文件。

生成物（全部可重入：重跑覆盖且结果一致）：
  benchmarks/tasks/cfdllm.cfdquery/cfdquery_q###.yaml   90 个任务契约
  benchmarks/tasks/cfdllm.cfdquery/cfdquery_q###.md     90 个题面文件

设计要点：
  - 字段严格套 contracts/task.example.yaml；
  - assets_revision + 数据 sha256 写死进每个 YAML（评测时逐题校验，防数据漂移）；
  - cfdquery 为纯 MCQ：无证据语料/拒答/区分层 => 子分只有客观层适用，
    权重按契约机制覆写为 requirements=1.0（见 YAML 内注释与 M1-summary）；
  - 题面不内联进 YAML，落 .md 便于版本化与 diff。

用法（benchmarks/ 下）：
  python3 -m runners.gen_tasks_cfdquery            # 生成/校验
  python3 -m runners.gen_tasks_cfdquery --check    # 只校验不写
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from .common import sha256_file

BENCH = Path(__file__).resolve().parent.parent
DATA = BENCH / "data/cfdllm/cfdquery/CFDQuery.json"
TASKS_DIR = BENCH / "tasks/cfdllm.cfdquery"
ASSETS_REVISION = "cfdquery@3b46d30+kaggle_v4"

WEIGHTS_NOTE = (
    "纯 MCQ 无证据/拒答/区分层：physics/objective 不适用（result.json 标注 N/A），"
    "权重经 YAML 覆写塌缩到 requirements（adapter 契约的覆写机制，非静默改分）"
)


def _read_no_translate(p: Path) -> str:
    if not p.exists():
        return ""
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


def build_prompt(q: dict) -> str:
    lines = [q["question_content"].strip(), ""]
    for opt in q["options"]:
        lines.append(f"{opt['option_index']}. {opt['option_content'].strip()}")
    lines += ["", "Answer with only the number (1, 2, 3, or 4)."]
    return "\n".join(lines) + "\n"


def task_yaml(q: dict, digest: str) -> dict:
    tid = f"cfdquery_q{q['question_index']:03d}"
    return {
        "id": tid,
        "registry_id": "cfdllm.cfdquery",
        "domain": "knowledge",
        "task_type": "qa_grounded",
        "model_profile": "plain_llm",
        "assets_revision": ASSETS_REVISION,
        "environment_digest": "computed-at-runtime",  # dev 终端运行时计算（common.environment_digest）
        "hidden": False,
        "allowed_tools": [],                          # plain_llm：无工具白名单
        "input": {
            "prompt_file": f"tasks/cfdllm.cfdquery/{tid}.md",
            "assets": [
                {"path": "data/cfdllm/cfdquery/CFDQuery.json", "digest": digest},
            ],
        },
        "output_contract": ["answer"],                # 缺答案字段 = missing_output
        "reference": {
            "source": "CFDQuery.json (BSD-3-Clause, NREL-Theseus/cfdllmbench)",
            "revision": ASSETS_REVISION,
            "question_index": q["question_index"],
            "correct_option_index": q["correct_option_index"],
            "n_options": len(q["options"]),
            "refusal_expected": False,
            "uncertainty_note": "客观题唯一答案，无不确定度",
        },
        "grader": {
            "validity_gate": True,
            "objective_layer": "exact_match",         # 选择题选项精确匹配
            "parse_rule": "strict_then_tolerant_first_digit_1_to_4",
            "evidence_layer": False,                  # 无证据语料 -> physics N/A
            "refusal_layer": False,
            "distinction_layer": False,               # 无区分层 -> objective 并入 requirements
            "robustness_samples": 1,
        },
        "scoring": {
            # 覆写默认权重：不适用的层权重归零（子分仍在 result.json 全报告并标注 N/A）
            "weights": {"physics": 0.0, "requirements": 1.0,
                        "objective": 0.0, "robustness": 0.0},
            "note": WEIGHTS_NOTE,
        },
        "limits": {"cpu": 1, "memory_gb": 2, "wall_clock_s": 600, "attempts": 3},
        "license_provenance": {
            "source": "NREL-Theseus/cfdllmbench + Kaggle nithinsekhar/cfdquery",
            "license": "BSD-3-Clause",
            "status": "confirmed-repo",
            "revision": ASSETS_REVISION,
            "mirror_allowed": True,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只校验已生成文件的一致性")
    args = ap.parse_args()

    import json
    questions = json.loads(DATA.read_text(encoding="utf-8"))["CFD QA"]
    assert len(questions) == 90, f"预期 90 题，实际 {len(questions)}"
    digest = sha256_file(DATA)

    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    drift = []
    for q in questions:
        tid = f"cfdquery_q{q['question_index']:03d}"
        ypath = TASKS_DIR / f"{tid}.yaml"
        ppath = TASKS_DIR / f"{tid}.md"
        want_yaml = yaml.safe_dump(task_yaml(q, digest), sort_keys=False,
                                   allow_unicode=True)
        want_prompt = build_prompt(q)
        if args.check:
            # newline=""：禁止 universal-newline 翻译——上游数据含真实 CR/LF（q74 另有
            # 坏 \rho 转义产生的孤立 CR，见 PROVENANCE.md），必须按字节忠实比对
            got_y = _read_no_translate(ypath)
            got_p = _read_no_translate(ppath)
            if got_y != want_yaml or got_p != want_prompt:
                drift.append(tid)
        else:
            ypath.write_text(want_yaml, encoding="utf-8")
            ppath.write_text(want_prompt, encoding="utf-8")

    if args.check:
        if drift:
            print(f"[check] 与镜像不一致的任务: {drift}（重跑生成器修复）")
            return 1
        print(f"[check] {len(questions)} 个任务 YAML 与镜像一致 (assets {digest[:12]}…)")
        return 0
    print(f"[gen] {len(questions)} tasks -> {TASKS_DIR}")
    print(f"      data sha256 = {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
