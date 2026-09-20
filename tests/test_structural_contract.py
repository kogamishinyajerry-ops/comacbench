"""Public runner and contribution contracts for the bounded cantilever profile."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml
from runners.common import TaskSpec
from runners.simulation_agent import run_task

ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / 'packs/aviation-core-v1'
CONTRACT = {
    'profile': 'ccx.cantilever.v1',
    'geometry_mm': [100, 10, 5],
    'min_elements': [16, 4, 2],
    'material': {'youngs_modulus_mpa': 210000, 'poisson_ratio': .3,
                 'density_tonne_mm3': 7.85e-9},
    'total_fy_n': -1000,
}


def evaluate(code, contract=True):
    p = V1 / 'tasks/aviation.structures/beam_static_01.yaml'
    spec = yaml.safe_load(p.read_text())
    if contract:
        spec['grader']['deck_contract'] = copy.deepcopy(CONTRACT)
    task = TaskSpec(spec, p)
    with patch('runners.simulation_agent.get_answer', return_value={
            'answer': code, 'meta': {'provider': 'external', 'model': 'recorded-test'}}):
        return run_task(task, provider='external', model='recorded-test', seed=0,
                        env_digest='test-env', prompt_cache={task.id: p.with_suffix('.md').read_text()},
                        assets_root=V1, oracle_cache=None)


class StructuralContractTests(unittest.TestCase):
    def test_historical_disconnected_tip_load_is_rejected_before_solver(self):
        for model in ('minimax-live-v2', 'glm-live-v2'):
            with self.subTest(model=model):
                deck = (ROOT / 'report/2026-09-06-aviation-plugin-v1/structural-diagnosis'
                        / model / 'model.inp').read_text()
                result = evaluate('from pathlib import Path\nPath("model.inp").write_text(' + repr(deck) + ')')
                self.assertEqual(result['validity_gate'], 0)
                self.assertEqual(result['score'], 0)
                details = json.loads(result['artifacts']['grade_details'])
                audit = details['deck_audit']
                issue = next(i for i in audit['issues'] if i['code'] == 'unconnected_loaded_nodes')
                self.assertEqual(issue['details']['count'], 8)
                self.assertNotIn('ccx_s', details)


class DeckAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import subprocess
        import sys
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run([sys.executable, str(V1 / 'private/beam_static_01.py')], cwd=tmp, check=True)
            cls.good = (Path(tmp) / 'model.inp').read_text()

    def audit(self, deck):
        from runners.solvers.cantilever_contract import audit_cantilever_deck
        return audit_cantilever_deck(deck, CONTRACT)

    def test_mesh_material_boundary_and_load_faults(self):
        faults = {
            'mesh': self.good.replace('100.000000', '99.000000'),
            'material': self.good.replace('210000.0, 0.3', '21000.0, 0.3'),
            'boundary': self.good.replace('NROOT, 1, 3, 0.0', 'NROOT, 1, 2, 0.0'),
            'load': self.good.replace('*CLOAD\n', '*CLOAD\nNROOT, 2, -1\n', 1),
            'output': self.good.replace('*NODE PRINT, NSET=NROOT\nRF', '*NODE PRINT, NSET=NROOT\nU'),
        }
        for check, deck in faults.items():
            with self.subTest(check=check):
                result = self.audit(deck)
                self.assertFalse(result['passed'])
                self.assertIn(check, {i['check'] for i in result['issues']})

    def test_native_solver_result_keeps_full_evidence_and_completed_audit(self):
        result = evaluate((V1 / 'private/beam_static_01.py').read_text())
        self.assertEqual(result['score'], 1)
        details = json.loads(result['artifacts']['grade_details'])
        self.assertTrue(details['deck_audit']['passed'])
        evidence = json.loads(result['artifacts']['engineering_evidence'])
        import hashlib
        self.assertTrue(evidence['complete'])
        for name in ('make_case.py', 'model.inp', 'model.dat', 'model.solver.log'):
            file = evidence['files'][name]
            self.assertEqual(hashlib.sha256(file['text'].encode()).hexdigest(), file['sha256'])
        self.assertIn('Job finished', evidence['files']['model.solver.log']['text'])

    def test_rejects_mesh_and_dialect_failures_with_specific_feedback(self):
        import re
        faults = {
            'unsupported_deck_feature': self.good.replace('*STEP', '*STEP, NLGEOM'),
            'unsupported_element_type': self.good.replace('TYPE=C3D20', 'TYPE=C3D20R'),
            'invalid_deck': self.good.replace('210000.0, 0.3', 'NaN, 0.3'),
            'undefined_connectivity': self.good.replace('*ELEMENT, TYPE=C3D20, ELSET=EALL\n1, 1,', '*ELEMENT, TYPE=C3D20, ELSET=EALL\n1, 999999,', 1),
            'material_assignment': self.good.replace('*SOLID SECTION, ELSET=EALL, MATERIAL=STEEL', '** missing material assignment'),
            'invalid_c3d20_geometry': self.good.replace('2.500000', '2.400000', 1),
            'nonfinite_load_sum': self.good.replace('*CLOAD', '*CLOAD\nNTIP, 2, 1e308', 1),
        }
        for code, deck in faults.items():
            with self.subTest(code=code):
                result = self.audit(deck)
                self.assertFalse(result['passed'])
                self.assertIn(code, {i['code'] for i in result['issues']})
                json.dumps(result, allow_nan=False)

    def test_valid_sets_generate_case_and_additive_loads(self):
        # Existing node IDs span 1..N, using GENERATE only for an unused named set.
        nodes = self.good.split('*ELEMENT')[0].splitlines()[1:]
        maximum = max(int(row.split(',')[0]) for row in nodes)
        deck = self.good.replace('*MATERIAL', f'*NSET, NSET=ALL, GENERATE\n1,{maximum}\n*NSET, NSET=ROOT_ALIAS\nNROOT\n*MATERIAL', 1)
        deck = deck.replace('NROOT, 1, 3, 0.0', 'ROOT_ALIAS, 1\nROOT_ALIAS, 2, 3')
        deck = deck.replace('*ELASTIC', '*ELASTIC, TYPE=ISOTROPIC')
        # Splitting the same nodal load across two CLOAD cards must sum identically.
        import re
        deck = re.sub(r'\*CLOAD\n(\d+), 2, (-?[\d.]+)',
                      lambda m: f'*CLOAD\n{m[1]}, 2, {float(m[2])/2}\n*CLOAD\n{m[1]}, 2, {float(m[2])/2}', deck)
        result = self.audit(deck.lower())
        self.assertTrue(result['passed'], result['issues'])

    def test_generated_dat_cannot_substitute_for_solver_output(self):
        code = (V1 / 'private/beam_static_01.py').read_text() + '\nopen("model.dat", "w").write("FAKE SOLVER DATA")'
        with patch('runners.solvers.calculix.run_ccx', return_value={
                'exit': 0, 'timeout': False, 'duration_s': .01, 'stdout_tail': ''}):
            result = evaluate(code)
        self.assertEqual(result['validity_gate'], 0)
        evidence = json.loads(result['artifacts']['engineering_evidence'])
        self.assertNotIn('model.dat', evidence['files'])

    def test_reference_passes_all_six_engineering_checks(self):
        result = self.audit(self.good)
        self.assertTrue(result['passed'], result['issues'])
        self.assertEqual({x['id'] for x in result['checks']},
                         {'connectivity', 'mesh', 'material', 'boundary', 'load', 'output'})


class StructuralPackTests(unittest.TestCase):
    def test_structural_pack_maps_all_six_checks(self):
        from comacbench.pack import validate_pack
        result = validate_pack(ROOT / 'packs/aviation-structures-v2')
        self.assertTrue(result['runnable'], result['issues'])
        self.assertFalse(result['publishable'])
        self.assertNotIn('partial_engineering_gate', {i['code'] for i in result['issues']})

    def test_calibration_rejects_wrong_failure_reason_even_at_zero_score(self):
        from subprocess import run, PIPE
        import shutil
        import sys
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'pack'; shutil.copytree(ROOT / 'packs/aviation-structures-v2', root)
            p = root / 'tasks/aviation.structures/beam_static_01.yaml'
            spec = yaml.safe_load(p.read_text())
            spec['evaluation']['negative_controls'] = [{'script':'private/wrong_material.py', 'max_score':0, 'expected_issue':'clamp_mismatch'}]
            p.write_text(yaml.safe_dump(spec))
            out = Path(tmp) / 'calibration'
            proc = run([sys.executable, '-m', 'comacbench', 'calibrate', str(root), '--out', str(out)], cwd=ROOT, stdout=PIPE, stderr=PIPE, text=True)
            self.assertEqual(proc.returncode, 3, proc.stderr)
            report = json.loads((out / 'run.json').read_text())
            self.assertFalse(report['calibration_passed'])
            control = report['controls'][0]
            self.assertEqual(control['score'], 0)
            self.assertFalse(control['passed'])
            self.assertIn('material_mismatch', control['actual_issues'])

    def test_malformed_or_conflicting_contract_blocks_contribution(self):
        from comacbench.pack import validate_pack
        import shutil
        mutations = [lambda t: t['grader'].update(deck_contract=None),
                     lambda t: t['grader']['deck_contract'].update(total_fy_n=-500),
                     lambda t: t['grader']['deck_contract'].update(min_elements=[0,4,2]),
                     lambda t: t['grader']['deck_contract']['material'].pop('density_tonne_mm3'),
                     lambda t: t['grader']['extract']['root_rf_sum_n'].update(set='NTIP'),
                     lambda t: t['evaluation']['negative_controls'][0].update(expected_issue='made_up_check')]
        for change in mutations:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / 'pack'; shutil.copytree(ROOT / 'packs/aviation-structures-v2', root)
                p = root / 'tasks/aviation.structures/beam_static_01.yaml'
                t = yaml.safe_load(p.read_text()); change(t); p.write_text(yaml.safe_dump(t))
                result = validate_pack(root)
                self.assertFalse(result['runnable'])
                self.assertTrue(any(i['code'] in {'invalid_deck_contract', 'deck_reference_mismatch', 'unknown_expected_issue'} for i in result['issues']), result['issues'])


if __name__ == '__main__':
    unittest.main()
