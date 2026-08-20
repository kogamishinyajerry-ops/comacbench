"""gen_tasks_mbpp.py — 从镜像 MBPP sanitized test 生成任务 YAML + 题面 + oracle 解。

生成物（幂等，--check 校验）：
  tasks/mbpp.sanitized/mbpp_<NNN>.yaml   257 个任务契约
  tasks/mbpp.sanitized/mbpp_<NNN>.md     257 个题面（官方口径：任务描述 + 示例测试）
  data/mbpp/sanitized/oracle/mbpp_<NNN>.py   oracle 解（官方参考 code 字段）

提示协议（官方 MBPP 评测口径）：
  模型可见 = 任务描述 + test_list[0] 作示例（官方 prompt 协议）；
  判分隐藏 = test_list 全量（含可见示例条）；
  函数名约定 = 参考实现的顶层 def 名（断言按官方代码调用该名，模型须同名交付），
  题面末尾显式给出函数名约定。
  test_imports（官方）置顶拼装；test_setup_code 在 sanitized test 为空（0/257）。

协议（code_exec / unit_tests_problem）：与 humaneval 同款。
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from pathlib import Path

import yaml

from .common import sha256_file

BENCH = Path(__file__).resolve().parent.parent
DATA = BENCH / "data/mbpp/sanitized"
TASKS_DIR = BENCH / "tasks/mbpp.sanitized"
ORACLE_DIR = DATA / "oracle"
ASSETS_REVISION = "mbpp@sanitized_test+hf_20260821"


def top_level_functions(code: str) -> list[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    return [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]


def build_prompt_md(text: str, example_test: str, fn_names: list[str]) -> str:
    fn_note = (f"\nUse exactly these top-level function name(s) in your solution: "
               f"{', '.join(fn_names)}.\n" if fn_names else "\n")
    return (text.rstrip() + "\n" + fn_note
            + "\nYour code should pass these tests:\n\n```\n"
            + example_test.strip() + "\n```\n")


def task_yaml(task_id: int, row: dict, data_digest: str, oracle_digest: str,
              prompt_sha: str) -> dict:
    tid = f"mbpp_{task_id:03d}"
    return {
        "id": tid,
        "registry_id": "mbpp.sanitized",
        "domain": "coding",
        "task_type": "code_exec",
        "model_profile": "plain_llm",
        "assets_revision": ASSETS_REVISION,
        "environment_digest": "computed-at-runtime",
        "hidden": False,
        "allowed_tools": ["python"],
        "input": {
            "prompt_file": f"tasks/mbpp.sanitized/{tid}.md",
            "prompt_sha256": prompt_sha,
            "assets": [
                {"path": "data/mbpp/sanitized/mbpp_sanitized_test.jsonl",
                 "digest": data_digest},
                {"path": f"data/mbpp/sanitized/oracle/{tid}.py",
                 "digest": oracle_digest},
            ],
        },
        "output_contract": ["script"],
        "reference": {
            "source": "MBPP sanitized test（CC BY 4.0, google-research-datasets/mbpp）",
            "revision": ASSETS_REVISION,
            "mbpp_task_id": task_id,
            "n_test_cases": len(row["test_list"]),
            "uncertainty_note": "断言二值判定无比对不确定度",
        },
        "grader": {
            "answer_format": "code",
            "exec_kind": "unit_tests_problem",
            "validity_gate": True,
            "tests": list(row["test_list"]),
            "test_imports": list(row.get("test_imports") or []),
            "determinism_runs": 2,
            "sandbox": {"banned": "network/process/ctypes/sys.path",
                        "isolated_interpreter": True},
            "oracle_source": f"data/mbpp/sanitized/oracle/{tid}.py",
        },
        "scoring": {
            "weights": {"physics": 0.5, "requirements": 0.2, "objective": 0.0,
                        "robustness": 0.3},
            "note": "objective=N/A（无边界输入测试）权重 0；robustness=两次执行确定性；"
                    "summary 另报 pass@1",
        },
        "limits": {"cpu": 4, "memory_gb": 4, "wall_clock_s": 120, "attempts": 3},
        "license_provenance": {
            "source": "google-research-datasets/mbpp（HF sanitized test split）",
            "license": "CC BY 4.0",
            "status": "confirmed-dataset",
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
            (DATA / "mbpp_sanitized_test.jsonl").read_text(encoding="utf-8").splitlines()]
    data_digest = sha256_file(DATA / "mbpp_sanitized_test.jsonl")
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    ORACLE_DIR.mkdir(parents=True, exist_ok=True)

    drift, n = [], 0
    for r in rows:
        task_id = int(r["task_id"])
        tid = f"mbpp_{task_id:03d}"
        oracle_src = r["code"] if r["code"].endswith("\n") else r["code"] + "\n"
        oracle_digest = hashlib.sha256(oracle_src.encode()).hexdigest()
        fns = top_level_functions(r["code"])
        prompt_md = build_prompt_md(r["prompt"], r["test_list"][0], fns)
        prompt_sha = hashlib.sha256(prompt_md.encode()).hexdigest()
        want = yaml.safe_dump(task_yaml(task_id, r, data_digest, oracle_digest,
                                        prompt_sha),
                              sort_keys=False, allow_unicode=True)
        ypath, ppath = TASKS_DIR / f"{tid}.yaml", TASKS_DIR / f"{tid}.md"
        opath = ORACLE_DIR / f"{tid}.py"
        if args.check:
            if (_read_no_translate(ypath) != want
                    or _read_no_translate(ppath) != prompt_md
                    or _read_no_translate(opath) != oracle_src):
                drift.append(tid)
        else:
            ypath.write_text(want, encoding="utf-8")
            ppath.write_text(prompt_md, encoding="utf-8")
            opath.write_text(oracle_src, encoding="utf-8")
        n += 1
    if args.check:
        if drift:
            print(f"[check] 不一致: {drift[:5]}... 共 {len(drift)}")
            return 1
        print(f"[check] {n} 个任务与镜像一致")
        return 0
    print(f"[gen] {n} tasks -> {TASKS_DIR} | oracle -> {ORACLE_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
