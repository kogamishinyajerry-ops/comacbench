"""Exercise the actual CLI orchestration with solver and agent boundaries mocked."""
import argparse
from contextlib import ExitStack, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from comacbench import __main__ as cli


class CompletionOrchestrationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'pack'
        (self.root / 'tasks/example').mkdir(parents=True)
        self.out = Path(self.tmp.name) / 'out'
        self.tasks = [{'id': 'one', 'suite': 'example', 'adapter': 'code_exec',
                       'path': 'tasks/example/one.yaml'}]
        self.spec = {'grader': {'oracle_source': 'private/reference.py'},
                     'evaluation': {'negative_controls': [
                         {'script': 'private/wrong.py', 'max_score': 0}]}}
        # JSON is also valid YAML. No contributed code is run by these fixtures.
        (self.root / 'tasks/example/one.yaml').write_text(json.dumps(self.spec))
        self.validation = {'runnable': True, 'tasks': self.tasks, 'pack': {'id': 'fixture'}}
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        for name, value in (
            ('validate_pack', self.validation), ('execution_environment', {}),
            ('engine_identity', {}), ('fingerprint', 'fixture'),
            ('load_agent', None), ('agent_identity', {'name': 'fixture'}),
        ):
            self.stack.enter_context(patch.object(cli, name, return_value=value))
        self.stack.enter_context(patch.object(
            cli, 'digest', side_effect=lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()))
        self.stack.enter_context(patch.object(cli, 'write_report'))
        self.stack.enter_context(redirect_stdout(io.StringIO()))

    def args(self, command='run'):
        return argparse.Namespace(pack=str(self.root), out=str(self.out), command=command,
                                  agent=str(self.root.parent / 'agent.json'), seed=0, resume=False)

    def write_result(self, dest, *, task_id='one', filename='one', score=1, failure_mode=None):
        dest.mkdir(parents=True, exist_ok=True)
        result = {'task_id': task_id, 'registry_id': 'example', 'score': score,
                  'validity_gate': 1 if score else 0, 'failure_mode': failure_mode,
                  'artifacts': {'grade_details': '{}'}, 'gate_failures': []}
        (dest / f'result_{filename}.json').write_text(json.dumps(result))

    def run_with_result(self, **changes):
        return patch.object(cli, 'run_suite', side_effect=lambda root, suite, dest, *args:
                            self.write_result(dest, **changes))

    def document(self):
        return json.loads((self.out / 'run.json').read_text())

    def test_successful_runner_without_results_is_interrupted(self):
        with patch.object(cli, 'run_suite', return_value=[]):
            with self.assertRaisesRegex(ValueError, 'result_completeness_failed'):
                cli.execute(self.args())
        self.assertEqual(self.document()['status'], 'interrupted')
        self.assertEqual(self.document()['completion']['missing_tasks'], ['example/one'])

    def test_partial_roster_does_not_pass_calibration(self):
        self.tasks.append({'id': 'two', 'suite': 'example', 'adapter': 'code_exec',
                           'path': 'tasks/example/two.yaml'})
        (self.root / 'tasks/example/two.yaml').write_text(json.dumps(self.spec))
        def control_run(argv, **kwargs):
            dest = Path(argv[argv.index('--out') + 1])
            task_id = dest.name.rsplit('-', 1)[0]
            self.write_result(dest, task_id=task_id, filename=task_id, score=0,
                              failure_mode='missing_output')
            return SimpleNamespace(returncode=0)
        with self.run_with_result(), patch.object(cli.subprocess, 'run', side_effect=control_run):
            with self.assertRaisesRegex(ValueError, 'result_completeness_failed'):
                cli.execute(self.args('calibrate'))
        self.assertEqual(self.document()['completion']['recorded_results'], 1)
        self.assertNotEqual(self.document().get('calibration_passed'), True)

    def test_valid_zero_score_remains_complete(self):
        with self.run_with_result(score=0, failure_mode='missing_output'):
            self.assertEqual(cli.execute(self.args()), 0)
        self.assertEqual(self.document()['status'], 'complete')
        self.assertFalse(self.document()['results'][0]['full_pass'])

    def test_result_identity_mismatch_is_interrupted(self):
        with self.run_with_result(task_id='other'):
            with self.assertRaisesRegex(ValueError, 'result_completeness_failed'):
                cli.execute(self.args())
        self.assertIn('result_task_id_mismatch', self.document()['results'][0]['result_issues'])

    def calibrate(self, failure_mode):
        def control_run(argv, **kwargs):
            dest = Path(argv[argv.index('--out') + 1])
            self.write_result(dest, score=0, failure_mode=failure_mode)
            return SimpleNamespace(returncode=0)
        with self.run_with_result(), patch.object(cli.subprocess, 'run', side_effect=control_run):
            return cli.execute(self.args('calibrate'))

    def test_crashed_negative_control_fails_calibration(self):
        self.assertEqual(self.calibrate('crash'), 3)
        self.assertFalse(self.document()['calibration_passed'])
        self.assertIn('voided_result', self.document()['controls'][0]['result_issues'])

    def test_environment_failure_is_not_negative_control_success(self):
        self.assertEqual(self.calibrate('env_mismatch'), 3)
        self.assertFalse(self.document()['calibration_passed'])

    def test_expected_negative_control_does_not_regress(self):
        self.assertEqual(self.calibrate('missing_output'), 0)
        self.assertTrue(self.document()['calibration_passed'])


if __name__ == '__main__':
    unittest.main()
