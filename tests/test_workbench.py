"""Executable contract, change semantics, and negative controls for the workbench."""
from copy import deepcopy
import importlib.util
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from comacbench import workbench as wb
from comacbench import workbench_review as reviewer
from comacbench.workbench_report import export_report

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "examples/workbench/workload-change-v1.json"
spec = importlib.util.spec_from_file_location("workbench_reference", ROOT / "examples/workbench/reference_policy.py")
reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reference)


class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.session = self.root / "session"
        self.scenario = wb.read_json(SCENARIO)
        self.subject = {"name": "test-reference", "revision": "1", "kind": "reference"}
        wb.start(self.session, self.scenario, self.subject)

    def view(self):
        return wb.observe(self.session)

    def act(self, action):
        return wb.act(self.session, action)["result"]

    def put(self, target, payload=None, basis=None):
        obs = self.view()
        return self.act({"op": "put", "target": target,
                         "basis": obs["dependencies"][target] if basis is None else basis,
                         "payload": reference.payload(obs, target) if payload is None else payload})

    def check(self, target):
        return self.act({"op": "check", "target": target})

    def repair(self):
        reference.repair_phase(self.session)

    def last_path(self):
        return sorted((self.session / "events").glob("*.json"))[-1]

    def rewrite_last(self, mutate):
        path = self.last_path()
        event = wb.read_json(path)
        mutate(event)
        path.write_bytes(wb.canonical(event))

    def test_reference_completes_three_phases_with_exact_action_accounting(self):
        reference.complete(self.session)
        obs = self.view()
        self.assertTrue(obs["complete"])
        self.assertEqual(obs["actions_used"], 25)
        self.assertEqual(obs["counts"], {"put": 11, "check": 11, "advance": 2, "submit": 1})
        self.assertTrue(all(value == "verified" for value in obs["statuses"].values()))
        self.assertEqual(obs["artifacts"]["review"]["payload"]["claim"], "needs_review")
        self.assertEqual(obs["limitations"]["solver_execution"], "not_performed")
        self.assertFalse(obs["limitations"]["publishable"])

    def test_condition_change_invalidates_only_affected_descendants(self):
        self.repair()
        old = deepcopy(self.view()["artifacts"]["normalized_ground"])
        result = self.act({"op": "advance"})
        self.assertEqual(result["invalidated"], ["normalized_cruise", "normalized_reserve", "run_plan", "review"])
        self.assertEqual(result["retained"], ["normalized_ground"])
        self.assertEqual(self.view()["artifacts"]["normalized_ground"], old)

    def test_program_change_retains_all_normalized_evidence(self):
        self.repair()
        self.act({"op": "advance"})
        self.repair()
        result = self.act({"op": "advance"})
        self.assertEqual(result["invalidated"], ["run_plan", "review"])
        self.assertEqual(result["retained"], ["normalized_cruise", "normalized_ground", "normalized_reserve"])

    def test_revision_label_alone_cannot_mask_a_content_change(self):
        scenario = deepcopy(self.scenario)
        scenario["phases"] = scenario["phases"][:2]
        scenario["phases"][1]["changes"] = {"condition_ground": deepcopy(scenario["conditions"]["ground"])}
        scenario["phases"][1]["changes"]["condition_ground"]["rows"][0]["altitude"]["value"] = 123
        other = self.root / "same-label"
        wb.start(other, scenario, self.subject)
        reference.repair_phase(other)
        result = wb.act(other, {"op": "advance"})["result"]
        self.assertIn("normalized_ground", result["invalidated"])
        self.assertIn("normalized_cruise", result["retained"])

    def test_note_only_change_keeps_all_checks(self):
        scenario = deepcopy(self.scenario)
        scenario["phases"] = scenario["phases"][:2]
        scenario["phases"][1]["changes"] = {"note": {"text": "Editorial correction only"}}
        other = self.root / "note-only"
        wb.start(other, scenario, self.subject)
        reference.repair_phase(other)
        result = wb.act(other, {"op": "advance"})["result"]
        self.assertEqual(result["invalidated"], [])
        self.assertEqual(len(result["retained"]), 5)

    def test_baseline_cannot_skip_mandatory_changes(self):
        self.repair()
        result = self.act({"op": "submit", "claim": "ready_for_execution"})
        self.assertEqual(result["code"], "mandatory_changes_remaining")
        self.assertFalse(self.view()["complete"])

    def test_missing_artifacts_block_advance(self):
        result = self.act({"op": "advance"})
        self.assertEqual(result["code"], "unverified_targets")
        self.assertEqual(len(result["targets"]), 5)

    def test_old_result_cannot_be_submitted_after_change(self):
        reference.complete(self.session, negative="stale")
        self.assertFalse(self.view()["complete"])
        self.assertEqual(wb.read_json(self.last_path())["result"]["code"], "unverified_targets")

    def test_false_ready_claim_is_retained_and_can_be_corrected(self):
        reference.complete(self.session, negative="false-ready")
        before = self.view()["actions_used"]
        self.assertEqual(self.view()["counts"]["rejected"], 1)
        result = self.act({"op": "submit", "claim": "needs_review"})
        self.assertTrue(result["ok"])
        self.assertEqual(self.view()["actions_used"], before + 1)
        self.assertEqual(self.view()["counts"]["rejected"], 1)

    def test_forged_current_content_with_stale_basis_fails(self):
        self.repair()
        old_basis = self.view()["dependencies"]["normalized_cruise"]
        self.act({"op": "advance"})
        self.put("normalized_cruise", basis=old_basis)
        self.assertEqual(self.check("normalized_cruise")["code"], "missing_or_stale_evidence")

    def test_current_basis_does_not_make_wrong_old_values_correct(self):
        self.repair()
        old_payload = self.view()["artifacts"]["normalized_cruise"]["payload"]
        self.act({"op": "advance"})
        old_payload["source_revision"] = "B"
        self.put("normalized_cruise", payload=old_payload)
        self.assertEqual(self.check("normalized_cruise")["code"], "content_review_failed")

    def test_child_requires_verified_not_merely_present_parents(self):
        for node in ["normalized_cruise", "normalized_ground", "normalized_reserve"]:
            self.put(node)
        self.put("run_plan")
        result = self.check("run_plan")
        self.assertEqual(result["code"], "missing_or_stale_evidence")

    def test_replacing_parent_invalidates_existing_child_checks(self):
        self.repair()
        self.put("normalized_ground", payload={"point": "wrong"})
        self.assertEqual(self.view()["statuses"]["run_plan"], "stale")
        self.assertFalse(self.check("normalized_ground")["ok"])
        self.assertFalse(self.check("review")["ok"])

    def test_failed_content_review_and_repair_are_both_counted(self):
        self.put("normalized_ground", payload={"point": "wrong"})
        self.assertFalse(self.check("normalized_ground")["ok"])
        self.put("normalized_ground")
        self.assertTrue(self.check("normalized_ground")["ok"])
        self.assertEqual(self.view()["actions_used"], 4)
        self.assertEqual(self.view()["counts"]["rejected"], 1)
        self.assertEqual(len(list((self.session / "events").iterdir())), 4)

    def test_unhashable_and_unknown_actions_are_counted_rejections(self):
        actions = [None, [], True, {"op": []}, {"op": {}}, {"op": "unknown"},
                   {"op": "put", "target": [], "basis": {}, "payload": {}},
                   {"op": "check", "target": "missing"}, {"op": "advance", "extra": 1}]
        for action in actions:
            with self.subTest(action=action):
                self.assertFalse(self.act(action)["ok"])
        self.assertEqual(self.view()["actions_used"], len(actions))
        self.assertEqual(self.view()["counts"]["rejected"], len(actions))

    def test_basis_must_name_every_dependency_exactly(self):
        for basis in [{}, {"condition_ground": "bad"}, {"condition_ground": "a" * 64, "extra": None}]:
            with self.subTest(basis=basis):
                result = self.put("normalized_ground", basis=basis)
                self.assertEqual(result["code"], "basis_contract")

    def test_budget_is_global_across_failures_and_resume(self):
        scenario = deepcopy(self.scenario)
        scenario["max_actions"] = 2
        other = self.root / "budget"
        wb.start(other, scenario, self.subject)
        for _ in range(2):
            self.assertFalse(wb.act(other, {"op": "bad"})["result"]["ok"])
        with self.assertRaisesRegex(wb.WorkbenchError, "action_budget_exhausted"):
            wb.act(other, {"op": "advance"})
        self.assertEqual(wb.observe(other)["actions_remaining"], 0)
        self.assertEqual(len(wb.snapshot(other)["events"]), 2)

    def test_observe_and_report_do_not_spend_actions(self):
        self.put("normalized_ground")
        before = self.view()["actions_used"]
        self.view()
        result = export_report(self.session, self.root / "report")
        self.assertFalse(result["complete"])
        self.assertEqual(self.view()["actions_used"], before)

    def test_complete_session_is_not_reopened(self):
        reference.complete(self.session)
        with self.assertRaisesRegex(wb.WorkbenchError, "already_complete"):
            self.act({"op": "advance"})
        with self.assertRaises(FileExistsError):
            wb.start(self.session, self.scenario, self.subject)

    def test_engine_change_prevents_silent_resume(self):
        with patch.object(wb, "engine_identity", return_value="b" * 64):
            with self.assertRaisesRegex(wb.WorkbenchError, "engine_changed"):
                self.view()

    def test_forged_check_verdict_is_recomputed(self):
        self.put("normalized_ground", payload={"point": "bad"})
        self.check("normalized_ground")
        self.rewrite_last(lambda event: event["result"].update(ok=True, code="content_verified"))
        with self.assertRaisesRegex(wb.WorkbenchError, "event_result_mismatch"):
            self.view()

    def test_changed_action_payload_is_not_trusted(self):
        self.put("normalized_ground")
        self.rewrite_last(lambda event: event["action"]["payload"].update(altitude_m=123))
        with self.assertRaisesRegex(wb.WorkbenchError, "event_result_mismatch"):
            self.view()

    def test_event_chain_and_sequence_are_checked(self):
        self.put("normalized_ground")
        self.rewrite_last(lambda event: event.update(previous_sha256="b" * 64))
        with self.assertRaisesRegex(wb.WorkbenchError, "event_chain_mismatch"):
            self.view()

    def test_boolean_sequence_is_rejected(self):
        self.put("normalized_ground")
        self.rewrite_last(lambda event: event.update(seq=True))
        with self.assertRaisesRegex(wb.WorkbenchError, "event_chain_mismatch"):
            self.view()

    def test_deleted_middle_event_is_not_treated_as_no_failure(self):
        self.put("normalized_ground")
        self.check("normalized_ground")
        (self.session / "events/000001.json").unlink()
        with self.assertRaisesRegex(wb.WorkbenchError, "event_gap"):
            self.view()

    def test_unregistered_event_file_blocks_report(self):
        (self.session / "events/best-result.json").write_text("{}")
        with self.assertRaisesRegex(wb.WorkbenchError, "unregistered_file"):
            export_report(self.session, self.root / "bad-report")
        self.assertFalse((self.root / "bad-report").exists())

    def test_partial_tail_is_not_silently_discarded(self):
        (self.session / "events/000001.json").write_text('{"seq":')
        with self.assertRaisesRegex(wb.WorkbenchError, "invalid_json"):
            self.view()

    def test_changed_scenario_envelope_is_rejected(self):
        path = self.session / "session.json"
        data = wb.read_json(path)
        data["scenario"]["max_actions"] = 100
        path.write_bytes(wb.canonical(data))
        with self.assertRaisesRegex(wb.WorkbenchError, "manifest_changed"):
            self.view()

    def test_busy_writer_is_not_unlocked_by_reader(self):
        lock = self.session / ".writer.lock"
        lock.write_text("another writer")
        with self.assertRaisesRegex(wb.WorkbenchError, "session_locked"):
            self.view()
        self.assertTrue(lock.exists())

    def test_symlink_event_is_rejected(self):
        destination = self.root / "outside.json"
        destination.write_text("{}")
        try:
            (self.session / "events/000001.json").symlink_to(destination)
        except OSError:
            self.skipTest("native symlink creation is not permitted")
        with self.assertRaisesRegex(wb.WorkbenchError, "link_or_special_file"):
            self.view()

    def test_nonfinite_duplicate_and_oversized_json_fail_before_mutation(self):
        for text in ['{"x":NaN}', '{"x":Infinity}', '{"x":1e999}', '{"x":1,"x":2}']:
            with self.subTest(text=text), self.assertRaises(wb.WorkbenchError):
                wb.loads(text)
        with self.assertRaisesRegex(wb.WorkbenchError, "action_too_large"):
            self.act({"op": "bad", "data": "x" * wb.MAX_ACTION_BYTES})
        self.assertEqual(self.view()["actions_used"], 0)

    def test_report_refuses_inside_session_and_existing_destination(self):
        with self.assertRaisesRegex(wb.WorkbenchError, "outside_session"):
            export_report(self.session, self.session / "report")
        export_report(self.session, self.root / "report")
        with self.assertRaises(FileExistsError):
            export_report(self.session, self.root / "report")

    def test_report_escapes_untrusted_labels_and_marks_reference_scope(self):
        scenario = deepcopy(self.scenario)
        scenario["title"] = '<script>alert("bad")</script>'
        other = self.root / "html"
        wb.start(other, scenario, self.subject)
        export_report(other, self.root / "safe-report")
        text = (self.root / "safe-report/report.html").read_text(encoding="utf-8")
        self.assertNotIn('<script>alert', text)
        self.assertIn('&lt;script&gt;', text)
        self.assertIn('未调用模型', text)
        self.assertIn('default-src', text)
        self.assertNotIn('https://', text)

    def test_exported_artifact_bytes_and_lineage_match_replayed_trace(self):
        reference.complete(self.session)
        export_report(self.session, self.root / "delivery")
        manifest = wb.read_json(self.root / "delivery/artifacts/manifest.json")
        self.assertTrue(manifest["complete"])
        html = (self.root / "delivery/report.html").read_text(encoding="utf-8")
        self.assertIn("仍需澄清或审查", html)
        self.assertIn("reserve (missing_unit)", html)
        self.assertEqual(len(manifest["artifacts"]), 5)
        observation = self.view()
        for entry in manifest["artifacts"]:
            path = self.root / "delivery/artifacts" / entry["path"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), entry["sha256"])
            self.assertEqual(wb.read_json(path), observation["artifacts"][entry["target"]]["payload"])
            self.assertEqual(entry["basis"], observation["dependencies"][entry["target"]])
            self.assertEqual(entry["status"], "verified")

    def test_export_keeps_stale_artifacts_explicitly_marked(self):
        self.repair()
        self.act({"op": "advance"})
        export_report(self.session, self.root / "stale-delivery")
        manifest = wb.read_json(self.root / "stale-delivery/artifacts/manifest.json")
        statuses = {row["target"]: row["status"] for row in manifest["artifacts"]}
        self.assertEqual(statuses["normalized_ground"], "verified")
        self.assertEqual(statuses["run_plan"], "stale")
        self.assertFalse(manifest["complete"])
        html = (self.root / "stale-delivery/report.html").read_text(encoding="utf-8")
        self.assertIn("当前报告尚未通过有效版本检查", html)

    def test_cli_action_rejection_returns_one_and_material_error_returns_two(self):
        action = self.root / "action.json"
        action.write_text('{"op":"advance"}')
        result = subprocess.run([sys.executable, "-m", "comacbench.workbench", "act", str(self.session),
                                 "--action-file", str(action)], cwd=ROOT, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(result.stdout)["result"]["code"], "unverified_targets")
        action.write_text('{"op":')
        result = subprocess.run([sys.executable, "-m", "comacbench.workbench", "act", str(self.session),
                                 "--action-file", str(action)], cwd=ROOT, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.view()["actions_used"], 1)

    def test_cli_start_observe_and_report_work_from_source_workspace(self):
        other = self.root / "cli-session"
        commands = [
            ["start", str(SCENARIO), "--out", str(other), "--subject", "cli-test", "--revision", "1", "--kind", "reference"],
            ["observe", str(other)], ["report", str(other), "--out", str(self.root / "cli-report")],
        ]
        for command in commands:
            proc = subprocess.run([sys.executable, "-m", "comacbench.workbench", *command], cwd=ROOT,
                                  capture_output=True, text=True, timeout=20)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIsInstance(json.loads(proc.stdout), dict)
        self.assertTrue((self.root / "cli-report/report.html").is_file())


class SemanticReviewTests(unittest.TestCase):
    def setUp(self):
        self.scenario = wb.read_json(SCENARIO)
        self.sources = {f"condition_{key}": deepcopy(value) for key, value in self.scenario["conditions"].items()}
        self.sources.update(program=self.scenario["program"], note=self.scenario["note"])

    def accepts(self, target, payload):
        return all(check["passed"] for check in reviewer.review(self.scenario, self.sources, target, payload))

    def test_known_feet_and_pounds_case_has_independent_numerical_answer(self):
        payload = {"point": "cruise", "case_id": "SYNTH-01", "source_revision": "A", "status": "accepted",
                   "altitude_m": 3048.0, "mass_flow_kg_s": 0.90718474}
        self.assertTrue(self.accepts("normalized_cruise", payload))
        payload["altitude_m"] = 10000
        self.assertFalse(self.accepts("normalized_cruise", payload))

    def test_boolean_numeric_and_wrong_revision_fail(self):
        payload = {"point": "ground", "case_id": "SYNTH-01", "source_revision": "A", "status": "accepted",
                   "altitude_m": 0, "mass_flow_kg_s": 1.2}
        for field, value in [("altitude_m", False), ("source_revision", "B"), ("mass_flow_kg_s", 10**400)]:
            wrong = {**payload, field: value}
            self.assertFalse(self.accepts("normalized_ground", wrong))

    def test_duplicate_even_identical_rows_require_review(self):
        condition = self.sources["condition_ground"]
        condition["rows"].append(deepcopy(condition["rows"][0]))
        payload = {"point": "ground", "case_id": "SYNTH-01", "source_revision": "A",
                   "status": "needs_review", "reason_code": "conflict"}
        self.assertTrue(self.accepts("normalized_ground", payload))
        self.assertFalse(self.accepts("normalized_ground", {**payload, "reason_code": "missing_unit"}))

    def test_missing_unsupported_and_invalid_values_are_distinguished(self):
        variants = [(None, "missing_unit"), ({"value": 10, "unit": "km"}, "unsupported_unit"),
                    ({"value": True, "unit": "m"}, "invalid_value"),
                    ({"value": 10**400, "unit": "m"}, "invalid_value")]
        for quantity, reason in variants:
            with self.subTest(reason=reason, quantity=quantity):
                self.sources["condition_ground"]["rows"][0]["altitude"] = quantity
                payload = {"point": "ground", "case_id": "SYNTH-01", "source_revision": "A",
                           "status": "needs_review", "reason_code": reason}
                self.assertTrue(self.accepts("normalized_ground", payload))

    def test_absent_record_cannot_disappear_from_review(self):
        self.sources["condition_ground"]["rows"] = []
        payload = {"point": "ground", "case_id": "SYNTH-01", "source_revision": "A",
                   "status": "needs_review", "reason_code": "missing_record"}
        self.assertTrue(self.accepts("normalized_ground", payload))

    def test_plan_order_is_flexible_but_duplicates_and_omissions_fail(self):
        obs = {"sources": self.sources}
        payload = reference.payload(obs, "run_plan")
        payload["runs"].reverse()
        self.assertTrue(self.accepts("run_plan", payload))
        payload["runs"][0] = deepcopy(payload["runs"][1])
        self.assertFalse(self.accepts("run_plan", payload))
        payload["runs"].pop()
        self.assertFalse(self.accepts("run_plan", payload))

    def test_solver_execution_and_extra_success_flags_cannot_be_fabricated(self):
        payload = reference.payload({"sources": self.sources}, "review")
        self.assertTrue(self.accepts("review", payload))
        self.assertFalse(self.accepts("review", {**payload, "solver_execution": "passed"}))
        self.assertFalse(self.accepts("review", {**payload, "passed": True}))

    def test_non_object_submission_is_a_failed_check_not_a_crash(self):
        for value in [None, [], True, 123, "answer"]:
            with self.subTest(value=value):
                self.assertFalse(self.accepts("normalized_ground", value))

    def test_public_reference_does_not_import_evaluator(self):
        text = (ROOT / "examples/workbench/reference_policy.py").read_text(encoding="utf-8")
        self.assertNotIn("import workbench_review", text)
        self.assertNotIn("_expectation", text)


class ScenarioContractTests(unittest.TestCase):
    def test_invalid_scenarios_fail_before_creating_a_session(self):
        original = wb.read_json(SCENARIO)
        mutations = [lambda s: s.update(max_actions=True), lambda s: s.update(max_actions=0),
                     lambda s: s.update(protocol="other"), lambda s: s.update(conditions={}),
                     lambda s: s["phases"][1]["changes"].update(unknown={}),
                     lambda s: s["phases"][0]["changes"].update(note={"text": "bad"}),
                     lambda s: s["phases"][1].update(id="baseline"),
                     lambda s: s["conditions"]["ground"].update(rows=[None])]
        for mutate in mutations:
            scenario = deepcopy(original)
            mutate(scenario)
            with self.subTest(scenario=scenario), self.assertRaises(wb.WorkbenchError):
                wb.validate_scenario(scenario)

    def test_bad_subject_kind_is_reported_without_type_error(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "session"
            with self.assertRaises(wb.WorkbenchError):
                wb.start(destination, wb.read_json(SCENARIO), {"name": "a", "revision": "b", "kind": []})
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
