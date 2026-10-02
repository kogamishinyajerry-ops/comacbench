"""Content review for the public, synthetic workload-change family.

No solver runs here. The evaluator derives expectations from frozen source data,
never from an agent's claimed validity, earlier report, or proposed normalisation.
The reference policy in examples/workbench deliberately does not import this file.
"""
from __future__ import annotations

import math
from typing import Any

FAMILY = "comacbench.workload-change.v1"
REASONS = ("missing_record", "conflict", "missing_unit", "unsupported_unit", "invalid_value")


def graph(scenario: dict[str, Any]) -> dict[str, list[str]]:
    """One reviewed disposition per condition, then a plan and its review report."""
    nodes = {f"normalized_{key}": [f"condition_{key}"]
             for key in sorted(scenario["conditions"])}
    normalized = list(nodes)
    nodes["run_plan"] = normalized + ["program"]
    nodes["review"] = normalized + ["run_plan", "program"]
    return nodes


def public_contract(scenario: dict[str, Any]) -> dict[str, Any]:
    return {
        "family": FAMILY,
        "graph": graph(scenario),
        "normalization": {
            "accepted": ["point", "case_id", "source_revision", "status",
                         "altitude_m", "mass_flow_kg_s"],
            "needs_review": ["point", "case_id", "source_revision", "status", "reason_code"],
            "reason_codes": list(REASONS),
            "rule": "Zero rows: missing_record; multiple rows: conflict (even identical). "
                    "For a single row inspect altitude, then mass_flow; within each quantity check missing unit, "
                    "unsupported unit, then invalid value. Never infer a missing unit.",
            "conversions": {"altitude": {"m": 1.0, "ft": 0.3048},
                            "mass_flow": {"kg/s": 1.0, "lb/s": 0.45359237}},
            "numeric_comparison": {"relative_tolerance": 1e-10, "absolute_tolerance": 1e-8},
        },
        "run_plan": {
            "fields": ["program_name", "program_revision", "runs"],
            "run_fields": ["point", "case_id", "source_revision", "altitude_m", "mass_flow_kg_s"],
            "rule": "Exactly one row per accepted condition. Row order is irrelevant; duplicates fail.",
        },
        "review": {
            "fields": ["accepted_points", "review_points", "program_revision", "claim", "solver_execution"],
            "review_point_fields": ["point", "reason_code"],
            "claim": "needs_review if any condition needs review; otherwise ready_for_execution",
            "solver_execution": "not_performed",
        },
        "lineage": "put.basis must contain exactly the dependency digests in observe.dependencies. "
                   "Each target and all its parents must pass check at their current digest. "
                   "A changed source invalidates downstream checks, even if its revision label is unchanged.",
        "scope": "Input-package preparation only; no physical performance or solver validity is evaluated.",
    }


def _quantity(row: dict[str, Any], field: str, units: dict[str, float]) -> tuple[float | None, str | None]:
    quantity = row.get(field)
    if not isinstance(quantity, dict) or not isinstance(quantity.get("unit"), str):
        return None, "missing_unit"
    if quantity["unit"] not in units:
        return None, "unsupported_unit"
    value = quantity.get("value")
    if type(value) not in (int, float):
        return None, "invalid_value"
    try:
        result = value * units[quantity["unit"]]
        if not math.isfinite(result):
            return None, "invalid_value"
    except (OverflowError, ValueError):
        return None, "invalid_value"
    return result, None


def _disposition(point: str, condition: dict[str, Any]) -> dict[str, Any]:
    result = {"point": point, "case_id": condition["case_id"],
              "source_revision": condition["revision"]}
    rows = condition["rows"]
    reason = "missing_record" if not rows else "conflict" if len(rows) > 1 else None
    if reason is None:
        altitude, reason = _quantity(rows[0], "altitude", {"m": 1.0, "ft": 0.3048})
    if reason is None:
        flow, reason = _quantity(rows[0], "mass_flow", {"kg/s": 1.0, "lb/s": 0.45359237})
    if reason:
        return {**result, "status": "needs_review", "reason_code": reason}
    return {**result, "status": "accepted", "altitude_m": altitude, "mass_flow_kg_s": flow}


def _expectation(scenario: dict[str, Any], sources: dict[str, Any], target: str) -> dict[str, Any]:
    if target.startswith("normalized_"):
        point = target[len("normalized_"):]
        return _disposition(point, sources[f"condition_{point}"])
    dispositions = [_disposition(point, sources[f"condition_{point}"])
                    for point in sorted(scenario["conditions"])]
    accepted = [row for row in dispositions if row["status"] == "accepted"]
    program = sources["program"]
    if target == "run_plan":
        return {"program_name": program["name"], "program_revision": program["revision"],
                "runs": [{key: value for key, value in row.items() if key != "status"}
                         for row in accepted]}
    rejected = [{"point": row["point"], "reason_code": row["reason_code"]}
                for row in dispositions if row["status"] != "accepted"]
    return {"accepted_points": [row["point"] for row in accepted],
            "review_points": rejected, "program_revision": program["revision"],
            "claim": "needs_review" if rejected else "ready_for_execution",
            "solver_execution": "not_performed"}


def _equal(actual: Any, expected: Any) -> bool:
    if type(expected) in (int, float):
        if type(actual) not in (int, float):
            return False
        try:
            return math.isfinite(actual) and math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-8)
        except (OverflowError, ValueError):
            return False
    if isinstance(expected, dict):
        return (isinstance(actual, dict) and set(actual) == set(expected)
                and all(_equal(actual[key], value) for key, value in expected.items()))
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            return False
        # These lists describe sets of uniquely identified points, not sequences.
        # Matching with removal keeps duplicates visible and avoids dict-overwrite bugs.
        remaining = list(actual)
        for item in expected:
            for index, candidate in enumerate(remaining):
                if _equal(candidate, item):
                    remaining.pop(index)
                    break
            else:
                return False
        return True
    return type(actual) is type(expected) and actual == expected


def review(scenario: dict[str, Any], sources: dict[str, Any], target: str,
           payload: Any) -> list[dict[str, Any]]:
    """Return semantic checks. This function cannot mark lineage or a session valid."""
    if target not in graph(scenario):
        raise ValueError("unknown_target")
    expected = _expectation(scenario, sources, target)
    if not isinstance(payload, dict):
        return [{"check": "object_required", "passed": False}]
    checks = [{"check": "field_contract", "passed": set(payload) == set(expected)}]
    for key, value in expected.items():
        checks.append({"check": f"content.{key}",
                       "passed": key in payload and _equal(payload[key], value)})
    return checks
