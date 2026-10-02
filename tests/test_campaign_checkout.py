"""Exercise the exact workflow export script with a local Git-object fixture.

No network, credentials, models or solver data. The fixture contains a colon-
bearing research path in Git objects without ever creating it on disk.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest


class SourceExportTests(unittest.TestCase):
    def setUp(self):
        if not shutil.which('git'):
            self.skipTest('git is not installed')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root/'origin.git'
        subprocess.run(['git', 'init', '--bare', str(self.source)], check=True, capture_output=True)
        self.git('config', 'uploadpack.allowFilter', 'true')
        workflow = Path(__file__).resolve().parents[1]/'.github/workflows/campaign-audit.yml'
        text = workflow.read_text(encoding='utf-8')
        self.script = textwrap.dedent(text.split('# BEGIN_SOURCE_EXPORT\n', 1)[1].split('# END_SOURCE_EXPORT', 1)[0])
        self.workflow_text = text
        self.workspace = self.root/'workspace'

    def git(self, *args, content=None):
        env = dict(os.environ, GIT_AUTHOR_NAME='Fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
                   GIT_COMMITTER_NAME='Fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid')
        return subprocess.check_output(['git', '-C', str(self.source), *args],
                                        input=content, env=env, stderr=subprocess.PIPE).decode().strip()

    def blob(self, text):
        return self.git('hash-object', '-w', '--stdin', content=text.encode())

    def tree(self, entries):
        # Build raw tree bytes, so Windows never tries to materialize the bad path.
        payload = b''.join(mode.encode()+b' '+name.encode()+b'\0'+bytes.fromhex(sha)
                           for name, mode, sha in sorted(entries, key=lambda e: e[0]+('/' if e[1]=='40000' else '')))
        return self.git('hash-object', '-t', 'tree', '-w', '--stdin', content=payload)

    def commit(self, *, link=False):
        content = self.blob('# synthetic source fixture\n')
        files = [('campaign.py', '100644', content)]
        if link:
            files.append(('link.py', '120000', self.blob('../../outside')))
        tree = self.tree([
            ('comacbench', '40000', self.tree(files)),
            ('tests', '40000', self.tree([('test_campaign.py', '100644', content)])),
            ('data', '40000', self.tree([('strainRateViscosityModel:nu', '100644', content)])),
            ('.github', '40000', self.tree([('workflows', '40000', self.tree([
                ('campaign-audit.yml', '100644', self.blob(self.workflow_text))]))]))])
        sha = self.git('commit-tree', tree, '-m', 'synthetic export test')
        self.git('update-ref', 'refs/heads/main', sha)
        return sha

    def run_export(self, sha):
        env = dict(os.environ, SOURCE_SHA=sha, SOURCE_URL=self.source.as_uri(),
                   GITHUB_WORKSPACE=str(self.workspace), RUNNER_TEMP=str(self.root), GIT_TERMINAL_PROMPT='0')
        return subprocess.run([sys.executable, '-c', self.script], env=env,
                              capture_output=True, text=True, timeout=60)

    def test_exact_commit_exports_only_selected_sources(self):
        sha = self.commit()
        proc = self.run_export(sha)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(sha, proc.stdout)
        self.assertTrue((self.workspace/'comacbench/campaign.py').is_file())
        self.assertTrue((self.workspace/'tests/test_campaign.py').is_file())
        self.assertTrue((self.workspace/'.github/workflows/campaign-audit.yml').is_file())
        self.assertFalse((self.workspace/'data').exists())
        self.assertFalse((self.workspace/'.git').exists())

    def test_selected_symlink_is_rejected_before_extraction(self):
        proc = self.run_export(self.commit(link=True))
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('unsafe source member', proc.stderr)
        self.assertFalse((self.workspace/'comacbench').exists())

    def test_unknown_commit_does_not_fall_back_to_main(self):
        self.commit()
        proc = self.run_export('b'*40)
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse((self.workspace/'comacbench').exists())

    def test_non_sha_ref_is_rejected(self):
        proc = self.run_export('refs/heads/main')
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('expected exact source commit', proc.stderr)


if __name__ == '__main__':
    unittest.main()
