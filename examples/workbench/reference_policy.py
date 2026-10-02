"""Deterministic public reference policy: interface/calibration evidence, not a model.

Uses the documented action API, with an independent implementation of the public
normalisation rules. It neither imports the reviewer nor edits the session files.
Run as: python examples/workbench/reference_policy.py --out ./change-reference-01
"""
from __future__ import annotations

import argparse
from decimal import Decimal
import math
from pathlib import Path
import sys
from typing import Any

# The source-workspace example can be launched from outside the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from comacbench.workbench import act, observe, read_json, start  # noqa: E402
from comacbench.workbench_report import export_report  # noqa: E402


def decisions(sources: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for key in sorted(sources):
        if not key.startswith("condition_"):
            continue
        data = sources[key]
        point = key[len("condition_"):]
        row = {"point": point, "case_id": data["case_id"], "source_revision": data["revision"]}
        issue = None
        values = {}
        if len(data["rows"]) != 1:
            issue = "missing_record" if not data["rows"] else "conflict"
        else:
            for field, units, output in (
                ("altitude", {"m": "1", "ft": "0.3048"}, "altitude_m"),
                ("mass_flow", {"kg/s": "1", "lb/s": "0.45359237"}, "mass_flow_kg_s"),
            ):
                quantity = data["rows"][0].get(field)
                if not isinstance(quantity, dict) or not isinstance(quantity.get("unit"), str):
                    issue = "missing_unit"
                elif quantity["unit"] not in units:
                    issue = "unsupported_unit"
                elif type(quantity.get("value")) not in (float, int):
                    issue = "invalid_value"
                else:
                    try:
                        value = float(Decimal(str(quantity["value"])) * Decimal(units[quantity["unit"]]))
                        if math.isfinite(value):
                            values[output] = value
                        else:
                            issue = "invalid_value"
                    except (ValueError, OverflowError):
                        issue = "invalid_value"
                if issue:
                    break
        if issue:
            row.update(status="needs_review", reason_code=issue)
        else:
            row.update(status="accepted", **values)
        rows.append(row)
    return rows


def payload(observation: dict[str, Any], target: str) -> dict[str, Any]:
    rows = decisions(observation["sources"])
    if target.startswith("normalized_"):
        return next(row for row in rows if row["point"] == target[len("normalized_"):])
    program = observation["sources"]["program"]
    accepted = [row for row in rows if row["status"] == "accepted"]
    rejected = [{"point": row["point"], "reason_code": row["reason_code"]}
                for row in rows if row["status"] == "needs_review"]
    if target == "run_plan":
        return {"program_name": program["name"], "program_revision": program["revision"],
                "runs": [{key: value for key, value in row.items() if key != "status"} for row in accepted]}
    return {"accepted_points": [row["point"] for row in accepted], "review_points": rejected,
            "program_revision": program["revision"],
            "claim": "needs_review" if rejected else "ready_for_execution", "solver_execution": "not_performed"}


def repair_phase(session: Path) -> None:
    observation = observe(session)
    order = sorted(node for node in observation["statuses"] if node.startswith("normalized_")) + ["run_plan", "review"]
    for target in order:
        observation = observe(session)
        if observation["statuses"][target] == "verified":
            continue
        response = act(session, {"op": "put", "target": target,
                                "basis": observation["dependencies"][target],
                                "payload": payload(observation, target)})
        if not response["result"]["ok"]:
            raise RuntimeError(response["result"])
        checked = act(session, {"op": "check", "target": target})
        if not checked["result"]["ok"]:
            raise RuntimeError(checked["result"])


def complete(session: Path, *, negative: str | None = None) -> None:
    while True:
        repair_phase(session)
        observation = observe(session)
        if observation["remaining_phases"]:
            advanced = act(session, {"op": "advance"})
            if not advanced["result"]["ok"]:
                raise RuntimeError(advanced["result"])
            if negative == "stale":
                result = act(session, {"op": "submit", "claim": "ready_for_execution"})
                if result["result"]["ok"]:
                    raise RuntimeError("negative control was accepted")
                return
        else:
            claim = payload(observation, "review")["claim"]
            if negative == "false-ready":
                claim = "ready_for_execution"
            result = act(session, {"op": "submit", "claim": claim})
            if result["result"]["ok"] == (negative == "false-ready"):
                raise RuntimeError(result["result"])
            return


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", type=Path, default=Path(__file__).with_name("workload-change-v1.json"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--negative", choices=("stale", "false-ready"))
    args = parser.parse_args()
    session = args.out / "session"
    start(session, read_json(args.scenario), {"name": "deterministic-reference", "revision": "1.0.0",
                                           "kind": "negative_control" if args.negative else "reference"})
    complete(session, negative=args.negative)
    result = export_report(session, args.out / "report")
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
