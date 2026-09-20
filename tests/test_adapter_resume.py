"""The shared resume guarantee must be enforced by every adapter CLI."""
from pathlib import Path
import json
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SUITES = {
    'code_exec': 'humaneval.python',
    'field_prediction': 'superwing.coeff_lite',
    'simulation_agent': 'cfdb.case_setup',
    'design_artifact': 'spreadsheetbench.verified_subset',
}

class AdapterResumeTests(unittest.TestCase):
    def test_all_adapter_clis_refuse_mixed_seed_and_preserve_valid_cache(self):
        for adapter, suite in SUITES.items():
            with self.subTest(adapter=adapter), tempfile.TemporaryDirectory(prefix='comac-adapter-') as temp:
                root = Path(temp)
                tasks = root/'tasks'/suite
                tasks.mkdir(parents=True)
                (root/'data').symlink_to(ROOT/'data', target_is_directory=True)
                p = sorted((ROOT/'tasks'/suite).glob('*.yaml'))[0]
                shutil.copy2(p, tasks/p.name)
                shutil.copy2(p.with_suffix('.md'), tasks/p.with_suffix('.md').name)
                out = root/'out'
                command = [sys.executable, '-m', 'runners.'+adapter,
                           '--tasks', str(tasks), '--out', str(out), '--provider', 'stub']
                if adapter == 'design_artifact':
                    scaffold = root/'workflow notes.md'
                    scaffold.write_text('Check every required output before finishing.')
                    command += ['--iterate','2','--limit','1','--scaffold',str(scaffold)]
                first = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=30)
                self.assertEqual(first.returncode, 0, first.stderr)
                row_path = next(out.glob('result_*.json'))
                row = json.loads(row_path.read_text())
                self.assertNotEqual(row['failure_mode'], 'crash', first.stdout)
                manifest = json.loads((out/'run_manifest.json').read_text())
                replay = shlex.split(manifest['rerun_command'])
                replay = replay[replay.index('&&')+1:]
                self.assertEqual(replay[0], sys.executable)
                if adapter == 'design_artifact':
                    self.assertEqual(manifest['extra']['python'], sys.executable)
                    self.assertEqual(manifest['n_tasks'], 1)
                    for flag, value in [('--iterate','2'),('--limit','1'),('--scaffold',str(scaffold))]:
                        self.assertEqual(replay[replay.index(flag)+1],value)
                before = {f.name:f.read_bytes() for f in out.iterdir() if not f.name.startswith('.')}
                mixed = subprocess.run(command+['--seed','99','--resume'], cwd=ROOT, text=True, capture_output=True, timeout=30)
                self.assertNotEqual(mixed.returncode, 0, adapter+' accepted mismatched seed')
                self.assertIn('[resume]', mixed.stderr)
                self.assertEqual({f.name:f.read_bytes() for f in out.iterdir() if not f.name.startswith('.')}, before)
                valid = subprocess.run(replay, cwd=ROOT, text=True, capture_output=True, timeout=30)
                self.assertEqual(valid.returncode, 0, valid.stderr)
                self.assertEqual(row_path.read_bytes(), before[row_path.name])
                self.assertEqual(json.loads((out/'run_manifest.json').read_text())['extra']['resumed_tasks'], 1)

if __name__ == '__main__':
    unittest.main()
