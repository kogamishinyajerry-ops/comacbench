"""Fixed-session public capability. Never accepts a filesystem path from the agent."""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
import re
from pathlib import Path
import sys

from . import workbench as wb


FIELDS = {"observe": {"op"}, "solve": {"op", "target"},
          "check": {"op", "target"}, "put": {"op", "target", "basis", "payload"},
          "advance": {"op"}, "submit": {"op", "claim"},
          "read_native": {"op", "target", "name"}}
NATIVE_FILES = {"model.inp", "model.dat", "model.solver.log", "model.sta", "model.cvg"}


def public_observation(observation: dict) -> dict:
    # Positive projection: the frozen manifest, phase list, and neighboring sessions
    # are never public. Current instructions/sources and already produced QoIs are.
    keys = ("protocol", "scenario_id", "instruction", "sources", "statuses",
            "dependencies", "artifacts", "complete", "actions_used", "actions_remaining", "counts")
    result = {key: deepcopy(observation[key]) for key in keys}
    contract = observation["contract"]
    result["contract"] = {
        "tool": "workbench", "argument": "request (JSON object)", "selector": "op",
        "fields": {op: sorted(fields) for op, fields in FIELDS.items()},
        "field_policy": "Exact fields only; no additional keys. op and target are strings.",
        "targets": contract["graph"],
        "operations": {
            "observe": "Read only the current inputs, statuses, artifact values and dependency digests.",
            "solve": "Run the fixed native model for a solution target; result becomes unchecked. No deck or command is accepted.",
            "check": "Validate the named current artifact against current inputs; stale/missing evidence is rejected.",
            "put": "Only target=review. Copy current dependencies.review as basis. Supply your own payload with the fields below.",
            "advance": "After all current targets are verified, request the next available work package. no_next_phase means none is available.",
            "submit": "After current targets are verified, submit claim from your review. mandatory_changes_remaining requires further work packages.",
            "read_native": "Read one allowlisted text file of the current solution target's existing job. No solve or action budget use.",
        },
        "review_fields": {"cases": "One object per load point, using case_fields below",
                          "claim": "requirements_met iff every abs(uy_mm) <= current requirement.max_tip_mm; otherwise needs_review",
                          "requirement_revision": "Current sources.requirement.revision (string)"},
        "case_fields": {"point": "load point ID (remove solution_ from target)",
                        "uy_mm": "Signed numeric tip displacement from native payload.qoi",
                        "rfy_n": "Numeric support reaction from native payload.qoi",
                        "meets_requirement": "Boolean abs(uy_mm) <= current max_tip_mm"},
        "path_semantics": "No filesystem paths or session IDs are accepted. The tool is bound by the host to exactly one session. target is a graph node ID, name is an exact filename from native_files. Slashes, traversal, absolute paths and neighboring results are rejected.",
        "native_files": sorted(NATIVE_FILES),
        "errors": "Feedback is result={ok,code,...}. Invalid gateway requests are denied before environment acceptance; accepted actions, including rejected actions, consume budget. Missing/stale evidence, invalid review, false claim, exhausted budgets and unavailable next package remain errors. Read/host errors never imply success.",
        "native_budget": deepcopy(contract["native_budget"]),
        "scope": "Already public fixed calibration task; no hidden/unseen/generalization claim or engineering approval. Input/solver/physical thresholds are unchanged.",
    }
    return result


def dispatch(session: Path, request: object) -> dict:
    if (not isinstance(request, dict) or not isinstance(request.get("op"), str)
            or request["op"] not in FIELDS or set(request) != FIELDS[request["op"]]):
        return {"result": {"ok": False, "code": "public_request_denied"}}
    op = request["op"]
    try:
        observation = wb.observe(session)
        if "target" in request and (not isinstance(request["target"], str)
                                     or request["target"] not in observation["statuses"]):
            return {"result": {"ok": False, "code": "public_target_denied"}}
        if op == "observe":
            return {"result": {"ok": True, "code": "observed"},
                    "observation": public_observation(observation)}
        if op == "read_native":
            name, target = request["name"], request["target"]
            if not isinstance(name, str) or name not in NATIVE_FILES or not target.startswith("solution_"):
                return {"result": {"ok": False, "code": "public_file_denied"}}
            payload = observation["artifacts"].get(target, {}).get("payload", {})
            job = payload.get("job_id")
            if not isinstance(job, str) or not job.isascii() or not job.isdigit():
                return {"result": {"ok": False, "code": "native_file_unavailable"}}
            root = (session / "native" / job).resolve()
            path = root / name
            if path.is_symlink() or path.resolve().parent != root or not path.is_file():
                return {"result": {"ok": False, "code": "native_file_unavailable"}}
            if path.stat().st_size > 1_000_000:
                return {"result": {"ok": False, "code": "native_file_too_large"}}
            return {"result": {"ok": True, "code": "native_text", "target": target,
                               "name": name, "text": path.read_text(encoding="utf-8", errors="replace")}}
        value = wb.act(session, request)
        return {"result": value["result"], "observation": public_observation(value["observation"])}
    except wb.WorkbenchError as exc:
        detail = str(exc) if re.fullmatch(r"[a-z0-9_]{1,80}", str(exc)) else "internal_archive_error"
        return {"result": {"ok": False, "code": "workbench_error", "detail": detail}}
    except OSError:
        # Never leak internal filesystem locations through an exception string.
        return {"result": {"ok": False, "code": "host_io_error"}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True, type=Path)  # supplied only by trusted host
    args = parser.parse_args()
    raw = sys.stdin.buffer.read(wb.MAX_ACTION_BYTES + 1)
    try:
        if len(raw) > wb.MAX_ACTION_BYTES:
            raise ValueError("request_too_large")
        request = wb.loads(raw.decode("utf-8"))
        value = dispatch(args.session, request)
    except (wb.WorkbenchError, ValueError, UnicodeError):
        value = {"result": {"ok": False, "code": "public_json_denied"}}
    print(json.dumps(value, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
