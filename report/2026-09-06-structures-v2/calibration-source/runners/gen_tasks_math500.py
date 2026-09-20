"""gen_tasks_math500.py — 从镜像 MATH-500 生成任务 YAML + 题面。

生成物（幂等，--check 校验）：
  tasks/math500.math_reasoning/math500_q<NNN>.yaml   500 个任务契约
  tasks/math500.math_reasoning/math500_q<NNN>.md     500 个题面（官方 problem 原文 + boxed 指令）

任务 id = 镜像行序（0-499，镜像 sha256 锁定 => 确定性）；unique_id 存 YAML 备溯源。

协议（qa_grounded / math_answer，reference_boxed 型）：
  gate         = \boxed{} 可抽取（或 #### 数值退化兜底且参考可数值化）
  requirements = 归一化精确匹配（数值化优先：数字/a-b/\frac 比值）
  physics/objective/robustness = N/A（权重 0）
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml

from .common import sha256_file

BENCH = Path(__file__).resolve().parent.parent
DATA = BENCH / "data/math500/math_reasoning"
TASKS_DIR = BENCH / "tasks/math500.math_reasoning"
ASSETS_REVISION = "math500@hf-h4_v1_20260821"


def build_prompt_md(problem: str) -> str:
    return (problem.rstrip()
            + "\n\nSolve the problem. End your response with the final answer "
              "in \\boxed{...} on the last line.\n")


def task_yaml(idx: int, row: dict, data_digest: str, prompt_sha: str) -> dict:
    tid = f"math500_q{idx:03d}"
    return {
        "id": tid,
        "registry_id": "math500.math_reasoning",
        "domain": "knowledge",
        "task_type": "qa_grounded",
        "model_profile": "plain_llm",
        "assets_revision": ASSETS_REVISION,
        "environment_digest": "computed-at-runtime",
        "hidden": False,
        "allowed_tools": [],
        "input": {
            "prompt_file": f"tasks/math500.math_reasoning/{tid}.md",
            "prompt_sha256": prompt_sha,
            "assets": [
                {"path": "data/math500/math_reasoning/math500_test.jsonl",
                 "digest": data_digest},
            ],
        },
        "output_contract": ["answer"],
        "reference": {
            "source": "MATH-500（MIT, 上游 hendrycks/math；HF HuggingFaceH4 重建）",
            "revision": ASSETS_REVISION,
            "unique_id": row["unique_id"],
            "level": row["level"],
            "subject": row["subject"],
            "reference_boxed": row["answer"],
            "refusal_expected": False,
            "uncertainty_note": "官方 boxed 最终答案；greedy exact match 口径（归一化+数值化优先），"
                                "非符号等价，同值不同形保守判负（registry risks 已标注）",
        },
        "grader": {
            "answer_format": "math_answer",
            "validity_gate": True,
            "objective_layer": "boxed_exact_match",
            "parse_rule": "last_boxed_brace_balanced_then_hash_num_fallback",
            "numeric_rel_tol": 1.0e-6,
            "evidence_layer": False,
            "refusal_layer": False,
            "distinction_layer": False,
            "robustness_samples": 1,
        },
        "scoring": {
            "weights": {"physics": 0.0, "requirements": 1.0, "objective": 0.0,
                        "robustness": 0.0},
            "note": "纯 boxed 答案：physics/objective/robustness 不适用，权重经 YAML 覆写"
                    "塌缩到 requirements",
        },
        "limits": {"cpu": 1, "memory_gb": 2, "wall_clock_s": 900, "attempts": 3},
        "license_provenance": {
            "source": "HuggingFaceH4/MATH-500（上游 hendrycks/math）",
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
            (DATA / "math500_test.jsonl").read_text(encoding="utf-8").splitlines()]
    data_digest = sha256_file(DATA / "math500_test.jsonl")

    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    drift, n = [], 0
    for idx, row in enumerate(rows):
        prompt_md = build_prompt_md(row["problem"])
        prompt_sha = hashlib.sha256(prompt_md.encode()).hexdigest()
        want = yaml.safe_dump(task_yaml(idx, row, data_digest, prompt_sha),
                              sort_keys=False, allow_unicode=True)
        tid = f"math500_q{idx:03d}"
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
        print(f"[check] {n} 个任务与镜像一致")
        return 0
    print(f"[gen] {n} tasks -> {TASKS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
