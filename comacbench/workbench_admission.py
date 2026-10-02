"""Maintainer-only audit of a public trial's host controls and lossless tool records.

Not an authentication or hostile-administrator boundary. Agent prose is never evidence
of protocol conformance. Historical reports are not modified by this module.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def unknown_admission(kind: str = "user_agent", reason: str = "No complete, verified host-control and tool-call record supplied.") -> dict:
    return {"protocol_conformance": "unknown" if kind == "user_agent" else "not_applicable",
            "reference_exposure": "unknown" if kind == "user_agent" else "reference_or_control",
            "score_admissible": False, "deviation_reasons": [reason] if kind == "user_agent" else ["Reference and negative controls are not model scores."],
            "evaluation_scope": "same_public_task_development_repeat",
            "unseen_generalization_score_admissible": False,
            "admission_evidence": {}, "trust_scope": "trusted local maintainer audit; not endpoint or OS attestation"}


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_trial(data: dict, directory: Path) -> dict:
    admission = unknown_admission(data["manifest"]["subject"]["kind"])
    if data["manifest"]["subject"]["kind"] != "user_agent":
        return admission
    issues = []
    try:
        control = _read(directory / "control.json")
        rows = _lines(directory / "boundary.jsonl")
        stream = _lines(directory / "dsh-events.jsonl")
        end = _read(directory / "execution.json")
        for name in ("control.json", "boundary.jsonl", "dsh-events.jsonl", "execution.json"):
            admission["admission_evidence"][name] = _sha(directory / name)
        manifest = data["manifest"]
        source = Path(__file__).resolve().parents[1]
        checks = {
            "control_protocol": control["protocol"] == "comacbench.public-boundary.v1",
            "session_binding": control["session_manifest_sha256"] == manifest["manifest_sha256"],
            "engine_binding": control["engine_sha256"] == manifest["engine_sha256"],
            "plugin_binding": control["plugin_sha256"] == _sha(source / "scripts/dsh_public_boundary.mjs"),
            "gateway_binding": control["gateway_sha256"] == _sha(source / "comacbench/workbench_public.py"),
            "fixed_budget": control["budget"] == {"actions": 32, "solver_calls": 6, "solve_timeout_s": 120, "tool_calls": 96, "model_assemblies": 64},
            "existing_model": control["model"]["provider"] == "zai-coding-cn" and control["model"]["model"] == "glm-4.7",
            "fresh_context": control["fresh_headless_session"] is True and control["creation_source"] == "startup",
            "context_boundary": control["runtime_context_suppressed"] is True and control["mode"] == "native",
            "scope": control["task_scope"] == "same_public_task_development_repeat" and control["prior_public_task_exposure"] is True,
            "live_denials": control["probe"]["all_denied"] is True and control["probe"]["schemas"] == ["workbench"]
                            and len(control["probe"]["probes"]) == 9 and all(p["is_error"] is True for p in control["probe"]["probes"]),
            "audit_sequence": [r["seq"] for r in rows] == list(range(1, len(rows) + 1)),
            "execution_closed": end["exit_code"] == 0 and end["attempt_count"] == 1 and end["model_or_tool_overrides"] == "boundary_only",
            "fresh_session_stream": len([r for r in stream if r["type"] == "session"]) == 1
                and next(r for r in stream if r["type"] == "session")["sessionId"] == control["agent_id"],
            "completed_stream": any(r["type"] == "status" and r.get("phase") == "turn_end"
                                    and r.get("reason", {}).get("kind") == "completed" for r in stream)
                                and stream[-1]["type"] == "final",
        }
        ready = [r for r in rows if r["type"] == "ready"]
        assemblies = [r for r in rows if r["type"] == "assembly"]
        prompts = [r for r in rows if r["type"] == "prompt_probe"]
        checks["public_prompt_probed"] = (len(prompts) == 1 and len(prompts[0]["sections"]) == 1
            and prompts[0]["sections"][0]["text"] == control["complete_public_system"]
            and not any(c["text"] for c in prompts[0]["contexts"]) and prompts[0]["schemas"] == ["workbench"])
        checks["controlled_assemblies"] = (len(ready) == 1 and bool(assemblies)
            and len(assemblies) <= 64 and ready[0]["seq"] < assemblies[0]["seq"]
            and all(r["schemas"] == ["workbench"] and not any(c["text"] for c in r["contexts"])
                    and r["model"] == control["model"] for r in assemblies)
            and not any(r["type"] == "blocked" for r in rows))
        calls = [r for r in stream if r["type"] == "tool_call"]
        results = [r for r in stream if r["type"] == "tool_result"]
        host_results = [r for r in rows if r["type"] == "tool_result" and not r["call_id"].startswith("boundary-probe-")]
        broker = [r for r in rows if r["type"] == "broker"]
        checks["all_calls_captured"] = (0 < len(calls) <= 96 and len(calls) == len(host_results) == len(results)
            and len({r["callId"] for r in calls}) == len(calls)
            and {r["callId"] for r in calls} == {r["callId"] for r in results} == {r["call_id"] for r in host_results})
        captured = {r["call_id"]: r for r in host_results}
        checks["call_arguments_match"] = all(r["tool"] == captured[r["callId"]]["name"]
            and r["input"] == captured[r["callId"]]["arguments"] for r in calls)
        checks["only_public_tool"] = all(r["tool"] == "workbench" for r in calls)
        projected = {r["call_id"]: ''.join(c.get("text", "") for c in r["content"] if c["type"] == "text") for r in host_results}
        checks["results_match"] = all(r["result"] == projected[r["callId"]] for r in results)
        checks["brokers_match"] = all(r["call_id"] in captured and r["request"] == captured[r["call_id"]]["arguments"]["request"]
            and r["exit_code"] == 0 and json.loads(r["stdout"]) == json.loads(projected[r["call_id"]]) for r in broker)
        accepted = [r["request"] for r in broker if r["request"].get("op") not in {"observe", "read_native"}
                    and "observation" in json.loads(r["stdout"])]
        checks["actions_match_environment"] = accepted == [e["action"] for e in data["events"]]
        checks["no_unlogged_host_tool"] = len(broker) == sum(not r["is_error"] for r in host_results)
        checks["public_projection_only"] = all("remaining_phases" not in json.loads(r["stdout"]).get("observation", {})
            and "manifest" not in json.loads(r["stdout"]) for r in broker)
        issues = [key for key, passed in checks.items() if not passed]
        admission["audit_checks"] = checks
        admission["tool_calls"] = len(calls)
        admission["prior_public_task_exposure"] = True
        if not issues:
            admission.update(protocol_conformance="conformant", reference_exposure="not_observed_in_recorded_run",
                             score_admissible=True, deviation_reasons=[])
        else:
            admission["deviation_reasons"] = ["Host audit did not establish conformance: " + ", ".join(issues)]
    except (OSError, ValueError, KeyError, TypeError, StopIteration, IndexError) as exc:
        admission["deviation_reasons"] = ["Incomplete or inconsistent host audit: " + type(exc).__name__]
    return admission


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True, type=Path)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    from .workbench_report import export_report
    print(json.dumps(export_report(args.session, args.out, admission_evidence=args.audit)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
