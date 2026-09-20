"""A hidden run must be replayable by its recorded CLI, including paths with spaces."""
from pathlib import Path
import json
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class HiddenReplayTests(unittest.TestCase):
    def test_recorded_command_replays_same_hidden_ids_and_digest(self):
        with tempfile.TemporaryDirectory(prefix='comac hidden replay ') as temp:
            root = Path(temp)
            tasks = root/'tasks'/'awcom.compliance'
            tasks.mkdir(parents=True)
            (root/'data').symlink_to(ROOT/'data', target_is_directory=True)
            src = ROOT/'tasks'/'awcom.compliance'
            for p in src.iterdir():
                if p.suffix in ('.yaml', '.md'):
                    shutil.copy2(p, tasks/p.name)
            out = root/'hidden results'
            r = subprocess.run([sys.executable, '-m', 'runners.qa_grounded',
                '--tasks', str(tasks), '--out', str(out), '--provider', 'oracle',
                '--hidden', '8', '--seed', '7'], cwd=ROOT, capture_output=True, text=True, timeout=30)
            self.assertEqual(r.returncode, 0, r.stderr)
            manifest = json.loads((out/'run_manifest.json').read_text())
            self.assertEqual(manifest['n_tasks'], 8)
            self.assertEqual(manifest['extra']['hidden_n'], 8)
            command = shlex.split(manifest['rerun_command'])
            self.assertEqual(command[:3], ['cd', str(ROOT), '&&'])
            self.assertEqual(command[3], sys.executable)
            self.assertEqual(command[command.index('--hidden')+1], '8')
            self.assertEqual(command[command.index('--seed')+1], '7')
            rows = {p.name:p.read_bytes() for p in out.glob('result_*.json')}
            self.assertEqual(len(rows), 8)
            for raw in rows.values():
                artifacts = json.loads(raw)['artifacts']
                self.assertFalse({'answer','raw','code','prompt'} & artifacts.keys())
            # Recorded safe replay keeps every completed result byte-for-byte.
            replay = subprocess.run(command[3:], cwd=command[1], capture_output=True, text=True, timeout=30)
            self.assertEqual(replay.returncode, 0, replay.stderr)
            self.assertEqual({p.name:p.read_bytes() for p in out.glob('result_*.json')}, rows)
            # Fresh output repeats the selected IDs and identity, without reusing cache.
            command[command.index('--out')+1] = str(root/'fresh output')
            replay = subprocess.run(command[3:], cwd=command[1], capture_output=True, text=True, timeout=30)
            self.assertEqual(replay.returncode, 0, replay.stderr)
            fresh = json.loads((root/'fresh output/run_manifest.json').read_text())
            self.assertEqual(fresh['extra']['selected_task_ids'], manifest['extra']['selected_task_ids'])
            self.assertEqual(fresh['extra']['resume_identity'], manifest['extra']['resume_identity'])
            self.assertEqual(fresh['extra']['resumed_tasks'], 0)

if __name__ == '__main__':
    unittest.main()
