"""common.py — adapter 公共基础设施（五类 adapter 共用，不绑定具体基准）。

职责（对应 adapters/README.md「通用约定」）：
  1. 读取并校验任务 YAML 必填字段；
  2. 计算 environment_digest（dev 终端：python 版本 + 平台 + runner 代码 + 数据指纹）；
  3. 校验 assets_revision 锁定的数据文件（sha256）；
  4. 构造标准 result.json；
  5. 写 run_manifest.json（可离线重跑：seed / provider / 摘要 / 重跑命令全落盘）。

失败模式（adapters/README.md 通用表）在此统一定义为常量。
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import yaml

# ---- 通用失败模式代码（adapters/README.md） ----
FM_MISSING_OUTPUT = "missing_output"      # output_contract 产物缺失        -> score=0
FM_ENV_MISMATCH = "env_mismatch"          # environment_digest 不匹配       -> 作废重跑（不计分）
FM_TIMEOUT = "timeout"                    # 超 limits                       -> score=0
FM_OOM = "oom"                            # 超 limits                       -> score=0
FM_TOOL_VIOLATION = "tool_violation"      # 越出 allowed_tools              -> score=0
FM_CRASH = "crash"                        # 运行器/判分器自身故障           -> 作废并告警（不计分）

# 作废类（任务不计分，也不计入模型失败——是 harness 自身问题）
VOIDED_FAILURE_MODES = {FM_ENV_MISMATCH, FM_CRASH}

REQUIRED_TASK_FIELDS = [
    "id", "registry_id", "domain", "task_type", "model_profile",
    "assets_revision", "allowed_tools", "input", "output_contract",
    "grader", "scoring", "limits", "license_provenance",
]

BENCH_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------- digests

def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def environment_digest(extra_paths: list[str | Path] | None = None) -> str:
    """dev 终端环境摘要：python + 平台 + runner 源码 + 显式追加文件（如数据 JSON）。

    无容器镜像的 dev 层用该复合摘要代替；任一组成变化 => 新评测周期。
    """
    parts: list[str] = [
        f"python={sys.version.split()[0]}",
        f"platform={platform.platform()}",
        f"machine={platform.machine()}",
    ]
    runners_dir = Path(__file__).resolve().parent
    for py in sorted(runners_dir.glob("*.py")):
        parts.append(f"runner:{py.name}={sha256_file(py)[:16]}")
    for p in extra_paths or []:
        p = Path(p)
        if p.exists():
            parts.append(f"file:{p.name}={sha256_file(p)[:16]}")
        else:
            parts.append(f"file:{p.name}=MISSING")
    return "sha256:" + sha256_bytes("\n".join(parts).encode())


# ---------------------------------------------------------------- task YAML

class TaskSpec:
    """已校验的任务契约。"""

    def __init__(self, spec: dict[str, Any], yaml_path: Path):
        self.spec = spec
        self.yaml_path = yaml_path
        missing = [f for f in REQUIRED_TASK_FIELDS if f not in spec]
        if missing:
            raise ValueError(f"{yaml_path}: 缺必填字段 {missing}")
        if Path(spec["id"]).name != yaml_path.stem:
            raise ValueError(
                f"{yaml_path}: 文件名必须等于 id（得到 id={spec['id']}）")

    def __getitem__(self, k: str) -> Any:
        return self.spec[k]

    def get(self, k: str, default: Any = None) -> Any:
        return self.spec.get(k, default)

    @property
    def id(self) -> str:
        return self.spec["id"]


def load_tasks(tasks_dir: str | Path) -> list[TaskSpec]:
    tasks = [TaskSpec(yaml.safe_load(p.read_text(encoding="utf-8")), p)
             for p in sorted(Path(tasks_dir).glob("*.yaml"))]
    if not tasks:
        raise FileNotFoundError(f"{tasks_dir} 下没有任务 YAML")
    return tasks


def verify_asset(path: str | Path, expect_sha256: str, what: str) -> None:
    got = sha256_file(path)
    if got != expect_sha256:
        raise RuntimeError(
            f"资产校验失败 [{what}]: {path}\n  期望 sha256={expect_sha256}\n  实际 sha256={got}"
            f"\n  => assets_revision 已漂移，按新评测周期处理（scoring/README.md §7）")


# ---------------------------------------------------------------- result.json

DEFAULT_SUBSCORES = ["physics", "requirements", "objective", "robustness"]


def build_result(
    *,
    task: TaskSpec,
    adapter: str,
    validity_gate: int,
    gate_failures: list[str],
    subscores: dict[str, float | None],
    score: float,
    artifacts: dict[str, str],
    timings: dict[str, float],
    env_digest: str,
    logs: list[str],
    failure_mode: str | None = None,
    applicability: dict[str, str] | None = None,
) -> dict[str, Any]:
    """标准 result.json（字段契约见 adapters/README.md）。"""
    res: dict[str, Any] = {
        "task_id": task.id,
        "registry_id": task["registry_id"],
        "adapter": adapter,
        "validity_gate": validity_gate,
        "gate_failures": gate_failures,
        "failure_mode": failure_mode,          # null=正常计分；VOIDED 类表示任务作废
        "subscores": {k: subscores.get(k) for k in DEFAULT_SUBSCORES},
        "subscore_applicability": applicability or {},
        "score": score,
        "artifacts": artifacts,
        "timings": {k: round(v, 3) for k, v in timings.items()},
        "environment_digest": env_digest,
        "assets_revision": task["assets_revision"],
        "logs": logs,
    }
    return res


def aggregate_score(
    subscores: dict[str, float], weights: dict[str, float], validity_gate: int,
) -> float:
    """Score = ValidityGate × Σ w_i·S_i（scoring/README.md §2；权重来自任务 YAML）。"""
    total = sum(weights.get(k, 0.0) * float(subscores.get(k) or 0.0)
                for k in DEFAULT_SUBSCORES)
    return round(validity_gate * total, 6)


# ---------------------------------------------------------------- run manifest

def write_run_manifest(
    out_dir: str | Path,
    *,
    registry_id: str,
    adapter: str,
    provider: str,
    seed: int,
    tasks_dir: Path,
    env_digest: str,
    assets: dict[str, str],
    rerun_command: str,
    extra: dict[str, Any] | None = None,
    task_ids: list[str] | None = None,
) -> Path:
    manifest = {
        "registry_id": registry_id,
        "adapter": adapter,
        "provider": provider,
        "seed": seed,
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "environment_digest": env_digest,
        "environment_note": "dev 终端（外网开发机，OpenFOAM+FoamAgent，无 Fluent/StarCCM）",
        "assets": assets,                     # {label: sha256}
        "tasks_dir": str(tasks_dir),
        "n_tasks": len(task_ids) if task_ids is not None else len(list(Path(tasks_dir).glob('*.yaml'))),
        "rerun_command": rerun_command,
        "git_commit": _git_commit(),
        "extra": extra or {},
    }
    path = Path(out_dir) / "run_manifest.json"
    write_json_atomic(path, manifest)
    return path


def write_json_atomic(path: Path, value: Any) -> None:
    """Publish a complete JSON file; interruption cannot leave a partial result."""
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _git_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=BENCH_ROOT,
            capture_output=True, text=True, timeout=10,
        )
        return out.stdout.strip() or "unknown(no-git)"
    except Exception:
        return "unknown(no-git)"


# ---------------------------------------------------------------- reporting

def gate_distribution(results: list[dict[str, Any]]) -> dict[str, Any]:
    """gate 类分布（报告必须给 gate 失败率与原因分布，不给裸均分——scoring/README.md §2）。"""
    n = len(results)
    passed = sum(1 for r in results if r["validity_gate"] == 1)
    reasons: dict[str, int] = {}
    for r in results:
        for g in r["gate_failures"]:
            reasons[g] = reasons.get(g, 0) + 1
    voided = sum(1 for r in results if r.get("failure_mode") in VOIDED_FAILURE_MODES)
    return {
        "n_tasks": n,
        "gate_passed": passed,
        "gate_failed": n - passed - voided,
        "voided": voided,
        "gate_failure_reasons": dict(sorted(reasons.items(), key=lambda kv: -kv[1])),
    }
