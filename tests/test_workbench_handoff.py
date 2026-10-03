"""Local handoff script: no solver, network, repo mutation or credential use."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'examples/workbench/local_acceptance.py'
spec=importlib.util.spec_from_file_location('local_acceptance',SCRIPT)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class HandoffTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.root=Path(temp.name);self.repo=self.root/'export';self.repo.mkdir()
        (self.repo/'source.py').write_text('# fixture, not actual repository\n')
        data={'repository':module.REPOSITORY,'base_commit':'a'*40,'scope':'unit-test-only',
              'files':{'source.py':module.hashed(self.repo/'source.py')}}
        (self.repo/'SOURCE_SNAPSHOT.json').write_text(json.dumps(data))

    def run_cli(self,*extra):
        return subprocess.run([sys.executable,str(SCRIPT),'--repo',str(self.repo),
                               '--out',str(self.root/'evidence'),*extra],capture_output=True,text=True,timeout=30)

    def test_preflight_does_not_claim_native_acceptance(self):
        p=self.run_cli();self.assertEqual(p.returncode,0,p.stderr)
        data=json.loads((self.root/'evidence/handoff-result.json').read_text())
        self.assertFalse(data['native_calibration_verified'])
        self.assertFalse(data['model_experiment_verified'])
        self.assertEqual(data['steps'],[])
        with zipfile.ZipFile(self.root/'evidence.zip') as z:
            self.assertIn('handoff-result.json',z.namelist())
            self.assertIn('evidence-manifest.json',z.namelist())

    def test_missing_binary_returns_blocked_evidence(self):
        p=self.run_cli('--run-native','--ccx',str(self.root/'not-a-binary'))
        self.assertEqual(p.returncode,2,p.stderr)
        data=json.loads((self.root/'evidence/handoff-result.json').read_text())
        self.assertIn('ccx_missing',data['error'])
        self.assertFalse(data['native_calibration_verified'])
        self.assertTrue((self.root/'evidence.zip').is_file())

    def test_changed_snapshot_and_unregistered_files_are_rejected(self):
        (self.repo/'source.py').write_text('changed')
        with self.assertRaisesRegex(ValueError,'snapshot_file_changed'):module.source_identity(self.repo)
        (self.repo/'source.py').write_text('# fixture, not actual repository\n')
        (self.repo/'another.py').write_text('# unexpected')
        with self.assertRaisesRegex(ValueError,'unregistered'):module.source_identity(self.repo)

    def test_wrong_head_and_existing_output_fail(self):
        with self.assertRaisesRegex(ValueError,'unexpected_HEAD'):module.source_identity(self.repo,'b'*40)
        (self.root/'evidence').mkdir()
        self.assertNotEqual(self.run_cli().returncode,0)
        self.assertFalse((self.root/'evidence.zip').exists())

    def test_source_under_os_directory_alias_is_accepted(self):
        alias=self.root/'alias'
        try: alias.symlink_to(self.root, target_is_directory=True)
        except OSError as exc: self.skipTest(f'directory symlinks unavailable: {exc}')
        self.assertEqual(module.source_identity(alias/'export'),module.source_identity(self.repo))

    def test_links_inside_snapshot_are_rejected_even_with_matching_hash(self):
        original=self.repo/'source.py'
        external=self.root/'external.py'
        external.write_bytes(original.read_bytes())
        original.unlink()
        try: original.symlink_to(external)
        except OSError as exc: self.skipTest(f'symlinks unavailable: {exc}')
        with self.assertRaisesRegex(ValueError,'snapshot_link'):module.source_identity(self.repo)

    def test_linked_subdirectory_inside_snapshot_is_rejected(self):
        external=self.root/'external';external.mkdir()
        (external/'source.py').write_text('# outside source')
        try: (self.repo/'nested').symlink_to(external,target_is_directory=True)
        except OSError as exc: self.skipTest(f'directory symlinks unavailable: {exc}')
        data=json.loads((self.repo/'SOURCE_SNAPSHOT.json').read_text())
        data['files']['nested/source.py']=module.hashed(external/'source.py')
        (self.repo/'SOURCE_SNAPSHOT.json').write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'snapshot_link'):module.source_identity(self.repo)


if __name__=='__main__':unittest.main()
