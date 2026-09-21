"""Evidence admission at the same public pack boundary used by the plugin."""
import sys
import tempfile
import shutil
import unittest
from pathlib import Path
import yaml
from comacbench.admission import validate_pack

ROOT = Path(__file__).resolve().parents[1]

class EvidenceAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pack = Path(self.tmp.name)/'pack'
        shutil.copytree(ROOT/'packs/aviation-cfd-step-v1', self.pack)

    def change(self, value):
        p = self.pack/'pack.yaml'
        d = yaml.safe_load(p.read_text())
        d['validation_evidence'] = value
        p.write_text(yaml.safe_dump(d, allow_unicode=True))

    def test_unknown_or_failed_study_cannot_authorize_launch(self):
        self.change({'protocol':'comacbench.research-links.v1', 'purpose':'research_support',
                     'studies':['re300-v1']})
        result = validate_pack(self.pack)
        self.assertFalse(result['runnable'])
        self.assertIn('unknown_research_evidence', [i['code'] for i in result['issues']])


class EvidencePolicyTests(EvidenceAdmissionTests):
    def test_missing_evidence_is_blocked(self):
        self.change(None)
        self.assertFalse(validate_pack(self.pack)['runnable'])

    def test_research_cannot_authorize_score_tolerance(self):
        self.change({'protocol':'comacbench.research-links.v1', 'purpose':'scoring_calibration',
                     'studies':['bfs-re100-validated-v1']})
        self.assertFalse(validate_pack(self.pack)['runnable'])

    def test_other_reynolds_cannot_replace_re100(self):
        self.change({'protocol':'comacbench.research-links.v1', 'purpose':'research_support',
                     'studies':['bfs-re200-validated-v1']})
        r = validate_pack(self.pack)
        self.assertIn('research_scope_mismatch', [i['code'] for i in r['issues']])
        self.assertFalse(r['runnable'])

    def test_three_accepted_matrices_do_not_add_scorable_tasks(self):
        self.change({'protocol':'comacbench.research-links.v1', 'purpose':'research_support',
                     'studies':[f'bfs-re{re}-validated-v1' for re in [100,200,300]]})
        r = validate_pack(self.pack)
        self.assertTrue(r['runnable'], r['issues'])
        self.assertEqual(r['task_count'], 1)
        self.assertFalse(r['publishable'])
        self.assertEqual([e['matrix_cases'] for e in r['validation_evidence']], [16,16,16])
        self.assertEqual([e['candidate_relative_tolerance'] for e in r['validation_evidence']], [.025,.02,.02])
        self.assertTrue(all(e['calibrated_tolerance'] is None for e in r['validation_evidence']))

    def test_tightening_public_tolerance_still_rejected(self):
        self.change({'protocol':'comacbench.research-links.v1', 'purpose':'research_support',
                     'studies':['bfs-re100-validated-v1']})
        p = self.pack/'tasks/aviation.cfd/backward_step_01.yaml'
        d = yaml.safe_load(p.read_text()); d['reference']['rel_tol'] = .025
        d['grader']['numeric_rel_tol'] = .025
        p.write_text(yaml.safe_dump(d))
        self.assertFalse(validate_pack(self.pack)['runnable'])

class EvidenceIntegrityTests(unittest.TestCase):
    def test_missing_and_modified_analysis_are_rejected(self):
        from comacbench.evidence import catalog, verify_study
        import copy
        study = copy.deepcopy(catalog()[0])
        # Keep just the real pinned analysis anchor to isolate this boundary fault.
        study['anchors'] = {study['analysis']: study['anchors'][study['analysis']]}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ValueError): verify_study(study, root)
            p = root/study['analysis']; p.parent.mkdir(parents=True)
            p.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'digest_mismatch'): verify_study(study, root)

class AdmissionExecutionTests(unittest.TestCase):
    def test_calibration_persists_evidence_entrypoint_for_resume(self):
        import subprocess
        import json
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp)/'pack'
            shutil.copytree(ROOT/'packs/aviation-core-v1', pack)
            meta = yaml.safe_load((pack/'pack.yaml').read_text())
            meta['suites'] = [s for s in meta['suites'] if s['id'] == 'enterprise.data']
            (pack/'pack.yaml').write_text(yaml.safe_dump(meta, allow_unicode=True))
            out = Path(tmp)/'run'
            # sys.executable is the venv interpreter on both POSIX (bin/python) and Windows (Scripts/python.exe)
            command = [sys.executable, '-m', 'comacbench.admission', 'calibrate', str(pack), '--out', str(out)]
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            state = json.loads((out/'run.json').read_text())
            self.assertTrue(state['calibration_passed'])
            self.assertIn('-m comacbench.admission calibrate ', state['rerun'])
            self.assertIn('validation_evidence', state['validation'])
            result = subprocess.run(command+['--resume'], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)

if __name__ == '__main__':
    unittest.main()
