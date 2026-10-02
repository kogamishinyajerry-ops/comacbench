"""Boundary/admission control tests. Process doubles here are never FEA evidence."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest
from unittest import mock

import test_workbench_native as native_fixtures
from comacbench import workbench as wb
from comacbench import workbench_ccx as ccx
from comacbench.workbench_public import dispatch, public_observation
from comacbench.workbench_admission import audit_trial, unknown_admission, CONTRACT_SHA256, _digest
from comacbench.workbench_report import export_report, render

ROOT = Path(__file__).resolve().parents[1]


class PublicBoundaryTests(unittest.TestCase):
    setUp = native_fixtures.NativeBridgeTests.setUp

    def start(self):
        return wb.start(self.session, self.scenario, {"name": "TEST DOUBLE", "revision": "1", "kind": "user_agent"})

    def test_future_inputs_and_reference_not_projected(self):
        original = self.start()
        value = public_observation(original)
        self.assertNotIn("remaining_phases", value)
        self.assertNotIn("phase_index", value)
        self.assertNotIn("manifest", value)
        text = json.dumps(value)
        for secret in ("requirement-b", "load-b", "0.45", "15 actions", "3 solves"):
            self.assertNotIn(secret, text)
        self.assertEqual(value["sources"]["requirement"]["max_tip_mm"], 0.6)
        self.assertEqual(original["remaining_phases"], 2)
        self.assertEqual(set(value["contract"]["fields"]), {"observe", "solve", "check", "put", "advance", "submit", "read_native"})

    def test_request_paths_denied_before_session_access(self):
        with mock.patch.object(wb, "observe", side_effect=AssertionError("must not read")):
            for request in ({"op": "observe", "session": "../other"}, {"op": "read", "path": "session/session.json"},
                            {"op": "observe", "path": "/etc/passwd"}, {"op": ["observe"]}, None):
                self.assertEqual(dispatch(self.session, request)["result"]["code"], "public_request_denied")

    def test_internal_reference_neighbors_and_traversal_are_denied(self):
        self.start()
        for name in ("../../session.json", "../tests/test_workbench_native.py", "/etc/passwd",
                     "../scripts/native_reference.py", "../docs/native-calibration-handoff.md", "../neighbor/report.json", "receipt.json"):
            value = dispatch(self.session, {"op": "read_native", "target": "solution_limit", "name": name})
            self.assertEqual(value["result"]["code"], "public_file_denied")
        self.assertEqual(dispatch(self.session, {"op": "solve", "target": "../other"})["result"]["code"], "public_target_denied")
        self.assertEqual(wb.observe(self.session)["actions_used"], 0)
        self.process.assert_not_called()

    def test_current_native_text_only_and_no_read_budget(self):
        self.start()
        self.assertTrue(dispatch(self.session, {"op": "solve", "target": "solution_limit"})["result"]["ok"])
        result = dispatch(self.session, {"op": "read_native", "target": "solution_limit", "name": "model.dat"})
        self.assertEqual(result["result"]["code"], "native_text")
        self.assertIn("displacements", result["result"]["text"])
        self.assertEqual(wb.observe(self.session)["actions_used"], 1)
        self.assertEqual(self.process.call_count, 1)

    def test_archive_errors_do_not_leak_paths(self):
        with mock.patch.object(wb, "observe", side_effect=wb.WorkbenchError("/private/secret.json: invalid")):
            self.assertEqual(dispatch(self.session, {"op": "observe"})["result"]["detail"], "internal_archive_error")

    def test_default_report_unknown_and_old_data_unchanged(self):
        self.start()
        before = wb.snapshot(self.session)
        export_report(self.session, self.root / "report")
        after = wb.snapshot(self.session)
        self.assertEqual(before, after)
        data = json.loads((self.root / "report/report.json").read_text())
        self.assertEqual(data["protocol_conformance"], "unknown")
        self.assertFalse(data["score_admissible"])
        html = (self.root / "report/report.html").read_text()
        self.assertLess(html.index('id="score-admission"'), html.index('class="metrics"'))
        self.assertIn("冻结场景原始说明", html)
        self.assertIn("不修改历史分数", html)

    def audit_fixture(self):
        self.start()
        data = wb.snapshot(self.session)
        manifest = data["manifest"]
        audit = self.root / "audit"; audit.mkdir()
        model = {"provider": "zai-coding-cn", "model": "glm-4.7"}
        sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
        control = {"protocol": "comacbench.public-boundary.v2", "session_manifest_sha256": manifest["manifest_sha256"],
            "engine_sha256": manifest["engine_sha256"], "plugin_sha256": sha(ROOT / "scripts/dsh_public_boundary.mjs"),
            "gateway_sha256": sha(ROOT / "comacbench/workbench_public.py"),
            "budget": {"actions": 32, "solver_calls": 6, "solve_timeout_s": 120, "tool_calls": 96, "model_assemblies": 64},
            "model": model, "fresh_headless_session": True, "creation_source": "startup", "runtime_context_suppressed": True,
            "mode": "native", "task_scope": "same_public_task_development_repeat", "prior_public_task_exposure": True, "public_observe_success": True,
            "probe": {"all_denied": True, "schemas": ["workbench"], "probes": [{"is_error": True}] * 9}, "agent_id": "test", "complete_public_system": "fixture"}
        contract = json.loads((ROOT / 'comacbench/public_input_v2.json').read_text())
        control.update(contract_version=contract['version'], contract_sha256=CONTRACT_SHA256,
                       complete_public_system=contract['sections'][0]['text'], public_user_entry=contract['user_entry'], runtime=contract['runtime'])
        assembled = {k:contract[k] for k in ('sections','contexts','tools')}
        messages = [{'role':'system', 'content':[{'type':'text','text':contract['sections'][0]['text']}]},
                    {'role':'user','content':[{'type':'text','text':contract['user_entry']}]}]
        actual = {'messages':messages,'tools':contract['tools']}
        request = {"op": "observe"}; args = {"request": request}
        output = json.dumps(dispatch(self.session, request))
        rows = [{"type": "ready"}, {"type": "assembly", "schemas": ["workbench"], **assembled, "model": model,
                "number":1, "contract_version":contract['version'], "contract_sha256":CONTRACT_SHA256,
                "input_sha256":_digest(assembled), "public_system_sha256":hashlib.sha256(contract['sections'][0]['text'].encode()).hexdigest()},
            {"type": "prompt_probe", **deepcopy(assembled), "schemas": ["workbench"]},
            {"type": "assembly", "schemas": ["workbench"], **deepcopy(assembled), "model": model,
                "number":2, "contract_version":contract['version'], "contract_sha256":CONTRACT_SHA256,
                "input_sha256":_digest(assembled), "public_system_sha256":hashlib.sha256(contract['sections'][0]['text'].encode()).hexdigest()},
            {"type":"model_input", "number":1, "assembly_number":2, "model":model, **actual,
             "contract_version":contract['version'], "contract_sha256":CONTRACT_SHA256, "input_sha256":_digest(actual)},
            {"type": "broker", "call_id": "call-1", "request": request, "exit_code": 0, "stdout": output},
            {"type": "tool_result", "call_id": "call-1", "name": "workbench", "arguments": args,
             "is_error": False, "content": [{"type": "text", "text": output}]}]
        stream = [{"type": "session", "sessionId": "test"}, {"type":"status", "phase":"step_start", "turn":1, "step":1}, {"type": "tool_call", "callId": "call-1", "tool": "workbench", "input": args},
            {"type": "tool_result", "callId": "call-1", "result": output},
            {"type": "status", "phase": "turn_end", "reason": {"kind": "completed"}}, {"type": "final", "text": "self claim ignored"}]
        (audit / "control.json").write_text(json.dumps(control))
        (audit / "boundary.jsonl").write_text(''.join(json.dumps({"seq": i + 1, **r}) + '\n' for i, r in enumerate(rows)))
        (audit / "dsh-events.jsonl").write_text(''.join(json.dumps(r) + '\n' for r in stream))
        (audit / "execution.json").write_text(json.dumps({"exit_code": 0, "attempt_count": 1, "model_or_tool_overrides": "boundary_only"}))
        return data, audit

    def test_admission_requires_host_records_not_agent_self_claim(self):
        data, audit = self.audit_fixture()
        result = audit_trial(data, audit)
        self.assertTrue(result["score_admissible"], result)
        self.assertFalse(result["unseen_generalization_score_admissible"])
        (audit / "control.json").unlink()
        self.assertFalse(audit_trial(data, audit)["score_admissible"])

    def test_mismatched_session_model_budget_and_tool_records_fail_closed(self):
        data, audit = self.audit_fixture()
        original = (audit / "control.json").read_text()
        for field, value in (("session_manifest_sha256", "wrong"), ("gateway_sha256", "wrong"),
                             ("model", {"provider": "other", "model": "other"}), ("fresh_headless_session", False)):
            control = json.loads(original); control[field] = value
            (audit / "control.json").write_text(json.dumps(control))
            self.assertFalse(audit_trial(data, audit)["score_admissible"], field)
        (audit / "control.json").write_text(original)
        with (audit / "dsh-events.jsonl").open('a') as file:
            file.write(json.dumps({"type": "tool_call", "callId": "unlogged", "tool": "read", "input": {}}) + '\n')
        self.assertFalse(audit_trial(data, audit)["score_admissible"])

    def test_reference_never_admissible_and_reason_is_escaped(self):
        self.assertFalse(unknown_admission("reference")["score_admissible"])
        self.start(); data = wb.snapshot(self.session)
        data.update(unknown_admission(reason='<script>alert(1)</script>'))
        self.assertNotIn('<script>', render(data))

    def test_string_request_trace_fails_closed_without_crashing(self):
        data, audit = self.audit_fixture()
        control = json.loads((audit / "control.json").read_text())
        control.pop("public_observe_success")
        (audit / "control.json").write_text(json.dumps(control))
        rows = [json.loads(x) for x in (audit / "boundary.jsonl").read_text().splitlines()]
        stream = [json.loads(x) for x in (audit / "dsh-events.jsonl").read_text().splitlines()]
        request = '{"op":"observe"}'
        output = json.dumps({"result": {"ok": False, "code": "public_request_denied"}})
        for row in rows:
            if row["type"] == "broker": row.update(request=request, stdout=output)
            if row["type"] == "tool_result": row.update(arguments={"request": request}, content=[{"type": "text", "text": output}])
        for row in stream:
            if row["type"] == "tool_call": row["input"] = {"request": request}
            if row["type"] == "tool_result": row["result"] = output
        (audit / "boundary.jsonl").write_text(''.join(json.dumps(r) + '\n' for r in rows))
        (audit / "dsh-events.jsonl").write_text(''.join(json.dumps(r) + '\n' for r in stream))
        result = audit_trial(data, audit)
        self.assertFalse(result["score_admissible"])
        self.assertFalse(result["audit_checks"]["entry_contract_probed"])


if __name__ == '__main__':
    unittest.main()
