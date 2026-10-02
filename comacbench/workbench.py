"""Opt-in, event-replayed tool environment for public engineering work packages.

Any trusted local Agent can use this CLI as a tool. It is not another Agent host,
not a sandbox, and not the existing pack/Campaign protocol. Only brokered action
counts are enforced; tokens, human interventions and external solver calls are not.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any, Iterator
import uuid

from . import workbench_review as evaluator

PROTOCOL = "comacbench.workbench.v1"
MAX_BYTES = 262144
MAX_ACTIONS = 1024
MAX_ACTION_BYTES = 32768
ID = re.compile(r"[a-z][a-z0-9_\-]{0,31}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")


class WorkbenchError(ValueError):
    """Invalid material, incompatible engine, or unverifiable local archive."""


def canonical(value: Any) -> bytes:
    try:
        return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    except (ValueError, TypeError, OverflowError, RecursionError) as exc:
        raise WorkbenchError("invalid_json_value") from exc


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise WorkbenchError("duplicate_json_key")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise WorkbenchError("nonfinite_json_number")


def loads(text: str) -> Any:
    if len(text.encode("utf-8")) > MAX_BYTES:
        raise WorkbenchError("json_too_large")
    try:
        value = json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)
        canonical(value)  # Also reject 1e999, which Python otherwise parses as infinity.
        return value
    except (ValueError, TypeError, RecursionError, UnicodeError) as exc:
        raise WorkbenchError(f"invalid_json: {exc}") from exc


def _ordinary(path: Path, *, directory: bool = False) -> None:
    info = path.lstat()
    if (stat.S_ISLNK(info.st_mode)
            or getattr(info, "st_file_attributes", 0) & 0x400
            or not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))):
        raise WorkbenchError("link_or_special_file")


def read_json(path: Path) -> Any:
    _ordinary(path)
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise WorkbenchError("json_too_large")
    try:
        return loads(raw.decode("utf-8"))
    except UnicodeError as exc:
        raise WorkbenchError("invalid_utf8") from exc


def _write_new(path: Path, value: Any) -> None:
    raw = canonical(value)
    if len(raw) > MAX_BYTES:
        raise WorkbenchError("json_too_large")
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def engine_identity() -> str:
    root = Path(__file__).parent
    return digest({name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                   for name in ("workbench.py", "workbench_review.py")})


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and len(value) <= 2000


def _source_valid(key: str, value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    if key.startswith("condition_"):
        return (set(value) == {"case_id", "revision", "rows"}
                and _text(value["case_id"]) and _text(value["revision"])
                and isinstance(value["rows"], list) and len(value["rows"]) <= 32
                and all(isinstance(row, dict) for row in value["rows"]))
    if key == "program":
        return set(value) == {"name", "revision"} and all(_text(v) for v in value.values())
    return key == "note" and set(value) == {"text"} and _text(value["text"])


def validate_scenario(scenario: Any) -> dict[str, Any]:
    required = {"protocol", "id", "revision", "title", "description", "license",
                "max_actions", "conditions", "program", "note", "phases"}
    if not isinstance(scenario, dict) or set(scenario) != required:
        raise WorkbenchError("scenario_fields")
    if scenario["protocol"] != evaluator.FAMILY:
        raise WorkbenchError("unsupported_family")
    if not isinstance(scenario["id"], str) or not ID.fullmatch(scenario["id"]):
        raise WorkbenchError("scenario_id")
    if not all(_text(scenario[key]) for key in ("revision", "title", "description", "license")):
        raise WorkbenchError("scenario_metadata")
    if type(scenario["max_actions"]) is not int or not 1 <= scenario["max_actions"] <= MAX_ACTIONS:
        raise WorkbenchError("action_budget")
    conditions = scenario["conditions"]
    if (not isinstance(conditions, dict) or not 1 <= len(conditions) <= 32
            or any(not isinstance(key, str) or not ID.fullmatch(key) for key in conditions)):
        raise WorkbenchError("condition_ids")
    sources = {f"condition_{key}": value for key, value in conditions.items()}
    sources.update(program=scenario["program"], note=scenario["note"])
    if any(not _source_valid(key, value) for key, value in sources.items()):
        raise WorkbenchError("source_schema")
    phases = scenario["phases"]
    if not isinstance(phases, list) or not 1 <= len(phases) <= 16:
        raise WorkbenchError("phase_schema")
    ids: set[str] = set()
    for index, phase in enumerate(phases):
        if (not isinstance(phase, dict) or set(phase) != {"id", "instruction", "changes"}
                or not isinstance(phase["id"], str) or not ID.fullmatch(phase["id"])
                or phase["id"] in ids or not _text(phase["instruction"])
                or not isinstance(phase["changes"], dict)):
            raise WorkbenchError("phase_schema")
        ids.add(phase["id"])
        if (index == 0 and phase["changes"]) or (index > 0 and not phase["changes"]):
            raise WorkbenchError("phase_changes")
        for key, value in phase["changes"].items():
            if key not in sources or not _source_valid(key, value):
                raise WorkbenchError("unknown_or_invalid_source_change")
    if len(canonical(scenario)) > MAX_BYTES // 2:
        raise WorkbenchError("scenario_too_large")
    return deepcopy(scenario)


def _initial(scenario: dict[str, Any]) -> dict[str, Any]:
    sources = {f"condition_{key}": deepcopy(value) for key, value in scenario["conditions"].items()}
    sources.update(program=deepcopy(scenario["program"]), note=deepcopy(scenario["note"]))
    return {"phase": 0, "sources": sources, "artifacts": {}, "checks": {},
            "actions_used": 0, "complete": False, "counts": {}}


def _node_digest(state: dict[str, Any], node: str) -> str | None:
    if node in state["sources"]:
        return digest(state["sources"][node])
    artifact = state["artifacts"].get(node)
    return digest(artifact) if artifact is not None else None


def _basis(state: dict[str, Any], dependencies: dict[str, list[str]], node: str) -> dict[str, Any]:
    return {parent: _node_digest(state, parent) for parent in dependencies[node]}


def _statuses(scenario: dict[str, Any], state: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    dependencies = evaluator.graph(scenario)
    for node, parents in dependencies.items():
        artifact = state["artifacts"].get(node)
        if artifact is None:
            result[node] = "missing"
        elif (artifact["basis"] != _basis(state, dependencies, node)
              or any(result[parent] != "verified" for parent in parents if parent in dependencies)):
            result[node] = "stale"
        else:
            checked = state["checks"].get(node)
            if checked is None or checked["artifact_sha256"] != _node_digest(state, node):
                result[node] = "unchecked"
            else:
                result[node] = "verified" if checked["passed"] else "failed"
    return result


def _transition(scenario: dict[str, Any], state: dict[str, Any], action: Any) -> dict[str, Any]:
    """Pure deterministic transition. Both execution and archive replay use this."""
    if state["complete"]:
        raise WorkbenchError("session_already_complete")
    if state["actions_used"] >= scenario["max_actions"]:
        raise WorkbenchError("action_budget_exhausted")
    state["actions_used"] += 1
    operation = action.get("op") if isinstance(action, dict) else None
    counter = operation if isinstance(operation, str) and operation in {"put", "check", "advance", "submit"} else "invalid"
    state["counts"][counter] = state["counts"].get(counter, 0) + 1

    def fail(code: str, **details: Any) -> dict[str, Any]:
        state["counts"]["rejected"] = state["counts"].get("rejected", 0) + 1
        return {"ok": False, "code": code, **details}

    dependencies = evaluator.graph(scenario)
    if not isinstance(action, dict):
        return fail("action_object_required")
    fields = {"put": {"op", "target", "basis", "payload"}, "check": {"op", "target"},
              "advance": {"op"}, "submit": {"op", "claim"}}
    if not isinstance(operation, str) or operation not in fields or set(action) != fields[operation]:
        return fail("action_contract")
    if operation in {"put", "check"}:
        target = action["target"]
        if not isinstance(target, str) or target not in dependencies:
            return fail("unknown_target")
        if operation == "put":
            basis = action["basis"]
            if (not isinstance(basis, dict) or set(basis) != set(dependencies[target])
                    or any(value is not None and (not isinstance(value, str) or not SHA.fullmatch(value))
                           for value in basis.values())):
                return fail("basis_contract")
            state["artifacts"][target] = {"payload": deepcopy(action["payload"]), "basis": deepcopy(basis)}
            state["checks"].pop(target, None)
            return {"ok": True, "code": "artifact_recorded", "target": target,
                    "artifact_sha256": _node_digest(state, target),
                    "status": _statuses(scenario, state)[target]}
        statuses = _statuses(scenario, state)
        if statuses[target] in {"missing", "stale"}:
            return fail("missing_or_stale_evidence", target=target, status=statuses[target])
        checks = evaluator.review(scenario, state["sources"], target,
                                  state["artifacts"][target]["payload"])
        passed = all(item["passed"] for item in checks)
        state["checks"][target] = {"artifact_sha256": _node_digest(state, target), "passed": passed}
        if not passed:
            return fail("content_review_failed", target=target, checks=checks)
        return {"ok": True, "code": "content_verified", "target": target, "checks": checks}
    statuses = _statuses(scenario, state)
    if any(value != "verified" for value in statuses.values()):
        return fail("unverified_targets", targets={key: value for key, value in statuses.items()
                                                   if value != "verified"})
    if operation == "advance":
        if state["phase"] + 1 >= len(scenario["phases"]):
            return fail("no_next_phase")
        before = {key: _node_digest(state, key) for key in dependencies}
        state["phase"] += 1
        changes = scenario["phases"][state["phase"]]["changes"]
        changed = sorted(key for key, value in changes.items() if digest(value) != digest(state["sources"][key]))
        state["sources"].update(deepcopy(changes))
        after = _statuses(scenario, state)
        return {"ok": True, "code": "phase_advanced", "phase": scenario["phases"][state["phase"]]["id"],
                "changed_sources": changed,
                "invalidated": [key for key, value in after.items() if value != "verified"],
                "retained": [key for key, value in after.items() if value == "verified"],
                "prior_artifact_digests": before}
    if state["phase"] + 1 != len(scenario["phases"]):
        return fail("mandatory_changes_remaining")
    required_claim = state["artifacts"]["review"]["payload"]["claim"]
    if action["claim"] != required_claim:
        return fail("false_completion_claim", required_claim=required_claim)
    state["complete"] = True
    return {"ok": True, "code": "work_package_complete", "claim": required_claim,
            "solver_execution": "not_performed", "engineering_approval": False}


@contextmanager
def _locked(root: Path) -> Iterator[None]:
    _ordinary(root, directory=True)
    lock = root / ".writer.lock"
    try:
        stream = lock.open("x", encoding="utf-8")
    except FileExistsError as exc:
        raise WorkbenchError("session_locked; inspect the writer before recovering an interrupted session") from exc
    try:
        with stream:
            stream.write(str(os.getpid()))
        yield
    finally:
        lock.unlink()


def _load(root: Path) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    manifest = read_json(root / "session.json")
    if (not isinstance(manifest, dict) or manifest.get("protocol") != PROTOCOL
            or set(manifest) != {"protocol", "session_id", "created_at", "scenario", "scenario_sha256",
                                 "engine_sha256", "subject", "manifest_sha256"}):
        raise WorkbenchError("session_manifest_contract")
    envelope = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if digest(envelope) != manifest["manifest_sha256"]:
        raise WorkbenchError("session_manifest_changed")
    scenario = validate_scenario(manifest["scenario"])
    if digest(scenario) != manifest["scenario_sha256"]:
        raise WorkbenchError("scenario_changed")
    if engine_identity() != manifest["engine_sha256"]:
        raise WorkbenchError("engine_changed; keep the archive and start a new session")
    _validate_subject(manifest["subject"])
    state = _initial(scenario)
    directory = root / "events"
    _ordinary(directory, directory=True)
    files = list(directory.iterdir())
    if len(files) > scenario["max_actions"]:
        raise WorkbenchError("event_count_exceeds_budget")
    files.sort(key=lambda item: item.name)
    events = []
    previous = manifest["manifest_sha256"]
    for index, path in enumerate(files, 1):
        if path.name != f"{index:06d}.json":
            raise WorkbenchError("event_gap_or_unregistered_file")
        event = read_json(path)
        if not isinstance(event, dict) or set(event) != {"seq", "previous_sha256", "action", "result"}:
            raise WorkbenchError("event_contract")
        if type(event["seq"]) is not int or event["seq"] != index or event["previous_sha256"] != previous:
            raise WorkbenchError("event_chain_mismatch")
        result = _transition(scenario, state, event["action"])
        if canonical(result) != canonical(event["result"]):
            raise WorkbenchError("event_result_mismatch")
        events.append(event)
        previous = digest(event)
    return manifest, state, events


def _validate_subject(subject: Any) -> None:
    if (not isinstance(subject, dict) or set(subject) != {"name", "revision", "kind"}
            or not _text(subject["name"]) or not _text(subject["revision"])
            or not isinstance(subject["kind"], str)
            or subject["kind"] not in {"user_agent", "reference", "negative_control"}):
        raise WorkbenchError("subject_contract")


def start(root: Path, scenario: dict[str, Any], subject: dict[str, str]) -> dict[str, Any]:
    scenario = validate_scenario(scenario)
    _validate_subject(subject)
    manifest = {"protocol": PROTOCOL, "session_id": uuid.uuid4().hex,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "scenario": scenario, "scenario_sha256": digest(scenario),
                "engine_sha256": engine_identity(), "subject": deepcopy(subject)}
    manifest["manifest_sha256"] = digest(manifest)
    root.mkdir(parents=True, exist_ok=False)
    (root / "events").mkdir()
    _write_new(root / "session.json", manifest)
    return observe(root)


def _observation(manifest: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    scenario = manifest["scenario"]
    dependencies = evaluator.graph(scenario)
    return {"protocol": PROTOCOL, "scenario_id": scenario["id"], "scenario_sha256": manifest["scenario_sha256"],
            "subject": manifest["subject"], "phase_index": state["phase"],
            "phase": scenario["phases"][state["phase"]]["id"],
            "instruction": scenario["phases"][state["phase"]]["instruction"],
            "remaining_phases": len(scenario["phases"]) - state["phase"] - 1,
            "sources": deepcopy(state["sources"]), "statuses": _statuses(scenario, state),
            "dependencies": {node: _basis(state, dependencies, node) for node in dependencies},
            "artifacts": deepcopy(state["artifacts"]),
            "complete": state["complete"], "actions_used": state["actions_used"],
            "actions_remaining": scenario["max_actions"] - state["actions_used"],
            "counts": deepcopy(state["counts"]), "contract": evaluator.public_contract(scenario),
            "limitations": {"public_regression_only": True, "publishable": False,
                            "isolated_transfer_verified": False, "solver_execution": "not_performed",
                            "identity_scope": "declared_subject_only", "sandboxed": False,
                            "budget_scope": "brokered_actions_only"}}


def observe(root: Path) -> dict[str, Any]:
    with _locked(root):
        manifest, state, _ = _load(root)
        return _observation(manifest, state)


def act(root: Path, action: Any) -> dict[str, Any]:
    # Snapshot all JSON values, rejecting nonfinite numbers and oversized requests.
    raw = canonical(action)
    if len(raw) > MAX_ACTION_BYTES:
        raise WorkbenchError("action_too_large")
    action = loads(raw.decode("utf-8"))
    with _locked(root):
        manifest, state, events = _load(root)
        result = _transition(manifest["scenario"], state, action)
        event = {"seq": len(events) + 1,
                 "previous_sha256": digest(events[-1]) if events else manifest["manifest_sha256"],
                 "action": action, "result": result}
        # A crash leaves an explicit invalid tail; it is never silently discarded.
        _write_new(root / "events" / f"{len(events) + 1:06d}.json", event)
        return {"result": result, "observation": _observation(manifest, state)}


def snapshot(root: Path) -> dict[str, Any]:
    """Recompute the report from every original action, not cached success flags."""
    with _locked(root):
        manifest, state, events = _load(root)
        return {"protocol": PROTOCOL, "manifest": manifest,
                "observation": _observation(manifest, state), "events": events}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    begin = commands.add_parser("start", help="Create a fresh public-regression session")
    begin.add_argument("scenario", type=Path)
    begin.add_argument("--out", type=Path, required=True)
    begin.add_argument("--subject", required=True)
    begin.add_argument("--revision", required=True)
    begin.add_argument("--kind", choices=("user_agent", "reference", "negative_control"), default="user_agent")
    view = commands.add_parser("observe", help="Read state and public rules without spending an action")
    view.add_argument("session", type=Path)
    action = commands.add_parser("act", help="Apply one bounded JSON action; failures are retained")
    action.add_argument("session", type=Path)
    action.add_argument("--action-file", type=Path, required=True)
    report = commands.add_parser("report", help="Re-review the archive and write offline JSON + HTML")
    report.add_argument("session", type=Path)
    report.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "start":
            value = start(args.out, read_json(args.scenario),
                          {"name": args.subject, "revision": args.revision, "kind": args.kind})
        elif args.command == "observe":
            value = observe(args.session)
        elif args.command == "act":
            value = act(args.session, read_json(args.action_file))
        else:
            from .workbench_report import export_report
            value = export_report(args.session, args.out)
        print(json.dumps(value, ensure_ascii=False, allow_nan=False))
        return 1 if args.command == "act" and not value["result"]["ok"] else 0
    except (WorkbenchError, OSError, UnicodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
