"""gen_tasks_scicode.py — 从镜像 SciCode（M2 子集）生成任务 YAML + 题面 + dev gold。

协议（与官方差异，如实标注）：
  - 任务粒度 = **整题**（模型一次写全部步函数）；官方为逐步骤自回归多轮。
    => 独立、可并行、可离线复跑；难度更高（无中间反馈），分数与官方榜单不可直接对比。
  - 判分 = 官方语义：每步每 test case（h5 期望 target + 数据集原始 assert 行）。
  - 特判步 13.6 / 62.1（无 h5 数值目标，官方走 txt 特判）排除判分；76.3 不在子集。
  - dev split 的 gold（general_solution）随数据集公开 => 泄漏风险，报告按 test/dev 分组；
    oracle 判分器自检用 dev gold（test split 无 gold 源，oracle 不可用——YAML 不设 oracle_source）。

用法（benchmarks/ 下）：python3 -m runners.gen_tasks_scicode [--check]
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml

from .common import sha256_file

BENCH = Path(__file__).resolve().parent.parent
DATA = BENCH / "data/scicode/physics"
TASKS_DIR = BENCH / "tasks/scicode.physics"
GOLD_DIR = DATA / "gold_dev"
ASSETS_REVISION = "scicode@e3158ea+hf_v1+test_data_h5_20240712"

EXCLUDED_STEPS = {"13.6", "62.1", "76.3"}  # 无 h5 数值目标（官方 txt 特判）

_WEIGHTS = {"physics": 0.5, "requirements": 0.2, "objective": 0.0, "robustness": 0.3}

_PROMPT_TMPL = """PROBLEM DESCRIPTION:
{background}

{description}

PROBLEM STEPS AND FUNCTION HEADERS:
{steps}

DEPENDENCIES:
Use only the following dependencies in your solution. Do not include these dependencies at the beginning of your code (they are already imported):
{dependencies}

RESPONSE GUIDELINES:
- Implement ALL step functions in a single ```python block, in the order given.
- Adhere exactly to the provided function headers (names, arguments, docstrings can be kept short).
- Later steps may call functions from earlier steps.
- Do NOT include dependency imports, example usage, or test code.
- Your response should contain ONLY the ```python code block.
"""


def _steps_block(steps: list[dict]) -> str:
    parts = []
    for i, s in enumerate(steps, 1):
        parts.append(f"## Step {i}\n"
                     f"Background:\n{s['step_background'].strip()}\n\n"
                     f"Description:\n{s['step_description_prompt'].strip()}\n\n"
                     f"Function header:\n{s['function_header'].strip()}\n")
    return "\n".join(parts)


def build_prompt(rec: dict) -> str:
    return _PROMPT_TMPL.format(
        background=rec["problem_background_main"].strip(),
        description=rec["problem_description_main"].strip(),
        steps=_steps_block(rec["sub_steps"]),
        dependencies=rec["required_dependencies"].strip(),
    ) + "\n"


def task_yaml(rec: dict, steps_meta: list[dict], digests: dict[str, str],
              prompt_sha: str, oracle_rel: str | None) -> dict:
    pid = rec["problem_id"]
    tid = f"scicode_p{int(pid):03d}"
    y: dict = {
        "id": tid,
        "registry_id": "scicode.physics",
        "domain": "coding",
        "task_type": "code_exec",
        "model_profile": "plain_llm",
        "assets_revision": ASSETS_REVISION,
        "environment_digest": "computed-at-runtime",
        "hidden": False,
        "allowed_tools": ["python"],
        "input": {
            "prompt_file": f"tasks/scicode.physics/{tid}.md",
            "prompt_sha256": prompt_sha,
            "assets": [{"path": f"data/scicode/physics/{n}", "digest": d}
                       for n, d in digests.items()],
        },
        "output_contract": ["solution_code"],
        "reference": {
            "source": "SciCode problems_{split}.jsonl + test_data.h5（官方数值期望）",
            "revision": ASSETS_REVISION,
            "problem_id": pid,
            "problem_name": rec["problem_name"],
            "split": "dev" if oracle_rel else "test",
            "n_steps": len(steps_meta),
            "n_cases": sum(s["n_cases"] for s in steps_meta),
            "uncertainty_note": "期望值为确定性数值（h5 锁定）；assert 语义来自数据集原始断言",
        },
        "grader": {
            "answer_format": "code",
            "exec_kind": "scicode_problem",
            "validity_gate": True,
            "dependencies": rec["required_dependencies"],
            "steps": steps_meta,           # 隐藏测试：模型只看 prompt_file
            "assert_semantics": "dataset_verbatim_np_allclose_vs_h5_target",
            "stability_layer": False,
            "determinism_runs": 2,
            "protocol_note": "整题一次生成（官方为逐步骤多轮）；分数不与官方榜单直接对比",
            "sandbox": {"banned": "network/process/ctypes/sys.path", "isolated_interpreter": True},
        },
        "scoring": {
            "weights": _WEIGHTS,
            "note": "physics=逐 case 通过率；requirements=判分 harness 可执行；"
                    "objective=N/A（数据集无边界输入测试）权重 0；robustness=两轮 pass 模式一致",
        },
        "limits": {"cpu": 4, "memory_gb": 8, "wall_clock_s": 900, "attempts": 3},
        "license_provenance": {
            "source": "scicode-bench/SciCode (Apache-2.0) + HF SciCode1/SciCode (apache-2.0)",
            "license": "Apache-2.0",
            "status": "confirmed-repo",
            "revision": ASSETS_REVISION,
            "mirror_allowed": True,
            "attribution": "SciCode: A Research Coding Benchmark Curated by Scientists, arXiv:2407.13168",
        },
    }
    if oracle_rel:
        y["grader"]["oracle_source"] = oracle_rel
    return y


def _read_no_translate(p: Path) -> str:
    if not p.exists():
        return ""
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    # json 往返后是 int；统一转 str 比较
    subset_ids = {str(x) for x in json.loads((DATA / "m2_subset_ids.json").read_text())}
    digests = {p.name: sha256_file(p) for p in sorted(DATA.glob("problems_*.jsonl"))}
    digests["test_data.h5"] = sha256_file(DATA / "test_data.h5")

    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    n, drift, stats = 0, [], {"test": 0, "dev": 0}
    for fn, split in (("problems_test.jsonl", "test"), ("problems_dev.jsonl", "dev")):
        for line in open(DATA / fn, encoding="utf-8"):
            rec = json.loads(line)
            if str(rec["problem_id"]) not in subset_ids:
                continue
            stats[split] += 1
            oracle_rel = None
            if split == "dev":
                gold = rec["general_solution"]
                gpath = GOLD_DIR / f"p{int(rec['problem_id']):03d}_gold.py"
                if not args.check:
                    gpath.write_text(gold, encoding="utf-8")
                oracle_rel = f"data/scicode/physics/gold_dev/p{int(rec['problem_id']):03d}_gold.py"
            steps_meta = []
            for s in rec["sub_steps"]:
                sid = str(s["step_number"])
                if sid in EXCLUDED_STEPS:
                    continue
                cases = list(s["test_cases"])
                steps_meta.append({"step_id": sid, "n_cases": len(cases),
                                   "test_cases": cases})
            prompt = build_prompt(rec)
            prompt_sha = hashlib.sha256(prompt.encode()).hexdigest()
            want = yaml.safe_dump(task_yaml(rec, steps_meta, digests, prompt_sha, oracle_rel),
                                  sort_keys=False, allow_unicode=True)
            tid = f"scicode_p{int(rec['problem_id']):03d}"
            ypath, ppath = TASKS_DIR / f"{tid}.yaml", TASKS_DIR / f"{tid}.md"
            if args.check:
                if _read_no_translate(ypath) != want or _read_no_translate(ppath) != prompt:
                    drift.append(tid)
            else:
                ypath.write_text(want, encoding="utf-8")
                ppath.write_text(prompt, encoding="utf-8")
            n += 1
    if args.check:
        if drift:
            print(f"[check] 不一致: {drift}")
            return 1
        print(f"[check] {n} 个任务与镜像一致 (test {stats['test']} / dev {stats['dev']})")
        return 0
    print(f"[gen] {n} tasks -> {TASKS_DIR} (test {stats['test']} / dev {stats['dev']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
