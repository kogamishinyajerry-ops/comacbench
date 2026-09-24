"""Synthetic paired experiments: these tests are not model performance results."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

import test_campaign as fixtures
from comacbench import campaign as c
from comacbench.campaign_comparison import recorded_diagnostics, render_comparison


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.CampaignTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def change(self, subject, tid='units', *, variant='transfer', seed=0, **changes):
        run = self.fixture.path(subject, variant, seed)
        doc, _ = c.read_json(run)
        row = next(row for row in doc['results'] if row['id'] == tid)
        path = run.parent / 'runs' / row['suite'] / f'result_{tid}.json'
        raw, _ = c.read_json(path)
        raw.update(changes)
        fixtures.write(path, raw)
        row.update(score=raw['score'], validity_gate=raw['validity_gate'],
                   result_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        fixtures.write(run, doc)

    def comparison(self, split='transfer'):
        return next(p for p in self.fixture.report()['comparisons'] if p['split'] == split)

    def test_unchanged_success(self):
        pair = self.comparison()
        self.assertEqual(pair['paired_outcomes']['counts']['both_pass'], 4)
        self.assertFalse(pair['paired_outcomes']['has_observed_regressions'])

    def test_balanced_net_zero_must_show_gain_and_regression(self):
        self.change('baseline', score=0, validity_gate=0, gate_failures=['wrong_units'])
        self.change('candidate', 'rejections', score=0, validity_gate=0, gate_failures=['wrong_rejection'])
        pair = self.comparison()
        self.assertEqual(pair['delta_pass_rate'], 0)
        self.assertEqual(pair['paired_outcomes']['counts'], {
            'gained': 1, 'regressed': 1, 'both_pass': 2, 'both_fail': 0, 'unresolved': 0})
        self.assertTrue(pair['paired_outcomes']['has_observed_regressions'])
        self.assertIn('出现新增退步', render_comparison(pair))

    def test_positive_net_does_not_hide_regression(self):
        self.change('baseline', score=0, validity_gate=0)
        self.change('baseline', seed=1, score=0, validity_gate=0)
        self.change('candidate', 'rejections', score=0, validity_gate=0)
        pair = self.comparison()
        self.assertEqual(pair['delta_pass_rate'], .25)
        self.assertTrue(pair['paired_outcomes']['has_observed_regressions'])

    def test_full_pass_threshold_not_a_new_scoring_rule(self):
        self.change('baseline', score=.2)
        self.change('candidate', score=.8)
        row = next(r for r in self.comparison()['paired_outcomes']['tasks'] if r['seed'] == 0 and r['task_id'] == 'units')
        self.assertEqual(row['outcome'], 'both_fail')
        self.assertEqual(row['baseline']['result']['score'], .2)
        self.assertEqual(row['candidate']['result']['score'], .8)

    def test_missing_candidate_is_unresolved_not_regression(self):
        self.fixture.path().unlink()
        pair = self.comparison()
        self.assertFalse(pair['comparable'])
        self.assertIsNone(pair['delta_pass_rate'])
        self.assertEqual(pair['paired_outcomes']['counts']['unresolved'], 2)
        self.assertEqual(pair['paired_outcomes']['counts']['regressed'], 0)
        self.assertIsNone(pair['paired_outcomes']['has_observed_regressions'])

    def test_missing_baseline_is_unresolved_not_gain(self):
        self.fixture.path('baseline').unlink()
        pair = self.comparison()
        self.assertEqual(pair['paired_outcomes']['counts']['unresolved'], 2)
        self.assertEqual(pair['paired_outcomes']['counts']['gained'], 0)

    def test_crash_is_unresolved(self):
        self.change('candidate', score=0, validity_gate=0, failure_mode='crash')
        pair = self.comparison()
        self.assertEqual(pair['paired_outcomes']['counts']['unresolved'], 2)
        self.assertFalse(pair['comparable'])

    def test_legitimate_timeout_is_completed_task_failure(self):
        self.change('candidate', score=0, validity_gate=0, failure_mode='timeout')
        pair = self.comparison()
        self.assertTrue(pair['comparable'])
        self.assertEqual(pair['paired_outcomes']['counts']['regressed'], 1)

    def test_global_extra_run_suppresses_all_transitions(self):
        self.change('candidate', score=0, validity_gate=0)
        fixtures.archive(self.fixture.runs / 'unregistered-retry')
        for pair in self.fixture.report()['comparisons']:
            self.assertFalse(pair['comparable'])
            self.assertTrue(pair['paired_outcomes']['archive_blocked'])
            self.assertEqual(pair['paired_outcomes']['counts']['unresolved'], 4)
            self.assertEqual(pair['paired_outcomes']['counts']['regressed'], 0)

    def test_one_broken_split_does_not_erase_other_split(self):
        self.fixture.path().unlink()
        self.assertTrue(self.comparison('development')['comparable'])
        self.assertFalse(self.comparison()['comparable'])

    def test_partial_verified_regression_is_visible_but_not_whole_group_claim(self):
        self.change('candidate', score=0, validity_gate=0)
        self.fixture.path().unlink()
        pair = self.comparison()
        self.assertFalse(pair['comparable'])
        self.assertTrue(pair['paired_outcomes']['has_observed_regressions'])
        self.assertIn('局部差异', render_comparison(pair))

    def test_pairing_by_task_id_not_result_order(self):
        self.change('candidate', 'rejections', score=0, validity_gate=0)
        self.fixture.mutate_doc(lambda d: d['results'].reverse(), self.fixture.path('candidate', seed=0))
        rows = self.comparison()['paired_outcomes']['tasks']
        self.assertEqual([(r['task_id'], r['seed']) for r in rows if r['outcome'] == 'regressed'], [('rejections', 0)])

    def test_seed_differences_not_paired_together(self):
        self.change('baseline', seed=0, score=0, validity_gate=0)
        self.change('candidate', seed=1, score=0, validity_gate=0)
        pair = self.comparison()
        self.assertEqual(pair['paired_outcomes']['counts']['gained'], 1)
        self.assertEqual(pair['paired_outcomes']['counts']['regressed'], 1)

    def test_provenance_retains_raw_and_run_hashes(self):
        for row in self.comparison()['paired_outcomes']['tasks']:
            for side in (row['baseline'], row['candidate']):
                path = self.fixture.runs / side['record']
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), side['result']['result_sha256'])
                self.assertTrue(c.SHA.fullmatch(side['run_sha256']))
                self.assertFalse(Path(side['record']).is_absolute())

    def test_raw_diagnostics_not_summary_diagnostics(self):
        self.change('candidate', score=0, validity_gate=0, failure_mode='physics', gate_failures=['wrong_unit'])
        self.fixture.mutate_doc(lambda d: d['results'][0].update(failure_mode='fake', gate_failures=['fake']),
                                self.fixture.path('candidate', seed=0))
        row = next(r for r in self.comparison()['paired_outcomes']['tasks'] if r['outcome'] == 'regressed')
        self.assertEqual(row['candidate']['result']['gate_failures'], ['wrong_unit'])
        self.assertEqual(row['candidate']['result']['failure_mode'], 'physics')

    def test_optional_bad_diagnostics_do_not_change_score(self):
        self.change('candidate', gate_failures=True, failure_mode=123)
        pair = self.comparison()
        self.assertTrue(pair['comparable'])
        result = pair['paired_outcomes']['tasks'][0]['candidate']['result']
        self.assertEqual(result['score'], 1)
        self.assertEqual(len(result['diagnostic_issues']), 2)

    def test_absent_diagnosis_not_invented(self):
        self.change('candidate', score=0, validity_gate=0)
        self.assertIn('未记录具体诊断', render_comparison(self.comparison()))

    def test_bounded_optional_diagnostics(self):
        result = recorded_diagnostics({'failure_mode': 'x'*1000, 'gate_failures': ['a'*1000]*50})
        self.assertEqual(len(result['failure_mode']), 240)
        self.assertTrue(all(len(item) <= 240 for item in result['gate_failures']))
        self.assertIn('gate_failures_truncated', result['diagnostic_issues'])

    def test_json_lock_not_mutated_or_reversioned(self):
        before = deepcopy(self.fixture.lock)
        self.fixture.report()
        self.assertEqual(before, self.fixture.lock)
        self.assertEqual(c.LOCK, 'comacbench.campaign.lock.v2')

    def test_no_comparison_requested_means_no_invented_ab(self):
        self.fixture.plan['comparisons'] = []
        self.fixture.lock = c.freeze_plan(self.fixture.plan, self.fixture.anchors)
        self.assertEqual(self.fixture.report()['comparisons'], [])

    def test_every_planned_pair_accounted_for(self):
        self.change('baseline', score=0, validity_gate=0)
        self.fixture.path().unlink()
        for pair in self.fixture.report()['comparisons']:
            audit = pair['paired_outcomes']
            self.assertEqual(sum(audit['counts'].values()), pair['paired_task_executions'])
            self.assertEqual(len(audit['tasks']), pair['paired_task_executions'])

    def test_counts_reconcile_with_original_delta(self):
        self.change('baseline', score=0, validity_gate=0)
        pair = self.comparison()
        counts = pair['paired_outcomes']['counts']
        self.assertEqual((counts['gained']-counts['regressed'])/pair['paired_task_executions'], pair['delta_pass_rate'])

    def test_html_escapes_diagnostics_and_comparison_labels(self):
        self.change('candidate', score=0, validity_gate=0, gate_failures=['<script>attack</script>'])
        pair = self.comparison()
        pair['family'] = '<img src=x>'
        page = render_comparison(pair)
        self.assertNotIn('<script>', page)
        self.assertNotIn('<img ', page)
        self.assertIn('&lt;script&gt;', page)

    def test_html_limit_does_not_trim_json_or_hide_regressions_first(self):
        pair = self.comparison()
        originals = pair['paired_outcomes']['tasks']
        pair['paired_outcomes']['tasks'] = [deepcopy(originals[0]) for _ in range(105)]
        pair['paired_outcomes']['tasks'][-1]['outcome'] = 'regressed'
        pair['paired_outcomes']['tasks'][-1]['task_id'] = 'last-regression'
        page = render_comparison(pair)
        self.assertIn('100/105', page)
        self.assertIn('last-regression', page)
        self.assertEqual(len(pair['paired_outcomes']['tasks']), 105)

    def test_real_campaign_cli_consumes_synthetic_archive_and_writes_drilldown(self):
        self.change('candidate', score=0, validity_gate=0, gate_failures=['wrong_unit'])
        lock = self.fixture.root / 'lock.json'
        fixtures.write(lock, self.fixture.lock)
        out = self.fixture.root / 'cli-report'
        proc = subprocess.run([sys.executable, '-m', 'comacbench.campaign', 'report', str(lock),
                               '--runs', str(self.fixture.runs), '--out', str(out)],
                              capture_output=True, text=True, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        report, _ = c.read_json(out / 'campaign.json')
        self.assertTrue(report['complete'])
        self.assertFalse(report['publishable'])
        self.assertFalse(report['isolated_transfer_verified'])
        self.assertIn('<details>', (out/'report.html').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
