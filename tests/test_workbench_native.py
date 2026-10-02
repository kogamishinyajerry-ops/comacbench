"""Native bridge control tests. Synthetic .dat/process doubles are NOT FEA evidence."""
from __future__ import annotations
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from comacbench import workbench as wb
from comacbench import workbench_ccx as ccx
from comacbench import workbench_structures as family
from comacbench.workbench_report import export_report

ROOT = Path(__file__).resolve().parents[1]


def scenario():
    return wb.read_json(ROOT / 'examples/workbench/structures-change-v1.json')


def synthetic_dat(force):
    # Literal beam-theory slope used ONLY as a test double, not a native result.
    _, _, roots, tips = ccx.mesh()
    lines = [' displacements (vx,vy,vz) for set NTIP and time 0.1000000E+01', '']
    lines += [f'{n} 0.0 {force * 0.0038095238095238095:.10E} 0.0' for n in tips]
    lines += ['', ' forces (fx,fy,fz) for set NROOT and time 0.1000000E+01', '']
    lines += [f'{n} 0.0 {-force / len(roots):.10E} 0.0' for n in roots]
    return '\n'.join(lines) + '\n'


def fake_process(command, root, log, timeout):
    force = wb.read_json(root / 'request.json')['force_y_n']
    (root / 'model.dat').write_text(synthetic_dat(force), encoding='ascii')
    (root / 'model.frd').write_text('SYNTHETIC TEST DOUBLE, NOT SOLVER OUTPUT\n', encoding='ascii')
    log.write_text('SYNTHETIC TEST DOUBLE\nJob finished\n', encoding='ascii')
    return {'exit_code': 0, 'timed_out': False, 'output_limit': False,
            'launch_error': None, 'duration_s': 0.1, 'process_started': True}


class NativeBridgeTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.session = self.root / 'session'
        binary = Path(sys.executable).resolve()
        self.bound = {'path':str(binary), 'sha256':ccx.sha(binary), 'version':'2.23',
                      'version_output':'TEST DOUBLE, NOT A SOLVER', 'version_exit_code':0, 'os':os.name,
                      'trust_scope':'operator_supplied_local_binary_not_attestation',
                      'library_env_sha256':wb.digest({k:os.environ.get(k) for k in ('LD_LIBRARY_PATH','DYLD_LIBRARY_PATH')})}
        self.probe = mock.patch.object(ccx, 'executor', return_value=self.bound).start()
        self.process = mock.patch.object(ccx, '_process', side_effect=fake_process).start()
        self.addCleanup(mock.patch.stopall)
        self.scenario = scenario()

    def start(self):
        return wb.start(self.session, self.scenario, {'name':'TEST DOUBLE','revision':'1','kind':'negative_control'})

    def act(self, action):
        return wb.act(self.session, action)

    def stage(self):
        obs = wb.observe(self.session)
        for target in ('solution_limit','solution_service'):
            if obs['statuses'][target] != 'verified':
                self.assertTrue(self.act({'op':'solve','target':target})['result']['ok'])
                result = self.act({'op':'check','target':target})
                self.assertTrue(result['result']['ok'])
                obs = result['observation']
        cases = []
        for name in ('limit','service'):
            q = obs['artifacts']['solution_'+name]['payload']['qoi']
            cases.append({'point':name, **q,
                          'meets_requirement':abs(q['uy_mm']) <= obs['sources']['requirement']['max_tip_mm']})
        payload = {'cases':cases, 'claim':'requirements_met' if all(r['meets_requirement'] for r in cases) else 'needs_review',
                   'requirement_revision':obs['sources']['requirement']['revision']}
        self.act({'op':'put','target':'review','basis':obs['dependencies']['review'],'payload':payload})
        self.assertTrue(self.act({'op':'check','target':'review'})['result']['ok'])
        return wb.observe(self.session)

    def complete(self):
        self.start()
        self.stage()
        self.act({'op':'advance'})
        self.stage()
        self.act({'op':'advance'})
        self.stage()
        return self.act({'op':'submit','claim':'needs_review'})

    def test_complete_three_phases_uses_three_solve_attempts(self):
        result = self.complete()
        self.assertTrue(result['observation']['complete'])
        self.assertEqual(result['observation']['actions_used'], 15)
        self.assertEqual(result['observation']['counts']['solver_calls'], 3)
        self.assertEqual(self.process.call_count, 3)
        self.assertFalse(result['observation']['limitations']['publishable'])
        self.assertEqual(result['observation']['artifacts']['review']['payload']['claim'], 'needs_review')

    def test_load_change_retains_other_native_job(self):
        self.start(); before = self.stage()
        change = self.act({'op':'advance'})
        self.assertEqual(change['result']['retained'], ['solution_service'])
        self.assertEqual(set(change['result']['invalidated']), {'solution_limit','review'})
        after = self.stage()
        self.assertEqual(before['artifacts']['solution_service'], after['artifacts']['solution_service'])
        self.assertNotEqual(before['artifacts']['solution_limit'], after['artifacts']['solution_limit'])

    def test_requirement_change_does_not_rerun_solver(self):
        self.start(); self.stage(); self.act({'op':'advance'}); before = self.stage()
        change = self.act({'op':'advance'})
        self.assertEqual(change['result']['invalidated'], ['review'])
        self.stage()
        self.assertEqual(self.process.call_count, 3)
        for key in ('solution_service','solution_limit'):
            self.assertEqual(before['artifacts'][key], wb.observe(self.session)['artifacts'][key])

    def test_stale_results_cannot_submit(self):
        self.start(); self.stage(); self.act({'op':'advance'})
        self.assertEqual(self.act({'op':'submit','claim':'requirements_met'})['result']['code'], 'unverified_targets')

    def test_false_claim_is_retained(self):
        self.start(); self.stage(); self.act({'op':'advance'}); self.stage(); self.act({'op':'advance'}); self.stage()
        result = self.act({'op':'submit','claim':'requirements_met'})
        self.assertEqual(result['result']['code'], 'false_completion_claim')
        self.assertFalse(result['observation']['complete'])
        self.assertTrue(self.act({'op':'submit','claim':'needs_review'})['observation']['complete'])
        self.assertEqual(wb.snapshot(self.session)['events'][-2]['result']['code'], 'false_completion_claim')

    def test_agent_cannot_put_native_metrics(self):
        obs = self.start()
        result = self.act({'op':'put','target':'solution_limit','basis':obs['dependencies']['solution_limit'],
                           'payload':{'valid':True,'qoi':{'uy_mm':0,'rfy_n':120}}})
        self.assertEqual(result['result']['code'], 'native_artifact_is_broker_owned')
        self.assertEqual(self.process.call_count, 0)

    def test_invalid_solve_never_starts_process(self):
        self.start()
        for action in ({'op':'solve','target':'review'}, {'op':'solve','target':[]},
                       {'op':'solve','target':'solution_limit','command':['rm']}, {'op':'solve','target':'../escape'}):
            self.assertFalse(self.act(action)['result']['ok'])
        self.assertEqual(self.process.call_count, 0)
        self.assertEqual(wb.observe(self.session)['actions_used'], 4)

    def test_public_observation_supplies_accepted_action_format(self):
        obs=self.start()
        contract=obs['contract']['action_format']
        example=contract['solve_example']
        self.assertEqual(set(example),set(contract['required_fields']['solve']))
        self.assertEqual(example[contract['selector']],'solve')
        result=self.act(example)
        self.assertTrue(result['result']['ok'])
        checked=self.act({contract['selector']:'check','target':example['target']})
        self.assertTrue(checked['result']['ok'])

    def test_call_budget_includes_failed_attempts(self):
        self.scenario['max_solver_calls'] = 1
        self.start()
        def broken(*args):
            result = fake_process(*args); result['exit_code'] = 1; return result
        self.process.side_effect = broken
        first = self.act({'op':'solve','target':'solution_limit'})
        self.assertFalse(first['result']['ok'])
        self.assertEqual(self.act({'op':'solve','target':'solution_limit'})['result']['code'], 'native_solve_target_or_budget')
        self.assertEqual(self.process.call_count, 1)
        self.assertEqual(first['observation']['counts']['solver_calls'], 1)

    def test_process_failure_overrules_correct_looking_dat(self):
        self.start()
        for code, timeout in ((1,False),(201,False),(0,True)):
            def broken(*args):
                r = fake_process(*args); r.update(exit_code=code,timed_out=timeout); return r
            self.process.side_effect = broken
            r = self.act({'op':'solve','target':'solution_limit'})
            self.assertFalse(r['result']['ok'])
            self.assertFalse(self.act({'op':'check','target':'solution_limit'})['result']['ok'])

    def test_missing_termination_marker_fails(self):
        self.start()
        def broken(command, root, log, timeout):
            r = fake_process(command, root, log, timeout); log.write_text('No completion marker\n'); return r
        self.process.side_effect = broken
        self.assertFalse(self.act({'op':'solve','target':'solution_limit'})['result']['ok'])

    def test_error_marker_even_with_finished_fails(self):
        self.start()
        def broken(command, root, log, timeout):
            r = fake_process(command, root, log, timeout); log.write_text('*ERROR\nJob finished\n'); return r
        self.process.side_effect = broken
        self.assertFalse(self.act({'op':'solve','target':'solution_limit'})['result']['ok'])

    def test_no_dat_is_failed_attempt_not_success(self):
        self.start()
        def broken(command, root, log, timeout):
            r = fake_process(command, root, log, timeout); (root/'model.dat').unlink(); return r
        self.process.side_effect = broken
        self.assertFalse(self.act({'op':'solve','target':'solution_limit'})['result']['ok'])
        self.assertEqual(wb.observe(self.session)['counts']['solver_calls'], 1)

    def test_changed_executable_is_not_silently_replaced(self):
        self.bound['sha256'] = 'b'*64
        self.start()
        result = self.act({'op':'solve','target':'solution_limit'})
        self.assertFalse(result['result']['ok'])
        self.assertEqual(self.process.call_count, 0)
        self.assertEqual(result['observation']['limitations']['solver_execution'], 'not_performed')

    def job(self):
        self.start(); self.act({'op':'solve','target':'solution_limit'})
        return self.session/'native/000001'

    def test_tampered_raw_data_blocks_replay(self):
        job = self.job(); (job/'model.dat').write_text('tampered')
        with self.assertRaisesRegex(wb.WorkbenchError,'native_archive_changed'):
            wb.observe(self.session)

    def test_extra_native_file_blocks_replay(self):
        job = self.job(); (job/'best-result.dat').write_text('unregistered')
        with self.assertRaisesRegex(wb.WorkbenchError,'native_archive_changed'):
            wb.observe(self.session)

    def test_changed_deck_cannot_pass_with_updated_file_hashes(self):
        job = self.job(); (job/'model.inp').write_text('*INCLUDE,INPUT=outside\n')
        (job/'receipt.json').write_bytes(wb.canonical({'protocol':'comacbench.native-job.v1','files':ccx._inventory(job)}))
        with self.assertRaisesRegex(wb.WorkbenchError,'native_input_mismatch'):
            wb.observe(self.session)

    def test_changed_receipt_cannot_pass_event_replay(self):
        job = self.job(); (job/'model.dat').write_text(synthetic_dat(-119.999))
        (job/'receipt.json').write_bytes(wb.canonical({'protocol':'comacbench.native-job.v1','files':ccx._inventory(job)}))
        with self.assertRaisesRegex(wb.WorkbenchError,'event_result_mismatch'):
            wb.observe(self.session)

    def test_interrupted_job_cannot_be_ignored_or_retried(self):
        self.start()
        def interrupt(command, root, log, timeout):
            raise OSError('synthetic interruption after reservation')
        self.process.side_effect = interrupt
        with self.assertRaises(OSError): self.act({'op':'solve','target':'solution_limit'})
        self.assertTrue((self.session/'native/000001/request.json').exists())
        with self.assertRaisesRegex(wb.WorkbenchError,'interrupted_native_job'):
            wb.observe(self.session)
        with self.assertRaises(wb.WorkbenchError): self.act({'op':'solve','target':'solution_limit'})
        self.assertEqual(self.process.call_count, 1)

    def test_deleted_event_with_native_job_is_not_silently_discarded(self):
        self.job(); (self.session/'events/000001.json').unlink()
        with self.assertRaisesRegex(wb.WorkbenchError,'interrupted_native_job'):
            wb.observe(self.session)

    def test_reporting_replays_without_new_solver_calls(self):
        self.complete(); result = export_report(self.session, self.root/'report')
        self.assertTrue(result['complete']); self.assertEqual(self.process.call_count, 3)
        self.assertEqual(len(list((self.root/'report/native').iterdir())), 3)
        for job in (self.session/'native').iterdir():
            self.assertEqual(ccx._inventory(job), ccx._inventory(self.root/'report/native'/job.name))
        text = (self.root/'report/report.html').read_text()
        self.assertIn('limit', text)
        self.assertNotIn('未运行工程求解器', text)

    def test_module_cli_reports_tampering_as_structured_failure(self):
        self.complete()
        dat=next((self.session/'native').glob('*/model.dat'))
        with dat.open('a') as f: f.write('\nINTENTIONAL_TEST_TAMPER\n')
        for command in (['observe',str(self.session)],
                        ['report',str(self.session),'--out',str(self.root/'bad-report')]):
            p=subprocess.run([sys.executable,'-m','comacbench.workbench',*command],
                             cwd=ROOT,capture_output=True,text=True,timeout=30)
            self.assertEqual(p.returncode,2,p.stderr)
            self.assertEqual(json.loads(p.stderr),{'error':'native_archive_changed'})
            self.assertNotIn('Traceback',p.stderr)
        self.assertFalse((self.root/'bad-report').exists())

    def test_copy_session_can_be_reverified_without_binary_present(self):
        self.complete()
        moved = self.root/'moved'; shutil.copytree(self.session,moved)
        with mock.patch.object(ccx,'executor',side_effect=AssertionError('must not probe')):
            self.assertTrue(wb.observe(moved)['complete'])
        self.assertEqual(self.process.call_count, 3)

    def test_reference_policy_reads_native_observations(self):
        spec = importlib.util.spec_from_file_location('native_reference', ROOT/'examples/workbench/native_reference.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        result = module.perform(self.root/'reference')
        self.assertTrue(result['complete']); self.assertEqual(self.process.call_count,3)
        self.assertEqual(wb.observe(self.root/'reference/session')['actions_used'],15)

    def test_native_reference_negative_examples(self):
        spec = importlib.util.spec_from_file_location('native_reference', ROOT/'examples/workbench/native_reference.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        for mode in ('stale','false-ready'):
            self.assertFalse(module.perform(self.root/mode,negative=mode)['complete'])


class NativeParserTests(unittest.TestCase):
    def test_known_literal_values_and_fortran_exponent(self):
        text = synthetic_dat(-100).replace('E','D')
        # Replacing E changes header names too; restore NTIP/NROOT unaffected.
        result = ccx.parse_dat(text)
        self.assertAlmostEqual(result['uy_mm'],-0.38095238095,places=9)
        self.assertAlmostEqual(result['rfy_n'],100,places=7)

    def test_mesh_geometry_rosters_and_element_count(self):
        nodes,elements,roots,tips = ccx.mesh()
        self.assertEqual((len(nodes),len(elements),len(roots),len(tips)),(1077,160,37,37))
        self.assertTrue(set(roots).isdisjoint(tips))
        self.assertTrue(all(len(set(c))==20 for _,c in elements))
        self.assertEqual(max(n[1] for n in nodes),100)

    def test_fixed_deck_has_no_include_and_total_load_is_correct(self):
        text = ccx.deck(-140).decode()
        self.assertNotIn('*INCLUDE',text)
        lines = text.splitlines(); total = 0
        for i,line in enumerate(lines):
            if line == '*CLOAD': total += float(lines[i+1].split(',')[2])
        self.assertAlmostEqual(total,-140,places=8)
        self.assertIn('*NODE FILE\nU, RF',text)

    def test_invalid_force_is_rejected(self):
        for force in (True,0,-1000,float('nan'),float('inf'),'100'):
            with self.assertRaises(wb.WorkbenchError): ccx.deck(force)

    def test_final_time_wrong(self):
        with self.assertRaisesRegex(wb.WorkbenchError,'not_final'):
            ccx.parse_dat(synthetic_dat(-100).replace('0.1000000E+01','0.5000000E+00'))

    def test_duplicate_block_is_rejected(self):
        with self.assertRaisesRegex(wb.WorkbenchError,'block_count'):
            ccx.parse_dat(synthetic_dat(-100)*2)

    def test_missing_or_duplicate_node_is_rejected(self):
        lines = synthetic_dat(-100).splitlines()
        for changed in (lines[:2]+lines[3:], lines[:3]+[lines[2]]+lines[3:]):
            with self.assertRaises(wb.WorkbenchError): ccx.parse_dat('\n'.join(changed))

    def test_nonfinite_and_wrong_set_rejected(self):
        text = synthetic_dat(-100)
        for changed in (text.replace('NTIP','OTHER'),text.replace('-3.8095238095E-01','1E999')):
            with self.assertRaises(wb.WorkbenchError): ccx.parse_dat(changed)

    def test_invalid_scenario_fields_fail_closed(self):
        edits = ({'max_solver_calls':True},{'solve_timeout_s':0},{'loads':[]},{'phases':[None]},
                 {'requirement':{'revision':'A','max_tip_mm':True}})
        for edit in edits:
            s = scenario(); s.update(edit)
            with self.assertRaises(wb.WorkbenchError): wb.validate_scenario(s)


class RealSubprocessGuardTests(unittest.TestCase):
    def probe(self, text='\nThis is Version 2.23\n\n', **changes):
        def process(command, root, log, timeout):
            self.assertEqual(command[1:], ['-v'])
            log.write_text(text)
            return dict(exit_code=201,timed_out=False,output_limit=False,launch_error=None,
                        duration_s=0.01,process_started=True) | changes
        with mock.patch.object(ccx,'_process',side_effect=process):
            return ccx.executor(sys.executable)

    def test_upstream_version_query_stop_status_is_recorded(self):
        for code in (0,201):
            bound=self.probe(exit_code=code)
            self.assertEqual(bound['version_exit_code'],code)
            ccx.validate_executor(bound)

    def test_version_banner_does_not_hide_process_failures(self):
        for change in ({'exit_code':1},{'exit_code':-9},{'timed_out':True},
                       {'output_limit':True},{'launch_error':'OSError'},{'process_started':False}):
            with self.subTest(change=change),self.assertRaisesRegex(wb.WorkbenchError,'version_unverified'):
                self.probe(**change)

    def test_version_probe_rejects_wrong_ambiguous_or_error_output(self):
        for text in ('This is Version 2.22','This is Version 2.230','Version 2.23',
                     'This is Version 2.23\n*ERROR in loader',
                     'This is Version 2.23\nThis is Version 2.23'):
            with self.subTest(text=text),self.assertRaisesRegex(wb.WorkbenchError,'version_unverified'):
                self.probe(text)

    def test_timeout_kills_real_test_process(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            result=ccx._process([sys.executable,'-c','import time;time.sleep(60)'],root,root/'test.log',0.2)
            self.assertTrue(result['process_started']);self.assertTrue(result['timed_out'])
            self.assertIsNotNone(result['exit_code']);self.assertLess(result['duration_s'],15)

    def test_normal_process_exit_is_recorded(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            result=ccx._process([sys.executable,'-c','print("test process, not CCX")'],root,root/'test.log',5)
            self.assertEqual(result['exit_code'],0);self.assertFalse(result['timed_out'])

    def test_explicit_missing_binary_does_not_fall_back(self):
        with mock.patch('shutil.which',return_value=sys.executable):
            with self.assertRaises(OSError): ccx.executor('/definitely-absent-comacbench-ccx')


@unittest.skipUnless(os.environ.get('COMACBENCH_TEST_CCX'), 'native CalculiX explicitly opt-in; fixture tests are not solver evidence')
class OptInNativeTests(unittest.TestCase):
    def test_real_native_reference_three_stages(self):
        spec=importlib.util.spec_from_file_location('native_reference', ROOT/'examples/workbench/native_reference.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as d:
            result=module.perform(Path(d)/'native',ccx=os.environ['COMACBENCH_TEST_CCX'])
            self.assertTrue(result['complete'])
            obs=wb.observe(Path(d)/'native/session')
            self.assertEqual(obs['counts']['solver_calls'],3)
            self.assertEqual(obs['artifacts']['review']['payload']['claim'],'needs_review')


if __name__=='__main__': unittest.main()
