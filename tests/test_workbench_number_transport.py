"""Real Node JSON transport, synthetic v2 audit fixture, no DSH/model/solver.

The original tests echoed Python's JSON straight back as model output.  These
checks include the JSON.parse/JSON.stringify hop in the actual DSH plugin.
"""
import json
import math
from pathlib import Path
import shutil
import subprocess
import unittest

import test_workbench_public as public_fixtures
from comacbench.workbench_admission import audit_trial

NODE_SCRIPT = ("let s='';process.stdin.setEncoding('utf8');"
               "process.stdin.on('data',x=>s+=x);"
               "process.stdin.on('end',()=>process.stdout.write(JSON.stringify(JSON.parse(s))));")


class NumberTransportTests(unittest.TestCase):
    def setUp(self):
        self.fixture = public_fixtures.PublicBoundaryTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.data, self.audit = self.fixture.audit_fixture()
        self.rows = self._read('boundary.jsonl')
        self.stream = self._read('dsh-events.jsonl')

    def _read(self, name):
        return [json.loads(s) for s in (self.audit/name).read_text(encoding='utf-8').splitlines()]

    def roundtrip(self, *, change=None, rewrite_broker=False):
        node = shutil.which('node')
        if node is None:
            self.skipTest('real Node JSON transport requires an installed node executable')
        broker = next(r for r in self.rows if r['type'] == 'broker')
        original = broker['stdout']
        value = json.loads(original)
        if change is not None:
            change(value)
            broker['stdout'] = json.dumps(value)
        proc = subprocess.run([node, '-e', NODE_SCRIPT], input=broker['stdout'],
                              text=True, capture_output=True, check=True, timeout=10,
                              encoding='utf-8')
        actual = proc.stdout
        if rewrite_broker:
            broker['stdout'] = actual
        next(r for r in self.rows if r['type'] == 'tool_result')['content'][0]['text'] = actual
        next(r for r in self.stream if r['type'] == 'tool_result')['result'] = actual
        self.save()
        return original, actual

    def save(self):
        for name, rows in [('boundary.jsonl', self.rows), ('dsh-events.jsonl', self.stream)]:
            (self.audit/name).write_text(''.join(json.dumps(r)+'\n' for r in rows), encoding='utf-8')

    def decision(self):
        return audit_trial(self.data, self.audit, session=self.fixture.session)

    def test_real_node_number_roundtrip_is_admitted(self):
        original, actual = self.roundtrip()
        before = json.loads(original)['observation']['sources']['load_service']['force_y_n']
        after = json.loads(actual)['observation']['sources']['load_service']['force_y_n']
        self.assertIs(type(before), float)
        self.assertIs(type(after), int)
        self.assertEqual(before, after)
        result = self.decision()
        self.assertTrue(result['score_admissible'], result)

    def test_node_numbers_match_current_public_projection(self):
        # Also covers the independent current-state check, not just broker text.
        self.roundtrip(rewrite_broker=True)
        result = self.decision()
        self.assertTrue(result['score_admissible'], result)

    def test_actual_numeric_change_is_still_rejected(self):
        self.roundtrip(change=lambda v: v['observation']['sources']['load_service'].update(force_y_n=-99))
        self.assertFalse(self.decision()['score_admissible'])

    def test_adjacent_float_change_is_not_tolerated(self):
        self.roundtrip(change=lambda v: v['observation']['sources']['load_service'].update(force_y_n=math.nextafter(-100., 0.)))
        self.assertFalse(self.decision()['score_admissible'])

    def test_boolean_is_not_a_number(self):
        self.roundtrip(change=lambda v: v['observation'].update(complete=0))
        self.assertFalse(self.decision()['score_admissible'])

    def test_string_is_not_a_number(self):
        self.roundtrip(change=lambda v: v['observation']['sources']['load_service'].update(force_y_n='-100'))
        self.assertFalse(self.decision()['score_admissible'])

    def test_extra_private_key_is_not_ignored(self):
        self.roundtrip(change=lambda v: v['observation'].update(manifest={'synthetic_reference': True}))
        self.assertFalse(self.decision()['score_admissible'])

    def test_actual_input_hash_is_not_relaxed(self):
        self.roundtrip()
        next(r for r in self.rows if r['type'] == 'model_input')['input_sha256'] = '0'*64
        self.save()
        self.assertFalse(self.decision()['score_admissible'])

    def test_old_protocol_is_not_retroactively_admitted(self):
        self.roundtrip()
        p = self.audit/'control.json'
        control = json.loads(p.read_text(encoding='utf-8'))
        control['protocol'] = 'comacbench.public-boundary.v1'
        p.write_text(json.dumps(control), encoding='utf-8')
        result = self.decision()
        self.assertFalse(result['score_admissible'])
        self.assertEqual(result['protocol_conformance'], 'unknown')


if __name__ == '__main__':
    unittest.main()
