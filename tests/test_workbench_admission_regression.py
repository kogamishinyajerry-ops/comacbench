"""Reviewer regression tests: synthetic host logs, no DSH/model/native solver.

Run against bundled source or the local repository:
  COMACBENCH_REVIEW_SOURCE=/path/to/comacbench python regression_admission.py -v
Expected at reviewed HEAD 640a4b86: 2 pass / 5 assertion failures.
After the requested fixes, all 7 must pass (update fixture shape for new audit
contracts without weakening any negative assertion).
"""
from __future__ import annotations
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent
sys.path[:0] = [str(SOURCE), str(SOURCE / 'tests')]
import test_workbench_public as fixtures
from comacbench.workbench_admission import audit_trial


class AdmissionCloseoutRegression(unittest.TestCase):
    def setUp(self):
        fixture = fixtures.PublicBoundaryTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.data, self.directory = fixture.audit_fixture()

    def rows(self, name):
        return [json.loads(line) for line in (self.directory / name).read_text(encoding='utf-8').splitlines()]

    def write_rows(self, name, values):
        if name == 'boundary.jsonl':
            values = [dict(value, seq=i + 1) for i, value in enumerate(values)]
        (self.directory / name).write_text(''.join(json.dumps(value) + '\n' for value in values), encoding='utf-8')

    def second_call(self, *, duplicate_broker=False, private_response=False):
        host = self.rows('boundary.jsonl')
        model = self.rows('dsh-events.jsonl')
        broker = deepcopy(next(row for row in host if row['type'] == 'broker'))
        host_result = deepcopy(next(row for row in host if row['type'] == 'tool_result'))
        call = deepcopy(next(row for row in model if row['type'] == 'tool_call'))
        result = deepcopy(next(row for row in model if row['type'] == 'tool_result'))
        host_result['call_id'] = call['callId'] = result['callId'] = 'call-2'
        broker['call_id'] = 'call-1' if duplicate_broker else 'call-2'
        if private_response:
            output = json.loads(result['result'])
            output['manifest'] = {'future_requirement': 'REVIEWER SYNTHETIC REFERENCE'}
            result['result'] = json.dumps(output)
            host_result['content'][0]['text'] = result['result']
            if not duplicate_broker:
                broker['stdout'] = result['result']
        host.extend([broker, host_result])
        model[-2:-2] = [call, result]
        self.write_rows('boundary.jsonl', host)
        self.write_rows('dsh-events.jsonl', model)

    def assert_denied(self):
        result = audit_trial(self.data, self.directory)
        self.assertFalse(result['score_admissible'], 'Incorrectly admitted: ' + json.dumps(result, ensure_ascii=False))

    def test_valid_distinct_brokers_are_accepted(self):
        self.second_call()
        self.assertTrue(audit_trial(self.data, self.directory)['score_admissible'])

    def test_missing_broker_is_denied(self):
        self.write_rows('boundary.jsonl', [r for r in self.rows('boundary.jsonl') if r['type'] != 'broker'])
        self.assert_denied()

    def test_duplicate_broker_cannot_replace_missing_call(self):
        self.second_call(duplicate_broker=True)
        self.assert_denied()

    def test_duplicate_broker_cannot_hide_private_response(self):
        self.second_call(duplicate_broker=True, private_response=True)
        self.assert_denied()

    def test_runtime_prompt_digest_drift_is_denied(self):
        rows = self.rows('boundary.jsonl')
        for row in rows:
            if row['type'] == 'assembly':
                row['public_system_sha256'] = '0' * 64
                row['number'] = 1
        self.write_rows('boundary.jsonl', rows)
        self.assert_denied()

    def test_duplicate_json_exit_key_is_denied(self):
        (self.directory / 'execution.json').write_text(
            '{"exit_code":1,"exit_code":0,"attempt_count":1,"model_or_tool_overrides":"boundary_only"}', encoding='utf-8')
        self.assert_denied()

    def test_private_field_nested_in_observation_is_denied(self):
        rows = self.rows('boundary.jsonl')
        stream = self.rows('dsh-events.jsonl')
        value = json.loads(next(r for r in rows if r['type'] == 'broker')['stdout'])
        value['observation']['manifest'] = {'future_requirement': 'REVIEWER SYNTHETIC REFERENCE'}
        output = json.dumps(value)
        for row in rows:
            if row['type'] == 'broker':
                row['stdout'] = output
            if row['type'] == 'tool_result':
                row['content'][0]['text'] = output
        for row in stream:
            if row['type'] == 'tool_result':
                row['result'] = output
        self.write_rows('boundary.jsonl', rows)
        self.write_rows('dsh-events.jsonl', stream)
        self.assert_denied()


if __name__ == '__main__':
    unittest.main()
