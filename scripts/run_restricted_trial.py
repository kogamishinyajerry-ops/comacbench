"""Maintainer launcher for one existing-configuration DSH public development trial.

No credential/config dump, installation, model selection or automatic retry. Each
invocation requires a new output directory; --preflight stops before model use.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from comacbench import workbench as wb

DISABLED = ["agent-instructions", "skill-filesystem", "tool-skill", "session-title-llm",
            "tool-bash", "tool-pwsh", "tool-jobs", "tool-fs", "tool-fs-search", "tool-web",
            "tool-subagent", "tool-subagent-fork", "tool-subagent-control", "tool-list-agents",
            "tool-workflow", "tool-todo", "tool-goal", "tool-ralph", "tool-plugin-manager"]
PROMPT = ("完成工具绑定的公开固定梁工作包。首先调用 workbench 的 observe，按其公开合同、当前输入和错误反馈操作。"
          "根据实际结果形成并检查 review，完成后提交。只使用该工具；失败保留并如实说明。"
          "这是同题已公开的一次受限开发复测，不是未见题、隐藏测试或泛化成绩。")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--dsh", type=Path, required=True)
    parser.add_argument("--dsh-root", type=Path, required=True)
    parser.add_argument("--ccx", type=Path, required=True)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    public = out / "public-workspace"; public.mkdir()
    audit = out / "audit"  # created exclusively by the host plugin
    session = out / "session"
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)
    if status and not args.preflight:
        raise RuntimeError("Final-source trial requires a clean committed source tree")
    started = datetime.now(timezone.utc).isoformat()
    observation = wb.start(session, wb.read_json(ROOT / "examples/workbench/structures-change-v1.json"),
        {"name": "DSH glm-4.7 restricted public repeat" if not args.preflight else "Infrastructure preflight; no model",
         "revision": revision, "kind": "user_agent" if not args.preflight else "negative_control"}, ccx_path=str(args.ccx.resolve()))
    (out / "maintainer-start.json").write_text(json.dumps(observation, ensure_ascii=False, indent=2) + '\n')
    # json syntax is a YAML subset; expression-valued headless config below is
    # inherited from the existing row, never copied from credential-bearing config.
    patch = ''.join(f'- id: {name}\n  disabled: true\n' for name in DISABLED)
    patch += '- id: tools\n  config:\n    mode: native\n'
    patch += '- id: headless-runner\n  inject: [headlessStartup, comacbenchBoundary]\n'
    plugin_config = {"python": sys.executable, "source": str(ROOT), "session": str(session),
                     "auditDir": str(audit), "probeOnly": args.preflight}
    patch += '- insert:\n  - id: comacbench-public-boundary\n    name: ' + json.dumps(str(ROOT / 'scripts/dsh_public_boundary.mjs')) + '\n'
    patch += '    config: ' + json.dumps(plugin_config) + '\n'
    overlay = out / "boundary-overlay.yml"; overlay.write_text(patch)
    (out / "prompt.txt").write_text(PROMPT + '\n')
    metadata = {"started_at": started, "source_commit": revision, "initial_status": status,
                "preflight_only": args.preflight, "attempt_count": 1,
                "model_or_tool_overrides": "boundary_only", "model_selection": "existing profile, asserted at runtime",
                "no_config_or_credentials_read": True, "budget": {"actions": 32, "solves": 6, "per_solve_s": 120},
                "prompt_sha256": hashlib.sha256((PROMPT + '\n').encode()).hexdigest()}
    (out / "launch.json").write_text(json.dumps(metadata, indent=2) + '\n')
    env = os.environ.copy()
    env["COMACBENCH_DSH_ROOT"] = str(args.dsh_root.resolve())
    env["DSH_TELEMETRY_DISABLED"] = "1"
    command = [str(args.dsh.resolve()), "headless", "--patch", str(overlay), "--json", "-"]
    with (out / "dsh-events.jsonl").open('xb') as stdout, (out / "dsh-stderr.log").open('xb') as stderr:
        process = subprocess.Popen(command, cwd=public, env=env, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr, start_new_session=True)
        try:
            process.communicate((PROMPT + '\n').encode(), timeout=1800)
            exit_code = process.returncode
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try: process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL); process.wait()
            exit_code = 124
    metadata.update(exit_code=exit_code, finished_at=datetime.now(timezone.utc).isoformat())
    (out / "execution.json").write_text(json.dumps(metadata, indent=2) + '\n')
    if audit.exists():
        import shutil
        for name in ("dsh-events.jsonl", "execution.json"):
            shutil.copyfile(out / name, audit / name)
    print(json.dumps({"out": str(out), "exit_code": exit_code, "preflight_only": args.preflight}))
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
