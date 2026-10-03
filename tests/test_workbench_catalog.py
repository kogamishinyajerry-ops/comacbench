"""The product view cannot turn research integration or file presence into readiness."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from comacbench import catalog
from comacbench.workbench import WorkbenchError, read_json

ROOT = Path(__file__).resolve().parents[1]


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "registry").mkdir()
        self.data = read_json(ROOT / "registry/product-scope.json")
        self.write(self.data)

    def write(self, data):
        (self.root / "registry/product-scope.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def material(self):
        # Synthetic file-presence fixtures, NOT copies of actual product packs.
        for entry in self.data["entries"]:
            path = self.root / entry["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture only\n", encoding="utf-8")
        ids = [item for group in self.data["benchmark_groups"] for item in group["registry_ids"]]
        (self.root / "registry/registry.yaml").write_text("entries:\n" + "".join(f"- id: {item}\n  status: integrated\n" for item in ids), encoding="utf-8")

    def test_default_pilot_is_file_level_workload_not_general_question_bank(self):
        rows = catalog.selected(self.root)
        self.assertEqual([row["id"] for row in rows], ["aviation-workload-starter-v1"])
        self.assertFalse(rows[0]["runtime_verified"])
        self.assertFalse(rows[0]["material_present"])

    def test_change_workbench_is_explicitly_experimental_and_not_a_pack(self):
        rows = catalog.selected(self.root, "experimental")
        self.assertEqual({r["id"] for r in rows}, {"workload-change-v1", "structures-change-v1"})
        self.assertTrue(all(r["kind"] == "workbench" for r in rows))
        self.assertIn("非既有 pack", rows[0]["limits"])

    def test_onboarding_and_calibration_are_available_but_not_pilot_scores(self):
        self.assertEqual(len(catalog.selected(self.root, "onboarding")), 1)
        self.assertEqual(len(catalog.selected(self.root, "calibration")), 2)
        self.assertEqual(len(catalog.selected(self.root, "legacy")), 1)
        self.assertEqual(len(catalog.selected(self.root, "all")), 7)

    def test_generic_benchmarks_are_diagnostic_even_when_integrated(self):
        self.material()
        result = catalog.validate_material(self.root)
        self.assertTrue(result["catalog_valid"])
        self.assertFalse(result["runtime_verified"])
        group = next(group for group in catalog.load_catalog(self.root)["benchmark_groups"] if group["id"] == "general-diagnostics")
        self.assertEqual(group["role"], "diagnostic")
        self.assertIn("gsm8k.math_reasoning", group["registry_ids"])
        self.assertEqual(catalog.load_catalog(self.root)["default_benchmark_role"], "research")

    def test_unknown_role_is_not_silently_defaulted(self):
        with self.assertRaisesRegex(WorkbenchError, "unknown_role"):
            catalog.selected(self.root, "ready")

    def test_duplicate_entry_ids_are_rejected(self):
        self.data["entries"].append(deepcopy(self.data["entries"][0]))
        self.write(self.data)
        with self.assertRaises(WorkbenchError):
            catalog.load_catalog(self.root)

    def test_path_traversal_absolute_and_windows_paths_are_rejected(self):
        for bad in ["../secrets", "/absolute", "packs/../secret/pack.yaml", "C:/pack.yaml", "packs\\x\\pack.yaml"]:
            data = deepcopy(self.data)
            data["entries"][0]["path"] = bad
            self.write(data)
            with self.subTest(path=bad), self.assertRaises(WorkbenchError):
                catalog.load_catalog(self.root)

    def test_duplicate_registry_assignments_are_rejected(self):
        self.data["benchmark_groups"][1]["registry_ids"].append(self.data["benchmark_groups"][0]["registry_ids"][0])
        self.write(self.data)
        with self.assertRaisesRegex(WorkbenchError, "registry_assignment"):
            catalog.load_catalog(self.root)

    def test_unknown_registry_assignment_fails_material_check(self):
        self.material()
        self.data["benchmark_groups"][0]["registry_ids"].append("invented.benchmark")
        self.write(self.data)
        with self.assertRaisesRegex(WorkbenchError, "unknown_registry_ids"):
            catalog.validate_material(self.root)

    def test_missing_pack_is_not_runtime_success(self):
        self.material()
        (self.root / self.data["entries"][0]["path"]).unlink()
        self.assertFalse(catalog.selected(self.root)[0]["material_present"])
        with self.assertRaisesRegex(WorkbenchError, "missing="):
            catalog.validate_material(self.root)

    def test_kind_path_mismatch_is_rejected(self):
        self.data["entries"][0]["kind"] = "workbench"
        self.write(self.data)
        with self.assertRaisesRegex(WorkbenchError, "kind_path"):
            catalog.load_catalog(self.root)

    def test_invalid_registry_yaml_reports_a_material_error(self):
        self.material()
        (self.root / "registry/registry.yaml").write_text("entries: [", encoding="utf-8")
        with self.assertRaisesRegex(WorkbenchError, "invalid_registry_yaml"):
            catalog.validate_material(self.root)

    def test_cli_defaults_to_pilot_and_reports_missing_material_honestly(self):
        process = subprocess.run([sys.executable, "-m", "comacbench.catalog", "--root", str(self.root), "--json"],
                                 cwd=ROOT, capture_output=True, text=True, timeout=20)
        self.assertEqual(process.returncode, 0, process.stderr)
        rows = json.loads(process.stdout)
        self.assertEqual(len(rows), 1)
        self.assertFalse(rows[0]["material_present"])
        process = subprocess.run([sys.executable, "-m", "comacbench.catalog", "--root", str(self.root), "--check"],
                                 cwd=ROOT, capture_output=True, text=True, timeout=20)
        self.assertEqual(process.returncode, 2)


if __name__ == "__main__":
    unittest.main()
