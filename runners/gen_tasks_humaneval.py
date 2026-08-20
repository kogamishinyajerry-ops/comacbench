"""gen_tasks_humaneval.py — 从镜像 HumanEval 生成任务 YAML + 题面 + oracle 解。

生成物（幂等，--check 校验）：
  tasks/humaneval.python/humaneval_<NNN>.yaml   164 个任务契约
  tasks/humaneval.python/humaneval_<NNN>.md     164 个题面（官方 prompt 原文 + 补全指令）
  data/humaneval/python/oracle/humaneval_<NNN>.py   oracle 解（prompt + canonical_solution）

隐藏测试拆分（AST，非正则）：
  官方 test 块 = `def check(candidate): <body>`。body 中：
    - 断言语句 -> 独立 case（community pass@1 的最小单元）；
    - 其余顶层语句（helper def / 赋值 / if 等）-> 逐 case 前置（语义不变）；
    - Name(candidate) 统一改写为 entry_point（AST 改名，零字符串误伤）；
  拆分失败（非常规结构）回退 = 整个 body 改名后单 case（官方整块语义）。
  unparse 丢注释不影响语义；cases 文本进 YAML 由判分器拼装执行。

协议（code_exec / unit_tests_problem）：
  gate         = 判分 harness 完整跑通（模型代码可导入）
  physics      = 隐藏断言逐条通过率（另报 pass@1 = physics==1.0 任务占比）
  robustness   = 两次执行逐 case 通过模式一致
"""

from __future__ import annotations

import argparse
import ast
import hashlib
from pathlib import Path

import yaml

from .common import sha256_file

BENCH = Path(__file__).resolve().parent.parent
DATA = BENCH / "data/humaneval/python"
TASKS_DIR = BENCH / "tasks/humaneval.python"
ORACLE_DIR = DATA / "oracle"
ASSETS_REVISION = "humaneval@openai-master+jsonl_20260821"

PROMPT_SUFFIX = (
    "\n# Complete the function above. Respond with the complete Python function "
    "(include the full function definition and any needed imports).\n"
)


class _Rename(ast.NodeTransformer):
    def __init__(self, param: str, entry: str) -> None:
        self.param, self.entry = param, entry

    def visit_Name(self, node: ast.Name) -> ast.Name:
        if node.id == self.param:
            node.id = self.entry
        return node


def split_tests(test_block: str, entry_point: str) -> tuple[list[str], str]:
    """官方 check 块 -> (逐断言 case 列表, 模式标签)。"""
    try:
        tree = ast.parse(test_block)
    except SyntaxError:
        return [test_block], "fallback_unparseable"
    check = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "check":
            check = node
            break
    if check is None or not check.args.args:
        return [test_block], "fallback_no_check"
    param = check.args.args[0].arg
    ren = _Rename(param, entry_point)

    helpers, asserts = [], []
    for stmt in check.body:
        (asserts if isinstance(stmt, ast.Assert) else helpers).append(stmt)
    if not asserts:
        whole = "\n".join(ast.unparse(ren.visit(s)) for s in check.body)
        return [whole], "fallback_no_assert"
    helper_src = "\n".join(ast.unparse(ren.visit(h)) for h in helpers)
    cases = [(helper_src + "\n" if helper_src else "") + ast.unparse(ren.visit(a))
             for a in asserts]
    mode = "split" if helpers else "split_pure"
    return cases, mode


def build_prompt_md(official_prompt: str) -> str:
    return official_prompt.rstrip() + "\n" + PROMPT_SUFFIX


def task_yaml(idx: int, spec: dict, cases: list[str], mode: str,
              data_digest: str, oracle_digest: str, prompt_sha: str) -> dict:
    tid = f"humaneval_{idx:03d}"
    return {
        "id": tid,
        "registry_id": "humaneval.python",
        "domain": "coding",
        "task_type": "code_exec",
        "model_profile": "plain_llm",
        "assets_revision": ASSETS_REVISION,
        "environment_digest": "computed-at-runtime",
        "hidden": False,
        "allowed_tools": ["python"],
        "input": {
            "prompt_file": f"tasks/humaneval.python/{tid}.md",
            "prompt_sha256": prompt_sha,
            "assets": [
                {"path": "data/humaneval/python/HumanEval.jsonl", "digest": data_digest},
                {"path": f"data/humaneval/python/oracle/{tid}.py",
                 "digest": oracle_digest},
            ],
        },
        "output_contract": ["function:" + spec["entry_point"]],
        "reference": {
            "source": "HumanEval 官方 test 块（MIT, openai/human-eval）",
            "revision": ASSETS_REVISION,
            "task_id": spec["task_id"],
            "entry_point": spec["entry_point"],
            "n_test_cases": len(cases),
            "uncertainty_note": "断言二值判定无比对不确定度；doctest 属公开提示面不计隐藏层",
        },
        "grader": {
            "answer_format": "code",
            "exec_kind": "unit_tests_problem",
            "validity_gate": True,
            "entry_point": spec["entry_point"],
            "tests": cases,
            "test_split_mode": mode,
            "test_imports": [],
            "determinism_runs": 2,
            "sandbox": {"banned": "network/process/ctypes/sys.path",
                        "isolated_interpreter": True},
            "oracle_source": f"data/humaneval/python/oracle/{tid}.py",
        },
        "scoring": {
            "weights": {"physics": 0.5, "requirements": 0.2, "objective": 0.0,
                        "robustness": 0.3},
            "note": "objective=N/A（无边界输入测试）权重 0；robustness=两次执行确定性；"
                    "summary 另报 pass@1（=官方口径）",
        },
        "limits": {"cpu": 4, "memory_gb": 4, "wall_clock_s": 120, "attempts": 3},
        "license_provenance": {
            "source": "openai/human-eval（HF openai/openai_humaneval 同源）",
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

    rows = [__import__("json").loads(l) for l in
            (DATA / "HumanEval.jsonl").read_text(encoding="utf-8").splitlines()]
    data_digest = sha256_file(DATA / "HumanEval.jsonl")
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    ORACLE_DIR.mkdir(parents=True, exist_ok=True)

    drift, n, modes = [], 0, {}
    for r in rows:
        idx = int(r["task_id"].split("/")[1])
        cases, mode = split_tests(r["test"], r["entry_point"])
        modes[mode] = modes.get(mode, 0) + 1
        prompt_md = build_prompt_md(r["prompt"])
        prompt_sha = hashlib.sha256(prompt_md.encode()).hexdigest()
        tid = f"humaneval_{idx:03d}"
        oracle_src = r["prompt"] + r["canonical_solution"] + "\n"
        oracle_digest = hashlib.sha256(oracle_src.encode()).hexdigest()
        want = yaml.safe_dump(task_yaml(idx, r, cases, mode, data_digest,
                                        oracle_digest, prompt_sha),
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
        print(f"[check] {n} 个任务与镜像一致（split 模式 {modes}）")
        return 0
    print(f"[gen] {n} tasks -> {TASKS_DIR} | oracle -> {ORACLE_DIR}（split 模式 {modes}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
