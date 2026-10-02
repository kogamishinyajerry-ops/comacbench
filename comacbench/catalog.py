"""Role-based product entry points, separate from registry integration status.

Default output is the pilot work package. --role all shows onboarding, calibration,
experimental and compatibility entries. No command runs a model or changes scores.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import sys
from typing import Any

from .workbench import ID, WorkbenchError, read_json

ENTRY_ROLES = {"pilot", "experimental", "onboarding", "calibration", "legacy"}
GROUP_ROLES = {"diagnostic", "calibration", "component", "research"}


def load_catalog(root: Path) -> dict[str, Any]:
    data = read_json(root / "registry" / "product-scope.json")
    if (not isinstance(data, dict) or set(data) != {"protocol", "revision", "default_benchmark_role", "entries", "benchmark_groups"}
            or data["protocol"] != "comacbench.catalog.v1" or data["default_benchmark_role"] != "research"
            or not isinstance(data["revision"], str) or not data["revision"]):
        raise WorkbenchError("catalog_contract")
    if not isinstance(data["entries"], list) or not data["entries"]:
        raise WorkbenchError("catalog_entries")
    seen = set()
    paths = set()
    for entry in data["entries"]:
        if (not isinstance(entry, dict) or set(entry) != {"id", "kind", "role", "path", "title", "purpose", "requires", "limits"}
                or not all(isinstance(value, str) and value.strip() for value in entry.values())
                or not ID.fullmatch(entry["id"]) or entry["id"] in seen
                or entry["kind"] not in {"pack", "workbench"} or entry["role"] not in ENTRY_ROLES):
            raise WorkbenchError("catalog_entry")
        path = PurePosixPath(entry["path"])
        if (path.is_absolute() or any(part in {"", ".", ".."} for part in entry["path"].split("/"))
                or "\\" in entry["path"] or ":" in entry["path"] or entry["path"] in paths):
            raise WorkbenchError("catalog_path")
        if (entry["kind"] == "pack" and (path.parts[0] != "packs" or path.name != "pack.yaml")) or (
                entry["kind"] == "workbench" and (path.parts[:2] != ("examples", "workbench") or path.suffix != ".json")):
            raise WorkbenchError("catalog_kind_path")
        seen.add(entry["id"])
        paths.add(entry["path"])
    if not isinstance(data["benchmark_groups"], list):
        raise WorkbenchError("catalog_groups")
    assigned = set()
    groups = set()
    for group in data["benchmark_groups"]:
        if (not isinstance(group, dict) or set(group) != {"id", "role", "registry_ids", "decision"}
                or not isinstance(group["id"], str) or not ID.fullmatch(group["id"])
                or group["id"] in groups or not isinstance(group["role"], str) or group["role"] not in GROUP_ROLES
                or not isinstance(group["decision"], str) or not group["decision"].strip()
                or not isinstance(group["registry_ids"], list) or not group["registry_ids"]):
            raise WorkbenchError("catalog_group")
        groups.add(group["id"])
        for registry_id in group["registry_ids"]:
            if not isinstance(registry_id, str) or not registry_id.strip() or registry_id in assigned:
                raise WorkbenchError("duplicate_or_invalid_registry_assignment")
            assigned.add(registry_id)
    return data


def selected(root: Path, role: str = "pilot") -> list[dict[str, Any]]:
    if role not in ENTRY_ROLES | {"all"}:
        raise WorkbenchError("unknown_role")
    return [{**entry, "material_present": (root / entry["path"]).is_file(), "runtime_verified": False}
            for entry in load_catalog(root)["entries"] if role == "all" or entry["role"] == role]


def validate_material(root: Path) -> dict[str, Any]:
    data = load_catalog(root)
    entries = selected(root, "all")
    missing = [entry["path"] for entry in entries if not entry["material_present"]]
    # Registry YAML stays the authority on existence, assets, licenses and status.
    # PyYAML is already a repository dependency; listing the catalog needs no YAML.
    try:
        import yaml
    except ImportError as exc:
        raise WorkbenchError("catalog_check_requires_existing_pyyaml_dependency") from exc
    try:
        registry = yaml.safe_load((root / "registry" / "registry.yaml").read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise WorkbenchError("invalid_registry_yaml") from exc
    if (not isinstance(registry, dict) or not isinstance(registry.get("entries"), list)
            or any(not isinstance(entry, dict) for entry in registry["entries"])):
        raise WorkbenchError("registry_contract")
    identifiers = [entry.get("id") for entry in registry["entries"] if isinstance(entry, dict)]
    if any(not isinstance(item, str) for item in identifiers) or len(identifiers) != len(set(identifiers)):
        raise WorkbenchError("registry_identifiers")
    known = set(identifiers)
    unknown = sorted(identifier for group in data["benchmark_groups"] for identifier in group["registry_ids"]
                     if identifier not in known)
    if missing or unknown:
        raise WorkbenchError(f"catalog_material_mismatch: missing={missing}; unknown_registry_ids={unknown}")
    return {"catalog_valid": True, "entries": len(entries), "runtime_verified": False,
            "note": "Material and role checks only; no tasks, models or solvers executed."}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--role", choices=sorted(ENTRY_ROLES | {"all"}), default="pilot")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--check", action="store_true", help="Validate paths and registry IDs, not runtime readiness")
    parser.add_argument("--research-policy", action="store_true", help="Show diagnostic/component/research disposition")
    args = parser.parse_args(argv)
    try:
        if args.check:
            result: Any = validate_material(args.root)
        elif args.research_policy:
            result = {key: load_catalog(args.root)[key] for key in ("default_benchmark_role", "benchmark_groups")}
        else:
            result = selected(args.root, args.role)
        if args.json or args.check or args.research_policy:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            for entry in result:
                print(f'{entry["id"]} [{entry["role"]} / {entry["kind"]}]\n'
                      f'  {entry["title"]} — {entry["purpose"]}\n'
                      f'  入口: {entry["path"]}\n  依赖: {entry["requires"]}\n  边界: {entry["limits"]}\n'
                      f'  材料存在: {entry["material_present"]}；运行环境尚未由 catalog 验证\n')
        return 0
    except (WorkbenchError, OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
