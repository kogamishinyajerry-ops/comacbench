"""gen_tasks_aeroengqa.py — 从镜像 AeroEngQA JSON 生成任务 YAML + 题面文件。

生成物（幂等，--check 校验）：
  tasks/aeroengqa.gold/aeroengqa_{sh|mh}_{a|u}###.yaml   80 个任务契约
  tasks/aeroengqa.gold/aeroengqa_{sh|mh}_{a|u}###.md     80 个题面（含 context）

split 编码：sh/mh = single/multi-hop；a/u = answerable/unanswerable。
判分口径（qa_grounded free_text 分支，全部规则判）：
  gate          ANSWER 行缺失/空 = missing_output
  requirements  可答题：归一化精确 / 数值集容差(±5% rel) / token F1 部分分；不可答题 N/A(权重0)
  physics       拒答层(应拒答答对/误拒) + 证据层(引用覆盖 needed × 无捏造) 的均值
  objective     区分层：BASIS ∈ report/computed/inferred（数据集无 basis 参考标签，
                逐字核验不进分，见 qa_grounded.grade_distinction 注释）
  权重（YAML 覆写）：可答题 {req .40, phy .35, obj .25, rob 0}；
                     不可答题 {req 0, phy .60, obj .40, rob 0}（requirements N/A 再分配）

用法（benchmarks/ 下）：
  python3 -m runners.gen_tasks_aeroengqa [--check]
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml

from .common import sha256_file

BENCH = Path(__file__).resolve().parent.parent
DATA_DIR = BENCH / "data/aeroengqa/gold"
TASKS_DIR = BENCH / "tasks/aeroengqa.gold"
ASSETS_REVISION = "aeroengqa@zenodo.14215677-v1.0"

SPLITS = [
    # (json, prefix, answerable, context keys)
    ("AeroEngQA_single-hop.json", "sh_a", True, ["context"]),
    ("AeroEngQA_multi-hop.json", "mh_a", True, ["context-1", "context-2"]),
    ("AeroEngQA_single-hop-unanswerable.json", "sh_u", False, ["context"]),
    ("AeroEngQA_multi-hop-unanswerable.json", "mh_u", False, ["context-1", "context-2"]),
]

_WEIGHTS_ANS = {"requirements": 0.40, "physics": 0.35, "objective": 0.25, "robustness": 0.0}
_WEIGHTS_UNANS = {"requirements": 0.0, "physics": 0.60, "objective": 0.40, "robustness": 0.0}

_OUTPUT_FMT = (
    "Answer using ONLY the information in the contexts above.\n"
    "Respond EXACTLY in this three-line format:\n"
    "ANSWER: <your answer in one short sentence; write REFUSED if the contexts do not contain the answer>\n"
    "BASIS: <report | computed | inferred>  (report = stated in the contexts; "
    "computed = derived by calculation; inferred = your own inference)\n"
    "CITATION: <the context number(s) you used or checked, e.g. [1] or [1,2]>"
)


def build_prompt(q: dict, ctx_keys: list[str]) -> str:
    parts = []
    for i, key in enumerate(ctx_keys, start=1):
        parts.append(f"Context [{i}]:\n{str(q[key]).strip()}\n")
    parts.append(f"Question: {q['question'].strip()}\n")
    parts.append(_OUTPUT_FMT)
    return "\n".join(parts) + "\n"


def task_yaml(q: dict, prefix: str, answerable: bool, ctx_keys: list[str],
              digests: dict[str, str], prompt_sha: str) -> dict:
    tid = f"aeroengqa_{prefix}{int(q['id']):03d}"
    n_ctx = len(ctx_keys)
    reference: dict = {
        "source": f"AeroEngQA {'/'.join(SPLITS[i][0] for i in range(len(SPLITS)))}",
        "revision": ASSETS_REVISION,
        "question_id": q["id"],
        "split": prefix,
        "n_contexts": n_ctx,
        "needed_citations": list(range(1, n_ctx + 1)),  # multi-hop 恒需两段（数据集构造）
        "refusal_expected": not answerable,
    }
    if answerable:
        reference["reference_answer"] = str(q["answer"]).strip()
    return {
        "id": tid,
        "registry_id": "aeroengqa.gold",
        "domain": "knowledge",
        "task_type": "qa_grounded",
        "model_profile": "plain_llm",
        "assets_revision": ASSETS_REVISION,
        "environment_digest": "computed-at-runtime",
        "hidden": False,
        "allowed_tools": [],
        "input": {
            "prompt_file": f"tasks/aeroengqa.gold/{tid}.md",
            "prompt_sha256": prompt_sha,
            "assets": [{"path": f"data/aeroengqa/gold/{name}", "digest": dig}
                       for name, dig in digests.items()],
        },
        "output_contract": ["answer"],
        "reference": reference,
        "grader": {
            "answer_format": "free_text",
            "validity_gate": True,
            "objective_layer": "free_text_exact_numeric_f1",
            "numeric_rel_tol": 0.05,
            "evidence_layer": True,
            "refusal_layer": True,
            "distinction_layer": True,
            "distinction_note": ("数据集无参考 basis 标签；区分层只判 BASIS 结构合法性，"
                                 "逐字核验不进分（见 runners/qa_grounded.py 注释）"),
            "robustness_samples": 1,
        },
        "scoring": {
            "weights": _WEIGHTS_ANS if answerable else _WEIGHTS_UNANS,
            "note": ("四层齐备：req=客观层(可答题)，phy=拒答+证据，obj=区分；"
                     "robustness 样本=1 不适用权重 0；不可答题 requirements N/A 权重 0"
                     "（.60/.40 再分配到 phy/obj）"),
        },
        "limits": {"cpu": 1, "memory_gb": 2, "wall_clock_s": 600, "attempts": 3},
        "license_provenance": {
            "source": "Zenodo 10.5281/zenodo.14215677 v1.0 (CC BY 4.0)",
            "license": "CC BY 4.0",
            "status": "confirmed-dataset",
            "revision": ASSETS_REVISION,
            "mirror_allowed": True,
            "attribution": ("Silva, Marsh, Yong, Middleton, Sóbester, "
                            "AIAA-2025, doi:10.2514/6.2025-0700"),
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

    digests = {p.name: sha256_file(p) for p in sorted(DATA_DIR.glob("*.json"))}
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    n_total, drift = 0, []
    for jname, prefix, answerable, ctx_keys in SPLITS:
        questions = json.loads((DATA_DIR / jname).read_text(encoding="utf-8"))
        for q in questions:
            n_total += 1
            tid = f"aeroengqa_{prefix}{int(q['id']):03d}"
            prompt = build_prompt(q, ctx_keys)
            prompt_sha = hashlib.sha256(prompt.encode()).hexdigest()
            want_yaml = yaml.safe_dump(
                task_yaml(q, prefix, answerable, ctx_keys, digests, prompt_sha),
                sort_keys=False, allow_unicode=True)
            ypath = TASKS_DIR / f"{tid}.yaml"
            ppath = TASKS_DIR / f"{tid}.md"
            if args.check:
                if (_read_no_translate(ypath) != want_yaml
                        or _read_no_translate(ppath) != prompt):
                    drift.append(tid)
            else:
                ypath.write_text(want_yaml, encoding="utf-8")
                ppath.write_text(prompt, encoding="utf-8")
    if args.check:
        if drift:
            print(f"[check] 与镜像不一致的任务: {drift}")
            return 1
        print(f"[check] {n_total} 个任务 YAML 与镜像一致")
        return 0
    print(f"[gen] {n_total} tasks -> {TASKS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
