"""Synthetic archive fixtures test the auditor, NOT an Agent or CFD capability."""
from __future__ import annotations

import contextlib
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from comacbench import campaign as c


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, allow_nan=True) + '\n', encoding='utf-8')


def agent(name):
    return {'name': 'external', 'model': name, 'revision': 'fixture-v1',
            'protocol': 'comacbench.agent.v1', 'agent_kind': 'user_agent',
            'config_sha256': c.sha(name), 'revision_files': {'wrapper.py': c.sha(name)},
            'command_files': {'0': 'a' * 64}, 'executable_sha256': 'a' * 64, 'identity_env': {}}


def archive(root, *, name='candidate', variant='dev', seed=0, mode='run'):
    tasks = [{'id': tid, 'suite': 'aviation.data', 'family': 'enterprise_data',
              'path': f'tasks/aviation.data/{tid}.yaml', 'adapter': 'code_exec',
              'exec_kind': 'unit_tests_problem', 'evidence_level': 'executable_checks'}
             for tid in ('units', 'rejections')]
    identity = {'protocol': 'comacbench.run.v1', 'pack_sha256': c.sha(variant),
                'engine': {'comacbench/completion.py': 'e' * 64},
                'execution_environment': {'python': {'path': '/fixture/python', 'sha256': 'a' * 64},
                                          'dependencies': {'PyYAML': 'fixture'}, 'solvers': {}},
                'agent': agent(name), 'mode': mode, 'seed': seed}
    if mode == 'calibrate':
        identity['agent'] = {'name': 'oracle', 'kind': 'grader_calibration'}
    doc = {'identity': identity, 'status': 'complete', 'mode': mode,
           'agent': identity['agent'], 'validation': {'runnable': True, 'tasks': tasks}, 'results': []}
    for task in tasks:
        raw = {'task_id': task['id'], 'registry_id': task['suite'], 'validity_gate': 1,
               'adapter': 'code_exec', 'environment_digest': 'sha256:' + 'f' * 64,
               'score': 1.0, 'failure_mode': None, 'gate_failures': [],
               'artifacts': {'grade_details': json.dumps({'kind': 'unit_tests'})}}
        path = root / 'runs' / task['suite'] / f'result_{task["id"]}.json'
        write(path, raw)
        doc['results'].append({**task, 'score': 1.0, 'validity_gate': 1, 'full_pass': True,
                               'result_file': 'C:\\old-machine\\result.json', 'result_issues': [],
                               'evidence_level': 'executable_checks',
                               'result_sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    write(root / 'runs/aviation.data/run_manifest.json', {
        'registry_id': 'aviation.data', 'adapter': 'code_exec',
        'provider': 'oracle' if mode == 'calibrate' else 'external', 'seed': seed,
        'n_tasks': len(tasks), 'environment_digest': 'sha256:' + 'f' * 64})
    write(root / 'run.json', doc)
    return root / 'run.json'


class CampaignTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.anchors, self.runs = self.root / 'anchors', self.root / 'runs'
        for name in ('baseline', 'candidate'):
            archive(self.anchors / name, name=name)
        for variant in ('dev', 'transfer'):
            archive(self.anchors / variant, variant=variant, mode='calibrate')
        self.plan = {'protocol': c.PLAN, 'id': 'unit-family-fixture', 'scope': 'public_regression',
                     'seeds': [0, 1],
                     'subjects': [{'id': name, 'anchor': f'{name}/run.json'}
                                  for name in ('baseline', 'candidate')],
                     'cases': [{'id': variant, 'family': 'unit-conversion',
                                'split': 'development' if variant == 'dev' else 'transfer',
                                'scope_note': 'Synthetic auditor fixture, not an engineering result.',
                                'anchor': f'{variant}/run.json'} for variant in ('dev', 'transfer')],
                     'comparisons': [{'baseline': 'baseline', 'candidate': 'candidate'}]}
        self.lock = c.freeze_plan(self.plan, self.anchors)
        for name in ('baseline', 'candidate'):
            for variant in ('dev', 'transfer'):
                for seed in (0, 1):
                    archive(self.runs / name / variant / f'seed-{seed}',
                            name=name, variant=variant, seed=seed)

    def path(self, name='candidate', variant='transfer', seed=1):
        return self.runs / name / variant / f'seed-{seed}' / 'run.json'

    def mutate_doc(self, fn, path=None):
        path = path or self.path()
        doc, _ = c.read_json(path)
        fn(doc)
        write(path, doc)

    def mutate_raw(self, fn, *, sync_summary=True, refresh_digest=True, path=None):
        path = path or self.path()
        doc, _ = c.read_json(path)
        row = doc['results'][0]
        raw_path = path.parent / 'runs' / row['suite'] / f'result_{row["id"]}.json'
        raw, _ = c.read_json(raw_path)
        fn(raw)
        write(raw_path, raw)
        if sync_summary:
            row.update(score=raw.get('score'), validity_gate=raw.get('validity_gate'))
        if refresh_digest:
            row['result_sha256'] = hashlib.sha256(raw_path.read_bytes()).hexdigest()
        write(path, doc)

    def report(self):
        return c.evaluate(self.lock, self.runs)

    def assert_blocked(self, code):
        report = self.report()
        self.assertFalse(report['complete'])
        errors = [issue for cell in report['cells'] for issue in cell['issues']]
        self.assertTrue(any(code in e for e in errors), errors)
        self.assertTrue(any(g['unresolved'] > 0 and g['pass_rate'] is None for g in report['groups']))
        self.assertFalse(next(p for p in report['comparisons'] if p['split'] == 'transfer')['comparable'])
        return report

    def test_complete_matrix_and_paired_denominators(self):
        report = self.report()
        self.assertTrue(report['complete'])
        self.assertEqual(len(report['cells']), 8)
        self.assertEqual(len(report['groups']), 4)
        self.assertTrue(all(g['expected'] == 4 and g['passed'] == 4 for g in report['groups']))
        self.assertTrue(all(p['delta_pass_rate'] == 0 for p in report['comparisons']))
        self.assertFalse(report['publishable'])
        self.assertFalse(report['isolated_transfer_verified'])
        self.assertFalse(report['engineering_artifacts_reverified'])

    def test_legitimate_engineering_failure_still_complete(self):
        self.mutate_raw(lambda raw: raw.update(score=0, validity_gate=0, failure_mode='physics',
                                               artifacts={'grade_details': '{}'}))
        report = self.report()
        self.assertTrue(report['complete'])
        group = next(g for g in report['groups'] if g['subject'] == 'candidate' and g['split'] == 'transfer')
        self.assertEqual((group['passed'], group['failed'], group['expected'], group['pass_rate']), (3, 1, 4, .75))
        comparison = next(p for p in report['comparisons'] if p['split'] == 'transfer')
        self.assertEqual(comparison['delta_pass_rate'], -.25)

    def test_forged_full_pass_is_not_credited(self):
        self.mutate_raw(lambda raw: raw.update(score=.2))
        self.assertTrue(c.read_json(self.path())[0]['results'][0]['full_pass'])
        self.assertEqual(sum(g['failed'] for g in self.report()['groups']), 1)

    def test_missing_run_keeps_fixed_denominator(self):
        shutil.rmtree(self.path().parent)
        report = self.assert_blocked('missing_file')
        group = next(g for g in report['groups'] if g['subject'] == 'candidate' and g['split'] == 'transfer')
        self.assertEqual((group['expected'], group['passed'], group['unresolved']), (4, 2, 2))

    def test_interrupted_run_blocks(self):
        self.mutate_doc(lambda doc: doc.update(status='interrupted'))
        self.assert_blocked('run_incomplete')

    def test_oracle_run_cannot_be_a_model_score(self):
        archive(self.path().parent, variant='transfer', seed=1, mode='calibrate')
        self.assert_blocked('calibration_not_score')

    def test_reference_selftest_cannot_be_model_score(self):
        def edit(doc):
            doc['identity']['agent']['agent_kind'] = 'reference_self_test'
            doc['agent'] = deepcopy(doc['identity']['agent'])
        self.mutate_doc(edit)
        self.assert_blocked('not_user_agent')

    def test_unknown_agent_kind_is_rejected(self):
        def edit(doc):
            doc['identity']['agent']['agent_kind'] = 'something_new'
            doc['agent'] = deepcopy(doc['identity']['agent'])
        self.mutate_doc(edit)
        self.assert_blocked('not_user_agent')

    def test_agent_revision_drift(self):
        def edit(doc):
            doc['identity']['agent']['revision'] = 'new'
            doc['agent'] = deepcopy(doc['identity']['agent'])
        self.mutate_doc(edit)
        self.assert_blocked('agent_identity_drift')

    def test_agent_summary_disagrees(self):
        self.mutate_doc(lambda doc: doc['agent'].update(model='different'))
        self.assert_blocked('agent_summary_mismatch')

    def test_engine_drift(self):
        self.mutate_doc(lambda doc: doc['identity']['engine'].update({'new.py': 'f' * 64}))
        self.assert_blocked('runtime_contract_drift')

    def test_environment_drift(self):
        self.mutate_doc(lambda doc: doc['identity']['execution_environment'].update(gpu='other'))
        self.assert_blocked('runtime_contract_drift')

    def test_pack_drift(self):
        self.mutate_doc(lambda doc: doc['identity'].update(pack_sha256='f' * 64))
        self.assert_blocked('runtime_contract_drift')

    def test_seed_mismatch(self):
        self.mutate_doc(lambda doc: doc['identity'].update(seed=99))
        self.assert_blocked('suite_manifest_mismatch')

    def test_seed_bool(self):
        self.mutate_doc(lambda doc: doc['identity'].update(seed=True))
        self.assert_blocked('invalid_run_seed')

    def test_mode_mismatch(self):
        self.mutate_doc(lambda doc: doc['identity'].update(mode='calibrate'))
        self.assert_blocked('run_mode_mismatch')

    def test_task_roster_missing(self):
        self.mutate_doc(lambda doc: doc['results'].pop())
        self.assert_blocked('result_roster_mismatch')

    def test_task_roster_duplicate(self):
        self.mutate_doc(lambda doc: doc['results'].append(deepcopy(doc['results'][0])))
        self.assert_blocked('result_roster_mismatch')

    def test_task_contract_drift(self):
        self.mutate_doc(lambda doc: doc['validation']['tasks'][0].update(family='changed'))
        self.assert_blocked('task_contract_drift')

    def test_raw_file_missing(self):
        (self.path().parent / 'runs/aviation.data/result_units.json').unlink()
        self.assert_blocked('missing_file')

    def test_raw_digest_tampered(self):
        self.mutate_raw(lambda raw: raw.update(score=0), refresh_digest=False)
        self.assert_blocked('result_digest_mismatch')

    def test_raw_summary_tampered(self):
        self.mutate_doc(lambda doc: doc['results'][0].update(score=.5))
        self.assert_blocked('result_summary_mismatch')

    def test_raw_wrong_task(self):
        self.mutate_raw(lambda raw: raw.update(task_id='other'))
        self.assert_blocked('result_task_id_mismatch')

    def test_raw_wrong_suite(self):
        self.mutate_raw(lambda raw: raw.update(registry_id='other'))
        self.assert_blocked('result_suite_mismatch')

    def test_recorded_result_issues(self):
        self.mutate_doc(lambda doc: doc['results'][0].update(result_issues=['voided_result']))
        self.assert_blocked('recorded_result_issues')

    def test_bool_score_rejected(self):
        self.mutate_raw(lambda raw: raw.update(score=True))
        self.assert_blocked('invalid_score')

    def test_nan_score_rejected(self):
        self.mutate_raw(lambda raw: raw.update(score=float('nan')))
        self.assert_blocked('nonfinite_json')

    def test_infinite_exponent_score_rejected(self):
        self.mutate_raw(lambda raw: raw.update(score=1e100))
        self.assert_blocked('invalid_score')

    def test_gate_contradiction(self):
        self.mutate_raw(lambda raw: raw.update(validity_gate=0))
        self.assert_blocked('gate_score_contradiction')

    def test_crash_is_not_engineering_failure(self):
        self.mutate_raw(lambda raw: raw.update(score=0, validity_gate=0, failure_mode='crash'))
        self.assert_blocked('voided_result')

    def test_env_mismatch_is_not_engineering_failure(self):
        self.mutate_raw(lambda raw: raw.update(score=0, validity_gate=0, failure_mode='env_mismatch'))
        self.assert_blocked('voided_result')

    def test_evidence_label_does_not_upgrade_raw_result(self):
        self.mutate_raw(lambda raw: raw.update(artifacts={'grade_details': '{}'}))
        self.mutate_doc(lambda doc: doc['results'][0].update(evidence_level='solver_executed'))
        self.assert_blocked('passing_evidence_mismatch')

    def test_bad_details_block(self):
        self.mutate_raw(lambda raw: raw.update(artifacts={'grade_details': '[]'}))
        self.assert_blocked('invalid_grade_details')

    def test_symlink_raw_result_blocked(self):
        path = self.path().parent / 'runs/aviation.data/result_units.json'
        target = path.with_suffix('.real')
        path.rename(target)
        try:
            path.symlink_to(target)
        except OSError:
            self.skipTest('symlink permission unavailable')
        self.assert_blocked('symlink_forbidden')

    def test_path_escape_in_task_blocked(self):
        self.mutate_doc(lambda doc: doc['validation']['tasks'][0].update(id='../escape'))
        self.assert_blocked('invalid_id')

    def test_duplicate_json_key(self):
        path = self.path()
        path.write_text(path.read_text().replace('"status": "complete"', '"status":"complete","status":"complete"'))
        self.assert_blocked('duplicate_json_key')

    def test_moved_run_folder_does_not_use_absolute_result_file(self):
        destination = self.root / 'copied'
        shutil.copytree(self.runs, destination)
        self.assertTrue(c.evaluate(self.lock, destination)['complete'])

    def test_unregistered_retry_blocks_comparison(self):
        archive(self.runs / 'candidate/transfer/retry-best')
        report = self.report()
        self.assertFalse(report['complete'])
        self.assertEqual(len(report['unexpected_runs']), 1)
        self.assertTrue(all(g['pass_rate'] is None for g in report['groups']))
        self.assertTrue(all(not p['comparable'] for p in report['comparisons']))

    def test_lock_digest_mismatch(self):
        self.lock['body']['id'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'lock_digest_mismatch'):
            self.report()

    def test_duplicate_seed_plan_rejected(self):
        self.plan['seeds'] = [0, 0]
        with self.assertRaisesRegex(ValueError, 'invalid_seeds'):
            c.freeze_plan(self.plan, self.anchors)

    def test_bool_seed_plan_rejected(self):
        self.plan['seeds'] = [True]
        with self.assertRaisesRegex(ValueError, 'invalid_seeds'):
            c.freeze_plan(self.plan, self.anchors)

    def test_duplicate_case_contract_rejected(self):
        self.plan['cases'][1]['anchor'] = 'dev/run.json'
        with self.assertRaisesRegex(ValueError, 'duplicate_case_contract'):
            c.freeze_plan(self.plan, self.anchors)

    def test_duplicate_subject_rejected(self):
        self.plan['subjects'][1]['anchor'] = 'baseline/run.json'
        with self.assertRaisesRegex(ValueError, 'duplicate_subject'):
            c.freeze_plan(self.plan, self.anchors)

    def test_reference_can_anchor_case_but_not_subject(self):
        self.assertEqual(self.lock['body']['cases'][0]['required_evidence']['aviation.data/units'], 'executable_checks')
        self.plan['subjects'][0]['anchor'] = 'dev/run.json'
        with self.assertRaisesRegex(ValueError, 'calibration_not_score'):
            c.freeze_plan(self.plan, self.anchors)

    def test_transfer_requires_development_in_same_family(self):
        self.plan['cases'][1]['family'] = 'unrelated'
        with self.assertRaisesRegex(ValueError, 'transfer_without_development'):
            c.freeze_plan(self.plan, self.anchors)

    def test_hidden_scope_rejected(self):
        self.plan['scope'] = 'isolated_holdout'
        with self.assertRaisesRegex(ValueError, 'unsupported_scope'):
            c.freeze_plan(self.plan, self.anchors)

    def test_freeze_is_deterministic(self):
        self.assertEqual(self.lock, c.freeze_plan(self.plan, self.anchors))

    def test_anchor_path_escape(self):
        self.plan['cases'][0]['anchor'] = '../outside/run.json'
        with self.assertRaisesRegex(ValueError, 'path_escape'):
            c.freeze_plan(self.plan, self.anchors)

    def test_cross_case_engine_drift_blocks(self):
        path = self.anchors / 'transfer/run.json'
        self.mutate_doc(lambda doc: doc['identity']['engine'].update({'new.py': 'f' * 64}), path)
        with self.assertRaisesRegex(ValueError, 'cross_case_engine_drift'):
            c.freeze_plan(self.plan, self.anchors)

    def test_stress_is_reported_separately(self):
        self.plan['cases'][1]['split'] = 'stress'
        self.lock = c.freeze_plan(self.plan, self.anchors)
        report = self.report()
        self.assertEqual({g['split'] for g in report['groups']}, {'development', 'stress'})
        self.assertFalse(report['isolated_transfer_verified'])

    def test_html_escapes_untrusted_diagnostics(self):
        report = self.report()
        report['id'] = '<script>alert(1)</script>'
        report['cells'][0]['issues'] = ['<img src=x onerror=alert(1)>']
        page = c.render_html(report)
        self.assertNotIn('<script>', page)
        self.assertNotIn('<img ', page)
        self.assertIn('&lt;script&gt;', page)
        self.assertIn('未验证隔离迁移', page)

    def test_cli_complete_and_no_overwrite(self):
        lockpath = self.root / 'lock.json'
        write(lockpath, self.lock)
        out = self.root / 'report'
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            args = ['report', str(lockpath), '--runs', str(self.runs), '--out', str(out)]
            self.assertEqual(c.main(args), 0)
            self.assertEqual(c.main(args), 2)
        self.assertTrue((out / 'report.html').is_file())
        self.assertTrue(c.read_json(out / 'campaign.json')[0]['complete'])

    def test_cli_incomplete_writes_honest_report(self):
        self.path().unlink()
        lockpath = self.root / 'lock.json'
        write(lockpath, self.lock)
        out = self.root / 'incomplete-report'
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(c.main(['report', str(lockpath), '--runs', str(self.runs), '--out', str(out)]), 2)
        self.assertIn('证据不齐', (out / 'report.html').read_text())

    def test_cli_output_inside_runs_refused(self):
        lockpath = self.root / 'lock.json'
        write(lockpath, self.lock)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(c.main(['report', str(lockpath), '--runs', str(self.runs), '--out', str(self.runs / 'report')]), 2)
        self.assertFalse((self.runs / 'report').exists())

    def test_cli_freeze_subprocess_no_solver_or_new_dependency(self):
        planpath, lockpath = self.root / 'plan.json', self.root / 'frozen.json'
        write(planpath, self.plan)
        proc = subprocess.run([sys.executable, '-m', 'comacbench.campaign', 'freeze', str(planpath),
                               '--anchors', str(self.anchors), '--out', str(lockpath)],
                              capture_output=True, text=True, timeout=15)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(c.read_json(lockpath)[0], self.lock)

    def test_oversized_json_rejected(self):
        path = self.root / 'huge.json'
        path.write_bytes(b' ' * (c.MAX_BYTES + 1))
        with self.assertRaisesRegex(ValueError, 'json_too_large'):
            c.read_json(path)

    def test_invalid_json_types_fail_closed(self):
        for value in ([], True, None, 'not-a-run'):
            with self.subTest(value=value):
                write(self.path(), value)
                self.assert_blocked('json_not_object')

    def test_missing_all_runs_is_not_empty_success(self):
        shutil.rmtree(self.runs)
        report = self.report()
        self.assertFalse(report['complete'])
        self.assertEqual(sum(g['unresolved'] for g in report['groups']), 16)
        self.assertTrue(all(g['pass_rate'] is None for g in report['groups']))

    def test_partial_task_failures_do_not_void_campaign(self):
        for path in self.runs.rglob('run.json'):
            self.mutate_raw(lambda raw: raw.update(score=0, validity_gate=0), path=path)
        report = self.report()
        self.assertTrue(report['complete'])
        self.assertTrue(all(g['pass_rate'] == .5 for g in report['groups']))

    def test_bool_gate_rejected(self):
        self.mutate_raw(lambda raw: raw.update(validity_gate=True))
        self.assert_blocked('invalid_validity_gate')

    def test_future_runtime_identity_fields_are_not_ignored(self):
        self.mutate_doc(lambda doc: doc['identity'].update(future_policy='changed'))
        self.assert_blocked('runtime_contract_drift')

    def test_float_overflow_json_rejected(self):
        with self.assertRaisesRegex(ValueError, 'nonfinite_json'):
            c.decode('{"score":1e999}')

    def test_subject_case_insensitive_path_collision(self):
        self.plan['subjects'][0]['id'] = 'CANDIDATE'
        with self.assertRaisesRegex(ValueError, 'duplicate_subject'):
            c.freeze_plan(self.plan, self.anchors)

    def test_case_case_insensitive_path_collision(self):
        self.plan['cases'][0]['id'] = 'TRANSFER'
        with self.assertRaisesRegex(ValueError, 'duplicate_case'):
            c.freeze_plan(self.plan, self.anchors)

    def test_unknown_task_kind_cannot_set_own_evidence_level(self):
        self.mutate_doc(lambda doc: doc['validation']['tasks'][0].update(exec_kind='arbitrary'))
        self.assert_blocked('unsupported_task_kind')

    def test_solver_anchor_must_have_solver_evidence(self):
        path = self.anchors / 'dev/run.json'
        self.mutate_doc(lambda doc: [t.update(exec_kind='cfd_step')
                                     for t in doc['validation']['tasks']], path)
        with self.assertRaisesRegex(ValueError, 'case_anchor_not_full_pass'):
            c.freeze_plan(self.plan, self.anchors)

    def test_evidence_floor_cannot_be_lowered_in_lock(self):
        case = self.lock['body']['cases'][0]
        case['required_evidence']['aviation.data/units'] = 'input_audit'
        self.lock['sha256'] = c.sha(self.lock['body'])
        with self.assertRaisesRegex(ValueError, 'invalid_evidence_level'):
            self.report()

    def test_partial_case_anchor_does_not_freeze(self):
        self.mutate_raw(lambda raw: raw.update(score=.5), path=self.anchors / 'dev/run.json')
        with self.assertRaisesRegex(ValueError, 'case_anchor_not_full_pass'):
            c.freeze_plan(self.plan, self.anchors)

    def test_bad_artifacts_type_is_not_passing_evidence(self):
        self.mutate_raw(lambda raw: raw.update(artifacts=[]))
        self.assert_blocked('invalid_artifacts')

    def test_campaign_matrix_limit(self):
        self.lock['body']['seeds'] = list(range(100))
        self.lock['body']['cases'] *= 500
        with self.assertRaisesRegex(ValueError, 'campaign_too_large'):
            self.report()

    def test_no_reference_anchor_score_flows_into_results(self):
        for path in self.runs.rglob('run.json'):
            self.mutate_raw(lambda raw: raw.update(score=0, validity_gate=0), path=path)
        report = self.report()
        self.assertEqual(len(report['cells']), 8)
        self.assertEqual({g['subject'] for g in report['groups']}, {'baseline', 'candidate'})
        self.assertEqual(sum(g['passed'] for g in report['groups']), 8)

    def mutate_manifest(self, fn):
        path = self.path().parent / 'runs/aviation.data/run_manifest.json'
        doc, _ = c.read_json(path)
        fn(doc)
        write(path, doc)

    def test_oracle_suite_under_external_run_rejected(self):
        self.mutate_manifest(lambda doc: doc.update(provider='oracle'))
        self.assert_blocked('suite_manifest_mismatch')

    def test_manifest_seed_disagrees(self):
        self.mutate_manifest(lambda doc: doc.update(seed=999))
        self.assert_blocked('suite_manifest_mismatch')

    def test_manifest_missing(self):
        (self.path().parent / 'runs/aviation.data/run_manifest.json').unlink()
        self.assert_blocked('missing_file')

    def test_manifest_environment_disagrees_with_raw(self):
        self.mutate_manifest(lambda doc: doc.update(environment_digest='sha256:' + 'a' * 64))
        self.assert_blocked('raw_manifest_mismatch')

    def test_manifest_adapter_disagrees(self):
        self.mutate_manifest(lambda doc: doc.update(adapter='simulation_agent'))
        self.assert_blocked('raw_manifest_mismatch')

    def test_manifest_task_count_disagrees(self):
        self.mutate_manifest(lambda doc: doc.update(n_tasks=999))
        self.assert_blocked('suite_manifest_mismatch')

    def test_suite_manifest_hashes_are_recorded(self):
        report = self.report()
        self.assertTrue(all('aviation.data' in cell['manifest_sha256'] for cell in report['cells']))

    def test_run_and_manifest_wrong_seed_still_rejected_against_plan(self):
        self.mutate_doc(lambda doc: doc['identity'].update(seed=999))
        self.mutate_manifest(lambda doc: doc.update(seed=999))
        self.assert_blocked('seed_mismatch')

    def test_windows_reserved_id_rejected(self):
        for value in ('CON', 'aux.txt', 'COM1', 'name.'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                c.identifier(value)


if __name__ == '__main__':
    unittest.main()
