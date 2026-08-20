"""providers.py — 模型调用层（qa 类 adapter 的被测对象入口）。

设计（与「求解器无关」原则同构）：adapter 不感知具体模型 CLI/SDK，
只通过 provider 名字取答案；真实 API 到位后增加 provider 即可，不改 adapter。

当前 provider：
  stub          确定性伪答案（sha256(seed|task_id|question) -> 1..4）。
                离线、无 API、可精确复现——用于判分管线冒烟与基线落盘。
  oracle        返回任务参考答案。仅用于判分器自检（oracle 必须 100 分，
                否则判分器有 bug），不得作为基线报告。
  openai_compat 通用 OpenAI 兼容 /chat/completions。读环境变量：
                BM_API_BASE / BM_API_KEY / BM_MODEL。
  glm           GLM（bigmodel.cn，OpenAI 兼容）。key 读 GLM_API_KEY，
                base 读 GLM_BASE_URL（缺省 coding 端点），模型缺省 glm-4.6。
  minimax       MiniMax（api.minimaxi.com/v1，OpenAI 兼容）。key 依次读
                MINIMAX_M3_API_KEY / MINIMAX_API_KEY，模型缺省 MiniMax-M3。
  ml_superwing  superwing ML 正例基线（RF，几何+工况→系数），非被测 LLM。
  ml_hilift     hilift ML 正例基线（RF 同款；保留集由任务 YAML 反推，见
                _train_hilift_ml docstring）。

推理模型差异（2026-08-19 实测）：
  GLM-4.6   最终答案在 message.content，思考在 message.reasoning_content；
  MiniMax-M3 思考内联在 message.content 的 <think>…</think> 标签内。
  => parse_answer 统一先剥 <think> 块再 strict->tolerant 解析。
密钥只从环境变量读，绝不落盘（macOS 下由调用方从 Keychain 注入）。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.request
from pathlib import Path
from typing import Any

from .common import TaskSpec


class ProviderError(RuntimeError):
    pass


# 命名 provider 预设（均 OpenAI 兼容 chat/completions）
#   extra_body:  并入请求体（如 GLM 思考开关）
#   escalate:    解析失败时的最后手段请求体补丁（关思考保答案输出）
PROVIDER_PRESETS: dict[str, dict[str, Any]] = {
    "glm": {
        "base_env": "GLM_BASE_URL",
        "base_default": "https://open.bigmodel.cn/api/coding/paas/v4",
        "key_envs": ["GLM_API_KEY"],
        "model_default": "glm-4.6",
        "keychain_hint": "security find-generic-password -s glm-api-key -w",
        "extra_body": {"thinking": {"type": "enabled"}},
        "escalate": {"thinking": {"type": "disabled"}, "max_tokens": 512},
    },
    "minimax": {
        "base_env": None,
        "base_default": "https://api.minimaxi.com/v1",
        "key_envs": ["MINIMAX_M3_API_KEY", "MINIMAX_API_KEY"],
        "model_default": "MiniMax-M3",
        "keychain_hint": "security find-generic-password -s minimax-m3-api-key -w",
        # M3 思考实测可超 16k token（q001 默认 16384 被耗尽、答案被截空）-> 提到 32768
        "extra_body": {"max_tokens": 32768},
        # thinking 开关在 MiniMax 端点同样有效（实测 disabled 后直接输出答案）
        "escalate": {"thinking": {"type": "disabled"}, "max_tokens": 512},
    },
}

_THINK_RE = re.compile(r"<think>.*?</think>", re.S)

# 任务无关的中性系统提示（free_text 任务用；具体格式要求在题面文件里）
_SYSTEM_PROMPT_FREE_TEXT = (
    "You are an expert aerospace engineering researcher.\n"
    "Answer strictly in the format requested by the user prompt."
)

_SYSTEM_PROMPT_CODE = (
    "You are an expert scientific programmer.\n"
    "Write complete, correct, runnable Python code for the given task.\n"
    "Respond with a single ```python code block and nothing else."
)

_SYSTEM_PROMPT_JSON = (
    "You are an expert aerospace engineer.\n"
    "Respond with a single valid JSON object and nothing else.\n"
    "Do not wrap it in code fences or add commentary."
)

_CODE_FENCE_RE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.S)


def extract_code_block(raw: str) -> str | None:
    """剥思考后取第一个 ```python 围栏块；无围栏时取非空全文。"""
    s = strip_think(raw)
    m = _CODE_FENCE_RE.search(s)
    if m:
        return m.group(1).strip()
    return s.strip() or None


def extract_json(raw: str) -> dict | None:
    """剥思考后取首个 JSON 对象（直接或去围栏）。"""
    import json as _json
    s = strip_think(raw)
    s = re.sub(r"```(?:json)?\s*", "", s).strip()
    m = re.search(r"\{.*\}", s, re.S)
    if m:
        try:
            return _json.loads(m.group(0))
        except Exception:
            pass
    try:
        return _json.loads(s)
    except Exception:
        return None


def strip_think(raw: str) -> str:
    """剥离内联思考块（MiniMax-M3 风格 <think>…</think>）。"""
    return _THINK_RE.sub("", raw or "").strip()


def parse_answer(raw: str) -> int | None:
    """解析 MCQ 输出 -> 1..4（先剥 <think>，再 strict->tolerant，同上游 llms.py）。"""
    s = strip_think(raw)
    if s in {"1", "2", "3", "4"}:
        return int(s)
    m = re.search(r"([1-4])", s)
    return int(m.group(1)) if m else None


# ---------------------------------------------------------------- stub

def _stub_answer(task: TaskSpec, seed: int, question: str) -> int:
    h = hashlib.sha256(
        f"{seed}|{task.id}|{question[:64]}".encode()).hexdigest()
    return int(h, 16) % 4 + 1


def _stub_free_text(task: TaskSpec, seed: int, prompt: str) -> str:
    """确定性 free_text stub：取题面首 8 词充当答案，结构字段齐全。
    只为打通管线（结构解析/gate/三层判分），答案本身无意义。"""
    words = " ".join(prompt.split())[:120].split()[:8]
    return f"ANSWER: {' '.join(words)}\nBASIS: report\nCITATION: [1]"


# ---------------------------------------------------------------- chat/completions

_SYSTEM_PROMPT = (
    "You are an expert computational fluid dynamics researcher.\n"
    "For each multiple-choice question, read the question and its four options,\n"
    "then respond with only the number (1, 2, 3, or 4) corresponding to the correct answer."
)


def _chat_completions_answer(
    prompt: str, max_attempts: int, *, base: str, key: str, model: str,
    label: str, extra_body: dict[str, Any] | None = None,
    escalate_body: dict[str, Any] | None = None,
    expect: str = "mcq",
) -> dict[str, Any]:
    system = {"mcq": _SYSTEM_PROMPT,
              "free_text": _SYSTEM_PROMPT_FREE_TEXT,
              "code": _SYSTEM_PROMPT_CODE,
              "json": _SYSTEM_PROMPT_JSON}[expect]

    def make_body(patch: dict[str, Any] | None) -> bytes:
        req_body: dict[str, Any] = {
            "model": model,
            "temperature": 0.0,
            "max_tokens": 16384,   # 思考 token 计入 completion；2048 实测会被长思考耗尽
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        }
        req_body.update(extra_body or {})
        req_body.update(patch or {})
        return json.dumps(req_body).encode()

    def accept(raw: str) -> int | None | str:
        """mcq: 选项号；code: python 围栏块；json: dict；其余: 剥思考原文。"""
        if expect == "mcq":
            return parse_answer(raw)
        if expect == "code":
            return extract_code_block(raw)
        if expect == "json":
            return extract_json(raw)
        return strip_think(raw) or None

    last_err = None
    use_escalated = False   # 解析失败后粘性升级（关思考保答案输出，避免浪费整段思考配额）
    for attempt in range(1, max_attempts + 1):
        is_final = attempt == max_attempts and escalate_body is not None
        use_esc = is_final or use_escalated
        try:
            req = urllib.request.Request(
                base.rstrip("/") + "/chat/completions", data=make_body(
                    escalate_body if use_esc else None),
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {key}"})
            with urllib.request.urlopen(req, timeout=600) as resp:
                data = json.loads(resp.read())
            err = data.get("error")
            if not err:
                br = data.get("base_resp") or {}
                if br.get("status_code", 0) not in (0, None):
                    err = br
            if err:
                raise RuntimeError(f"API 报错: {err}")
            ch = data["choices"][0]
            msg = ch["message"]
            raw = msg.get("content") or ""
            ans = accept(raw)
            if ans is not None:
                return {"answer": ans, "raw": raw, "attempts": attempt,
                        "meta": {"provider": label, "model": data.get("model", model),
                                 "finish_reason": ch.get("finish_reason"),
                                 "escalated": use_esc}}
            last_err = f"第 {attempt} 次输出无法解析: {raw!r:.160}"
            if escalate_body:
                use_escalated = True
        except Exception as e:  # noqa: BLE001 — 重试语义需捕获全部传输层错误
            last_err = f"第 {attempt} 次调用失败: {e}"
        time.sleep(min(5.0 * attempt, 20.0))
    raise ProviderError(f"{label} 重试用尽（{max_attempts}）: {last_err}")


def _preset_answer(provider: str, prompt: str, max_attempts: int,
                   model: str | None, expect: str) -> dict[str, Any]:
    p = PROVIDER_PRESETS[provider]
    base = os.environ.get(p["base_env"]) if p["base_env"] else None
    base = base or p["base_default"]
    key = next((os.environ[e] for e in p["key_envs"] if os.environ.get(e)), None)
    if not key:
        raise ProviderError(
            f"{provider} 未配置: 缺环境变量 {p['key_envs']}。"
            f"（本机 Keychain 取法: {p['keychain_hint']}，注入后重跑，密钥不落盘）")
    model = model or p["model_default"]
    return _chat_completions_answer(prompt, max_attempts, base=base, key=key,
                                    model=model, label=provider,
                                    extra_body=p.get("extra_body") or None,
                                    escalate_body=p.get("escalate") or None,
                                    expect=expect)


def _oracle_free_text(task: TaskSpec) -> str:
    """oracle 的 free_text 输出：可答题给参考答案+完整结构；不可答题规范拒答。"""
    ref = task["reference"]
    needed = ref.get("needed_citations") or []
    if ref.get("refusal_expected"):
        avail = ref.get("n_contexts", 1)
        cite = f"[1{',2' if avail > 1 else ''}]"
        return f"ANSWER: REFUSED\nBASIS: report\nCITATION: {cite}"
    return (f"ANSWER: {str(ref['reference_answer']).strip()}\n"
            f"BASIS: report\nCITATION: [{', '.join(str(c) for c in needed)}]")


# ---------------------------------------------------------------- ml_baseline

_ML_MODELS: dict[str, Any] = {}   # 惰性全局缓存（首次调用训练一次）


def _train_superwing_ml() -> dict[str, Any]:
    """superwing ML 基线：随机森林回归（几何参数 + 工况 → cl/cd/cm）。

    训练集 = train.parquet 全量（25985 样本）；特征 = configs.dat 38 几何参数 + aoa + mach。
    作为 field_prediction 的正例参照（LLM 近零 physics 的对照），非被测 LLM。
    """
    import csv as _csv
    import numpy as _np
    import pandas as _pd
    from sklearn.ensemble import RandomForestRegressor

    bench = Path(__file__).resolve().parent.parent
    d = bench / "data/superwing/coeff_lite"
    geo_names = (["SA", "DA", "DA_kink", "AR", "TR", "kink", "rootadj",
                  "rtcs_0", "rtcs_1", "rtcs_2", "cambers_0", "cambers_1", "cambers_2",
                  "twists_0", "twists_1", "twists_2", "twists_3"]
                 + [f"Uroot_{i}" for i in range(10)]
                 + [f"Utip_{i}" for i in range(10)]
                 + ["tcroot"])
    shapes: dict[int, list[float]] = {}
    for line in (d / "configs.dat").read_text().splitlines():
        if line.startswith(("VARIABLES", "ZONE", "TITLE")) or not line.strip():
            continue
        vals = line.split()
        shapes[int(float(vals[0]))] = [float(v) for v in vals[1:39]]
    tr = _pd.read_parquet(d / "train.parquet")
    X = _np.array([shapes[int(s)] + [a, m] for s, a, m in
                   zip(tr["wing_shape_idx"], tr["aoa"], tr["mach"])])
    models = {}
    for c in ("cl_solver", "cd_solver", "cm_solver"):
        m = RandomForestRegressor(n_estimators=100, random_state=0, n_jobs=-1)
        m.fit(X, tr[c].values)
        models[c] = m
    return {"models": models, "shapes": shapes, "geo_names": geo_names}


def _ml_superwing_predict(task: TaskSpec) -> dict[str, float]:
    if "superwing" not in _ML_MODELS:
        _ML_MODELS["superwing"] = _train_superwing_ml()
    ml = _ML_MODELS["superwing"]
    ref = task["reference"]
    feat = ml["shapes"][int(ref["wing_shape_idx"])] + [float(ref["aoa"]), float(ref["mach"])]
    import numpy as _np
    x = _np.array([feat])
    return {"cl": float(ml["models"]["cl_solver"].predict(x)[0]),
            "cd": float(ml["models"]["cd_solver"].predict(x)[0]),
            "cm": float(ml["models"]["cm_solver"].predict(x)[0])}


def _train_hilift_ml(tasks_dir: Path) -> dict[str, Any]:
    """hilift ML 基线：随机森林回归（8 高升力几何参数 + AoA → cl/cd/cm）。

    与 ml_superwing 同款（RF 100 trees, seed=0），作 field_prediction 正例参照。
    划分纪律（与生成器 gen_tasks_hilift.py 同口径）：
      - 保留集 = 生成器 RNG（seed 20260819）抽的 36 构型，整体剔除出训练
        （注意：70 道 ge 题只实际覆盖其中 32 个——其余 4 个未被抽样但同样保留）；
      - it 组（内插）的 (构型, 迎角) 测试行剔除，构型其余迎角保留；
      - 双保险：从任务 YAML 反推 ge 构型集，必须 ⊆ RNG 保留集，否则报错防漂移；
      训练行数 = 1800 - 36×10 - 30 = 1410（144 训练构型）。
    """
    import numpy as _np
    import pandas as _pd
    import yaml as _yaml
    from sklearn.ensemble import RandomForestRegressor

    bench = Path(__file__).resolve().parent.parent
    d = bench / "data/hilift/lite"
    geo_params = ["IB_Flap_Deflection", "OB_Flap_Deflection",
                  "IB_Flap_Gap_Multiplier", "OB_Flap_Gap_Multiplier",
                  "IB_Slat_Deflection", "OB_Slat_Deflection",
                  "IB_Slat_Gap_Multiplier", "OB_Slat_Gap_Multiplier"]

    fm = _pd.read_csv(d / "force_mom_all.csv")
    geo = _pd.read_csv(d / "geo_values_all.csv").set_index("GeoID")
    # 生成器同款保留集（gen_tasks_hilift.py: rng=default_rng(20260819), size=36）
    holdout = set(_np.random.default_rng(20260819).choice(
        sorted(fm["GeoID"].unique()), size=36, replace=False).tolist())

    # 双保险：任务 YAML 反推的 ge 构型必须 ⊆ 保留集（生成器换 seed 时立刻暴露）
    ge_in_tasks: set[str] = set()
    it_rows: set[tuple[str, float]] = set()
    for yp in sorted(tasks_dir.glob("*.yaml")):
        ref = (_yaml.safe_load(yp.read_text(encoding="utf-8")) or {}).get("reference") or {}
        gid, aoa = ref.get("wing_shape_idx"), ref.get("aoa")
        if gid is None or aoa is None:
            continue
        if ref.get("split_group") == "ge":
            ge_in_tasks.add(gid)
        elif ref.get("split_group") == "it":
            it_rows.add((gid, round(float(aoa), 6)))
    if not ge_in_tasks <= holdout:
        raise ProviderError(
            f"hilift 划分漂移: 任务 YAML 的 ge 构型 {sorted(ge_in_tasks - holdout)} "
            "不在 RNG 保留集内——生成器与 ML 基线口径需人工复核")
    tr = fm[~fm["GeoID"].isin(holdout)]
    tr = tr[~tr.apply(lambda r: (r["GeoID"], round(float(r["AoA"]), 6)) in it_rows, axis=1)]
    X = _np.array([[float(v) for v in geo.loc[g, geo_params]] + [float(a)]
                   for g, a in zip(tr["GeoID"], tr["AoA"])])
    models = {}
    for c in ("cl", "cd", "cm"):
        m = RandomForestRegressor(n_estimators=100, random_state=0, n_jobs=-1)
        m.fit(X, tr[c].values)
        models[c] = m
    return {"models": models, "geo": geo, "geo_params": geo_params,
            "n_train": len(tr), "n_holdout": len(holdout)}


def _ml_hilift_predict(task: TaskSpec) -> dict[str, float]:
    bench = Path(__file__).resolve().parent.parent
    tasks_dir = (bench / Path(task["input"]["prompt_file"]).parent).resolve()
    if "hilift" not in _ML_MODELS:
        _ML_MODELS["hilift"] = _train_hilift_ml(tasks_dir)
    ml = _ML_MODELS["hilift"]
    ref = task["reference"]
    import numpy as _np
    row = ml["geo"].loc[ref["wing_shape_idx"], ml["geo_params"]]
    x = _np.array([[float(v) for v in row] + [float(ref["aoa"])]])
    return {c: float(ml["models"][c].predict(x)[0]) for c in ("cl", "cd", "cm")}


# ---------------------------------------------------------------- entry

def get_answer(
    provider: str, task: TaskSpec, prompt: str, *, seed: int, max_attempts: int,
    model: str | None = None, expect: str = "mcq",
) -> dict[str, Any]:
    """返回 {answer, raw, attempts, meta}；无法给出 answer 时抛错。

    expect="mcq"       answer=int(1..4)；
    expect="free_text" answer=str（剥思考后的原文，结构解析由 grader 负责）。
    """
    if provider == "stub":
        if expect == "code":
            return {"answer": "pass\n", "raw": "pass", "attempts": 1,
                    "meta": {"provider": "stub", "seed": seed}}
        if expect == "json":
            # 确定性 stub：训练集均值（由 grader 侧 or task reference 提供更准确）
            return {"answer": {"cl": 0.3, "cd": 0.03, "cm": 0.0},
                    "raw": '{"cl": 0.3, "cd": 0.03, "cm": 0.0}',
                    "attempts": 1, "meta": {"provider": "stub", "seed": seed}}
        if expect == "free_text":
            raw = _stub_free_text(task, seed, prompt)
            return {"answer": raw, "raw": raw, "attempts": 1,
                    "meta": {"provider": "stub", "seed": seed}}
        a = _stub_answer(task, seed, prompt)
        return {"answer": a, "raw": str(a), "attempts": 1,
                "meta": {"provider": "stub", "seed": seed}}
    if provider == "ml_superwing":
        if expect != "json":
            raise ProviderError("ml_superwing 仅支持 expect=json（field_prediction）")
        pred = _ml_superwing_predict(task)
        return {"answer": pred, "raw": json.dumps(pred), "attempts": 1,
                "meta": {"provider": "ml_superwing",
                         "model": "RandomForestRegressor(100 trees, seed=0)"}}
    if provider == "ml_hilift":
        if expect != "json":
            raise ProviderError("ml_hilift 仅支持 expect=json（field_prediction）")
        pred = _ml_hilift_predict(task)
        return {"answer": pred, "raw": json.dumps(pred), "attempts": 1,
                "meta": {"provider": "ml_hilift",
                         "model": "RandomForestRegressor(100 trees, seed=0, "
                                  "split=任务YAML反推：ge构型整体保留+it测试行剔除)"}}
    if provider == "oracle":
        if expect == "code":
            raise ProviderError("oracle code 由 adapter 从 grader.oracle_source 读取，不走 provider")
        if expect == "json":
            ref = task["reference"]["true"]
            raw = json.dumps(ref, ensure_ascii=False)
            return {"answer": dict(ref), "raw": raw, "attempts": 1,
                    "meta": {"provider": "oracle"}}
        if expect == "free_text":
            raw = _oracle_free_text(task)
            return {"answer": raw, "raw": raw, "attempts": 1,
                    "meta": {"provider": "oracle"}}
        ref = task["reference"]["correct_option_index"]
        return {"answer": int(ref), "raw": str(ref), "attempts": 1,
                "meta": {"provider": "oracle"}}
    if provider in PROVIDER_PRESETS:
        return _preset_answer(provider, prompt, max_attempts, model, expect)
    if provider == "openai_compat":
        base = os.environ.get("BM_API_BASE")
        key = os.environ.get("BM_API_KEY")
        model = model or os.environ.get("BM_MODEL")
        missing = [n for n, v in (("BM_API_BASE", base), ("BM_API_KEY", key),
                                  ("BM_MODEL", model)) if not v]
        if missing:
            raise ProviderError(f"openai_compat 未配置: 缺 {missing}")
        return _chat_completions_answer(prompt, max_attempts, base=base, key=key,
                                        model=model, label="openai_compat",
                                        expect=expect)
    raise ProviderError(f"未知 provider: {provider}")
