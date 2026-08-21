"""gen_tasks_mbppplus.py — 从官方 MBPP+ NoExtreme release 生成任务（∩sanitized 224 题）。

数据源（2026-08-21 裁定，同 humanevalplus）：
  官方 GitHub release evalplus/mbppplus_release v0.2.0 NoExtreme 变体
  （md5 85d8d7a406c0686e80353e676189bfee）——HF 卡片版结构不同且 humanevalplus 侧
  已实证转换缺陷，统一以官方 release 为权威源。

任务集 = MBPP+（378）∩ 本仓库 mbpp.sanitized test（257）= 224，按官方 task_id 连接。

同提示纯测试升级口径：
  提示 = 原 sanitized 题面（问题 + 原 test_list[0] 示例 + 函数名约定，
  与 mbpp.sanitized 逐字一致——分差纯粹来自测试加强）；
  判分 = 官方 assertion 断言逐条 case + base/plus 全量输入活体 GT 比对
  （canonical 判分时现场执行，双侧 _nb 归一，官方 out==exp/allclose 语义）；
  oracle = release canonical_solution（EvalPlus 重写版，38/224 与原 sanitized code 相同）。

生成物（幂等，--check 校验）：
  tasks/mbpp.sanitized_plus/mbpp_plus_<NNN>.yaml/.md
  data/mbpp/sanitized_plus/oracle/mbpp_plus_<NNN>.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

from .common import sha256_file
from .gen_tasks_mbpp import top_level_functions
from .gen_tasks_humanevalplus import _NORM_SRC

BENCH = Path(__file__).resolve().parent.parent
DATA = BENCH / "data/mbpp/sanitized_plus"
ORIG = BENCH / "data/mbpp/sanitized"
TASKS_DIR = BENCH / "tasks/mbpp.sanitized_plus"
ORACLE_DIR = DATA / "oracle"
ASSETS_REVISION = "mbppplus@release_v0.2.0-noextreme_20260821"


def split_assertions(assertion: str) -> tuple[list[str], list[str]]:
    """官方 assertion 块 -> (逐断言 case, 前置 import/setup 行)。

    MBPP+ 的 assertion 块自带 `import math` / `from math import inf` 等前置行
    （mbpp/98、/404 等）——须进 test_imports 置顶执行，只取 assert 行会 NameError。
    """
    lines = [ln.strip() for ln in assertion.splitlines() if ln.strip()]
    cases = [ln for ln in lines if ln.startswith("assert ")]
    imports = [ln for ln in lines if not ln.startswith("assert ")]
    return cases, imports


# GT 覆写：release canonical 在自家输入上崩溃的题（官方重写版缺陷，如实记录）：
#   106 add_lists: canonical `test_tup + tuple(test_list)` 对 list 型第二参数 TypeError；
#     原 sanitized code `tuple(list(test_tup) + test_list)` 全输入可用 -> 用原版兜底。
OVERRIDE_GT_ORIGINAL = {106}

# 排除（canonical 与原 sanitized code 均在官方输入上崩溃——数据集自身缺陷）：
#   252 convert: plus 输入为 '(1+2j)' 等字符串，cmath.polar(str) TypeError（两版同）；
#   124 angle_complex: plus 输入为 '0'/'1j' 等字符串，a+b=字符串拼接后 cmath.phase(str)
#     TypeError（两版同——官方把复数输入字符串化，与数字型 GT 系统性不兼容）。
EXCLUDED_WITH_REASON = {
    252: "官方数据缺陷：plus 输入为字符串，canonical 与原版 code 均 cmath.polar(str) TypeError",
    124: "官方数据缺陷：plus 输入为字符串，a+b 拼接后 cmath.phase(str) TypeError（两版同）",
}


def _lit(x) -> str:
    """安全字面量 repr：inf/nan 浮点 -> float('inf') 等构造式（裸 inf 是 NameError）。"""
    if isinstance(x, float):
        if x != x:
            return "float('nan')"
        if x == float("inf"):
            return "float('inf')"
        if x == float("-inf"):
            return "float('-inf')"
        return repr(x)
    if isinstance(x, list):
        return "[" + ", ".join(_lit(v) for v in x) + "]"
    return repr(x)


def build_plus_batch_case(entry_point: str, canonical_src: str,
                          inputs: list, atol) -> str:
    """活体 GT 批量比对 case（与 humanevalplus 同款，inf/nan 输入安全字面量化）。"""
    return (
        _NORM_SRC + "\n"
        f"_gt_ns = {{}}\n"
        f"exec({canonical_src!r}, _gt_ns)\n"
        f"_gt = _gt_ns[{entry_point!r}]\n"
        f"_inputs = {_lit(inputs)}\n"
        f"_atol = {atol!r}\n"
        f"for _inp in _inputs:\n"
        f"    _exp = _nb(_gt(*_inp))\n"
        f"    _got = _nb({entry_point}(*_inp))\n"
        f"    if not (_got == _exp):\n"
        f"        import numpy as _np\n"
        f"        try:\n"
        f"            assert _np.allclose(_got, _exp, rtol=1e-07, atol=_atol)\n"
        f"        except Exception:\n"
        f"            assert False, f'mismatch on {{_inp!r}}'\n"
    )


def build_prompt_md(text: str, example_test: str, fn_names: list[str]) -> str:
    fn_note = (f"\nUse exactly these top-level function name(s) in your solution: "
               f"{', '.join(fn_names)}.\n" if fn_names else "\n")
    return (text.rstrip() + "\n" + fn_note
            + "\nYour code should pass these tests:\n\n```\n"
            + example_test.strip() + "\n```\n")


def task_yaml(task_id: int, spec: dict, cases: list[str], imports: list[str],
              data_digest: str, orig_digest: str,
              oracle_digest: str, prompt_sha: str) -> dict:
    tid = f"mbpp_plus_{task_id:03d}"
    return {
        "id": tid,
        "registry_id": "mbpp.sanitized_plus",
        "domain": "coding",
        "task_type": "code_exec",
        "model_profile": "plain_llm",
        "assets_revision": ASSETS_REVISION,
        "environment_digest": "computed-at-runtime",
        "hidden": False,
        "allowed_tools": ["python"],
        "input": {
            "prompt_file": f"tasks/mbpp.sanitized_plus/{tid}.md",
            "prompt_sha256": prompt_sha,
            "assets": [
                {"path": "data/mbpp/sanitized_plus/MbppPlus-NoExtreme.jsonl",
                 "digest": data_digest},
                {"path": "data/mbpp/sanitized/mbpp_sanitized_test.jsonl",
                 "digest": orig_digest},
                {"path": f"data/mbpp/sanitized_plus/oracle/{tid}.py",
                 "digest": oracle_digest},
            ],
        },
        "output_contract": ["script"],
        "reference": {
            "source": "MBPP+ 官方 release v0.2.0 NoExtreme 变体（Apache-2.0；上游 CC BY 4.0）",
            "revision": ASSETS_REVISION,
            "mbpp_task_id": task_id,
            "entry_point": spec["entry_point"],
            "n_test_cases": len(cases),
            "test_note": "官方 assertion 逐条 + base/plus 全量输入活体 GT 比对（双侧 _nb 归一）",
            "uncertainty_note": "断言二值判定无比对不确定度；atol 由官方 release 逐题给出",
        },
        "grader": {
            "answer_format": "code",
            "exec_kind": "unit_tests_problem",
            "validity_gate": True,
            "entry_point": spec["entry_point"],
            "tests": cases,
            "test_imports": imports,
            "determinism_runs": 2,
            "sandbox": {"banned": "network/process/ctypes/sys.path",
                        "isolated_interpreter": True},
            "oracle_source": f"data/mbpp/sanitized_plus/oracle/{tid}.py",
        },
        "scoring": {
            "weights": {"physics": 0.5, "requirements": 0.2, "objective": 0.0,
                        "robustness": 0.3},
            "note": "objective=N/A 权重 0；robustness=两次执行确定性；summary 另报 pass@1",
        },
        "limits": {"cpu": 4, "memory_gb": 4, "wall_clock_s": 600, "attempts": 3},
        "license_provenance": {
            "source": "evalplus/mbppplus_release v0.2.0 NoExtreme（GitHub）",
            "license": "Apache-2.0（数据）/ CC BY 4.0（上游 MBPP 本体）",
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
    if hasattr(sys, "set_int_max_str_digits"):
        sys.set_int_max_str_digits(0)

    plus = {int(json.loads(l)["task_id"].split("/")[1]): json.loads(l) for l in
            (DATA / "MbppPlus-NoExtreme.jsonl").read_text(encoding="utf-8").splitlines()}
    orig_rows = [json.loads(l) for l in
                 (ORIG / "mbpp_sanitized_test.jsonl").read_text(encoding="utf-8").splitlines()]
    data_digest = sha256_file(DATA / "MbppPlus-NoExtreme.jsonl")
    orig_digest = sha256_file(ORIG / "mbpp_sanitized_test.jsonl")

    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    ORACLE_DIR.mkdir(parents=True, exist_ok=True)
    drift, n, skipped, excluded = [], 0, [], []
    for r in orig_rows:                        # 以原 sanitized 顺序为准
        tid_num = int(r["task_id"])
        if tid_num in EXCLUDED_WITH_REASON:
            excluded.append(tid_num)
            continue
        p = plus.get(tid_num)
        if p is None:
            skipped.append(tid_num)
            continue
        fns = top_level_functions(r["code"])   # 函数名约定取原 sanitized 参考
        prompt_md = build_prompt_md(r["prompt"], r["test_list"][0], fns)
        prompt_sha = hashlib.sha256(prompt_md.encode()).hexdigest()
        if tid_num in OVERRIDE_GT_ORIGINAL:
            oracle_src = r["code"] if r["code"].endswith("\n") else r["code"] + "\n"
        else:
            oracle_src = (p["canonical_solution"] if
                          p["canonical_solution"].endswith("\n") else
                          p["canonical_solution"] + "\n")
        oracle_digest = hashlib.sha256(oracle_src.encode()).hexdigest()
        cases, imports = split_assertions(p["assertion"])
        # evalplus 官方 harness 语义：math 全局可用（/120 assertion 用 math.isclose
        # 但 assertion 块与原 sanitized test_imports 均未声明）——统一前置 import math。
        if "import math" not in imports:
            imports = ["import math"] + imports
        inputs = list(p["base_input"]) + list(p["plus_input"])
        cases.append(build_plus_batch_case(p["entry_point"], oracle_src,
                                           inputs, p["atol"]))
        want = yaml.safe_dump(task_yaml(tid_num, p, cases, imports, data_digest,
                                        orig_digest, oracle_digest, prompt_sha),
                              sort_keys=False, allow_unicode=True, width=10**9)
        tid = f"mbpp_plus_{tid_num:03d}"
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
        print(f"[check] {n} 个任务与镜像一致（跳过 {len(skipped)} 不在 MBPP+；"
              f"排除 {len(excluded)} 数据缺陷）")
        return 0
    print(f"[gen] {n} tasks -> {TASKS_DIR}（活体 GT）| 跳过 {len(skipped)} | "
          f"排除 {excluded}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
