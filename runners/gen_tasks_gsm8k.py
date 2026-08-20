"""gen_tasks_gsm8k.py — 从镜像 GSM8K 生成任务 YAML + 题面。

生成物（幂等，--check 校验）：
  tasks/gsm8k.math_reasoning/gsm8k_q<NNNN>.yaml   250 个任务契约
  tasks/gsm8k.math_reasoning/gsm8k_q<NNNN>.md     250 个题面（官方 question 原文 + #### 格式要求）

抽样口径（公共可比层的成本-代表性折中）：
  test split 1319 题中确定性 RNG（np.random.default_rng(20260821)）抽 250 题；
  RNG seed 落盘于此，重跑即复现；全量镜像仍在 data/（不走题面也能重抽）。

协议（qa_grounded / math_answer）：
  gate         = 模型输出最终数可解析（#### 优先 -> answer is -> 末数）
  requirements = 数值精确匹配（numeric_rel_tol=1e-6，等效精确，抗字面格式差）
  physics/objective/robustness = N/A（权重 0）
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import yaml

from .common import sha256_file

BENCH = Path(__file__).resolve().parent.parent
DATA = BENCH / "data/gsm8k/math_reasoning"
TASKS_DIR = BENCH / "tasks/gsm8k.math_reasoning"
ASSETS_REVISION = "gsm8k@openai-master+test.jsonl_20260821"
SAMPLE_SEED = 20260821
SAMPLE_N = 250


def extract_ref(answer_field: str) -> float:
    """官方口径：answer 末行 '#### <num>' 取首数字 token（去千分位逗号/货币符）。"""
    tail = answer_field.rsplit("####", 1)[1]
    import re as _re
    tok = _re.findall(r"-?\$?\d[\d,]*(?:\.\d+)?", tail)[0]
    return float(tok.strip().lstrip("$").replace(",", ""))


def build_prompt_md(question: str) -> str:
    return (question.rstrip()
            + "\n\nThink step by step, then give the final numeric answer on the "
              "last line in the exact format:\n#### <number>\n")


def task_yaml(idx: int, ref_num: float, data_digest: str, prompt_sha: str) -> dict:
    tid = f"gsm8k_q{idx:04d}"
    return {
        "id": tid,
        "registry_id": "gsm8k.math_reasoning",
        "domain": "knowledge",
        "task_type": "qa_grounded",
        "model_profile": "plain_llm",
        "assets_revision": ASSETS_REVISION,
        "environment_digest": "computed-at-runtime",
        "hidden": False,
        "allowed_tools": [],
        "input": {
            "prompt_file": f"tasks/gsm8k.math_reasoning/{tid}.md",
            "prompt_sha256": prompt_sha,
            "assets": [
                {"path": "data/gsm8k/math_reasoning/test.jsonl",
                 "digest": data_digest},
            ],
        },
        "output_contract": ["answer"],
        "reference": {
            "source": "GSM8K test.jsonl（MIT, openai/grade-school-math）",
            "revision": ASSETS_REVISION,
            "question_index": idx,
            "reference_number": ref_num,
            "refusal_expected": False,
            "uncertainty_note": "参考数为官方 #### 标注，唯一确定；容差 1e-6 等效精确匹配",
        },
        "grader": {
            "answer_format": "math_answer",
            "validity_gate": True,
            "objective_layer": "numeric_exact",
            "parse_rule": "hash_hash_hash_then_answer_is_then_last_number",
            "numeric_rel_tol": 1.0e-6,
            "evidence_layer": False,
            "refusal_layer": False,
            "distinction_layer": False,
            "robustness_samples": 1,
        },
        "scoring": {
            "weights": {"physics": 0.0, "requirements": 1.0, "objective": 0.0,
                        "robustness": 0.0},
            "note": "纯数值答案：physics/objective/robustness 不适用（result.json 标注 N/A），"
                    "权重经 YAML 覆写塌缩到 requirements",
        },
        "limits": {"cpu": 1, "memory_gb": 2, "wall_clock_s": 600, "attempts": 3},
        "license_provenance": {
            "source": "openai/grade-school-math",
            "license": "MIT",
            "status": "confirmed-repo",
            "revision": ASSETS_REVISION,
            "mirror_allowed": True,
        },
    }


def _read_no_translate(p: Path) -> str:
    if not p.exists():
        return ""
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    rows = [json.loads(l) for l in
            (DATA / "test.jsonl").read_text(encoding="utf-8").splitlines()]
    data_digest = sha256_file(DATA / "test.jsonl")
    chosen = sorted(np.random.default_rng(SAMPLE_SEED).choice(
        len(rows), size=SAMPLE_N, replace=False).tolist())

    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    drift, n = [], 0
    for idx in chosen:
        ref_num = extract_ref(rows[idx]["answer"])
        prompt_md = build_prompt_md(rows[idx]["question"])
        prompt_sha = hashlib.sha256(prompt_md.encode()).hexdigest()
        want = yaml.safe_dump(task_yaml(idx, ref_num, data_digest, prompt_sha),
                              sort_keys=False, allow_unicode=True)
        tid = f"gsm8k_q{idx:04d}"
        ypath, ppath = TASKS_DIR / f"{tid}.yaml", TASKS_DIR / f"{tid}.md"
        if args.check:
            if _read_no_translate(ypath) != want or _read_no_translate(ppath) != prompt_md:
                drift.append(tid)
        else:
            ypath.write_text(want, encoding="utf-8")
            ppath.write_text(prompt_md, encoding="utf-8")
        n += 1
    if args.check:
        if drift:
            print(f"[check] 不一致: {drift[:5]}... 共 {len(drift)}")
            return 1
        print(f"[check] {n} 个任务与镜像一致（seed={SAMPLE_SEED}, N={SAMPLE_N}）")
        return 0
    print(f"[gen] {n} tasks -> {TASKS_DIR}（从 {len(rows)} 题 RNG seed={SAMPLE_SEED} 抽样）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
