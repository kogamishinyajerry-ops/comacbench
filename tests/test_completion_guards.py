"""No solver, model, network, or third-party dependency is needed for these tests."""
import unittest
from comacbench.completion import completion_summary, negative_control_passed, result_issues


class CompletionGuardsTest(unittest.TestCase):
    def result(self, **changes):
        return dict(task_id='one', registry_id='example', validity_gate=0,
                    score=0.0, failure_mode=None, **{}) | changes

    def issues(self, **changes):
        return result_issues(self.result(**changes), task_id='one', suite='example')

    def control(self, result=None, expected=None, actual=()):
        return negative_control_passed(
            self.result() if result is None else result,
            {'max_score': 0, 'expected_issue': expected},
            task_id='one', suite='example', actual_issues=actual)

    def summary(self, rows, tasks=None):
        return completion_summary(
            [{'id': 'one', 'suite': 'example'}] if tasks is None else tasks, rows)

    def row(self, **changes):
        return dict(id='one', suite='example', score=0, full_pass=False,
                    result_issues=[]) | changes

    def test_empty_results_are_not_complete(self):
        s = self.summary([])
        self.assertFalse(s['complete'])
        self.assertEqual(s['missing_tasks'], ['example/one'])

    def test_empty_roster_is_not_complete(self):
        self.assertFalse(self.summary([], tasks=[])['complete'])

    def test_missing_one_result_is_not_hidden_by_a_full_pass(self):
        s = self.summary([self.row(score=1, full_pass=True)],
                         tasks=[{'id': i, 'suite': 'example'} for i in ('one', 'two')])
        self.assertFalse(s['complete'])
        self.assertEqual(s['expected_tasks'], 2)
        self.assertEqual(s['recorded_results'], 1)

    def test_completed_agent_failure_is_not_an_infrastructure_failure(self):
        self.assertTrue(self.summary([self.row()])['complete'])
        self.assertEqual(self.issues(failure_mode='missing_output'), [])

    def test_duplicate_results_are_not_complete(self):
        self.assertFalse(self.summary([self.row(), self.row()])['complete'])

    def test_unexpected_result_is_not_complete(self):
        self.assertFalse(self.summary([self.row(), self.row(id='other')])['complete'])

    def test_duplicate_roster_is_not_complete(self):
        task = {'id': 'one', 'suite': 'example'}
        self.assertFalse(self.summary([self.row()], tasks=[task, task])['complete'])

    def test_invalid_result_blocks_completion(self):
        s = self.summary([self.row(result_issues=['voided_result'])])
        self.assertFalse(s['complete'])
        self.assertEqual(s['scorable_results'], 0)

    def test_harness_failure_modes_cannot_pass_negative_control(self):
        for mode in ('crash', 'env_mismatch'):
            with self.subTest(mode=mode):
                r = self.result(failure_mode=mode)
                self.assertNotIn('voided', r)  # build_result() does not set this flag.
                self.assertFalse(self.control(r))
                self.assertFalse(self.control(r, 'wrong_load', ['wrong_load']))

    def test_explicit_voided_flag_cannot_pass(self):
        self.assertFalse(self.control(self.result(voided=True)))

    def test_expected_model_failures_can_pass_control(self):
        for mode in (None, 'missing_output', 'timeout', 'tool_violation'):
            with self.subTest(mode=mode):
                self.assertTrue(self.control(self.result(failure_mode=mode)))

    def test_named_diagnosis_is_still_required(self):
        self.assertFalse(self.control(expected='wrong_load', actual=['missing_material']))
        self.assertTrue(self.control(expected='wrong_load', actual=['wrong_load']))

    def test_identity_is_validated(self):
        for field, value in (('task_id', 'other'), ('registry_id', 'other')):
            with self.subTest(field=field):
                self.assertFalse(self.control(self.result(**{field: value})))

    def test_invalid_scores_are_rejected(self):
        for score in (None, True, False, '0', float('nan'), float('inf'), -1, 2, 10**1000):
            with self.subTest(score=score):
                self.assertIn('invalid_score', self.issues(score=score))
                self.assertFalse(self.control(self.result(score=score)))

    def test_invalid_gate_is_rejected(self):
        for gate in (None, True, False, '0', 0.0, 2):
            with self.subTest(gate=gate):
                self.assertIn('invalid_validity_gate', self.issues(validity_gate=gate))

    def test_gate_score_contradiction_is_rejected(self):
        self.assertIn('gate_score_contradiction', self.issues(score=0.5))

    def test_valid_partial_and_full_scores_are_accepted(self):
        self.assertEqual(self.issues(validity_gate=1, score=0.5), [])
        self.assertEqual(self.issues(validity_gate=1, score=1), [])

    def test_bad_envelope_is_rejected(self):
        for value in (None, [], 'result', 1):
            with self.subTest(value=value):
                self.assertEqual(result_issues(value, task_id='one', suite='example'),
                                 ['result_not_object'])

    def test_invalid_control_threshold_is_rejected(self):
        for maximum in (None, True, '0', float('nan'), float('inf'), -1, 2, 10**1000):
            with self.subTest(maximum=maximum):
                self.assertFalse(negative_control_passed(
                    self.result(), {'max_score': maximum}, task_id='one',
                    suite='example', actual_issues=[]))

    def test_threshold_and_gate_are_not_relaxed(self):
        self.assertFalse(self.control(self.result(validity_gate=1, score=0.1)))


if __name__ == '__main__':
    unittest.main()
