"""A local fake provider exercises a real interruption and exclusive output lock."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]

class InterruptedResumeTests(unittest.TestCase):
    def test_process_death_keeps_completed_work_and_releases_writer_lock(self):
        waiting = threading.Event()
        release = threading.Event()
        requests = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_POST(self):
                requests.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
                if len(requests) == 2:
                    waiting.set()
                    release.wait(15)
                body = json.dumps({'choices':[{'message':{'content':'1'}}]}).encode()
                try:
                    self.send_response(200)
                    self.send_header('Content-Length', str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError):
                    pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        self.addCleanup(release.set)
        with tempfile.TemporaryDirectory(prefix='comac-interrupted-') as temp:
            root = Path(temp)
            tasks = root/'tasks'/'fixture'
            tasks.mkdir(parents=True)
            for i in (1,2):
                tid = 'fixture_'+str(i)
                prompt = tasks/(tid+'.md')
                prompt.write_text('1. correct 2. incorrect')
                spec = {'id':tid, 'registry_id':'fixture.qa', 'domain':'knowledge',
                    'task_type':'qa_grounded', 'model_profile':'plain_llm',
                    'assets_revision':'v1', 'allowed_tools':[], 'hidden':False,
                    'input':{'prompt_file':str(prompt), 'assets':[]},
                    'output_contract':['answer'], 'reference':{'correct_option_index':1},
                    'grader':{'answer_format':'mcq', 'validity_gate':True},
                    'scoring':{'weights':{'requirements':1,'physics':0,'objective':0,'robustness':0}},
                    'limits':{'attempts':1,'wall_clock_s':10},
                    'license_provenance':{'license':'self-built','mirror_allowed':True}}
                (tasks/(tid+'.yaml')).write_text(yaml.safe_dump(spec))
            out = root/'out'
            command = [sys.executable,'-m','runners.qa_grounded','--tasks',str(tasks),
                '--out',str(out),'--provider','openai_compat','--resume']
            env = {**os.environ,'BM_API_BASE':f'http://127.0.0.1:{server.server_port}/v1',
                   'BM_API_KEY':'local-test-only','BM_MODEL':'fixture-model'}
            proc = subprocess.Popen(command,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            try:
                self.assertTrue(waiting.wait(10), 'second request never arrived')
                first = out/'result_fixture_1.json'
                before = first.read_bytes()
                manifest = json.loads((out/'run_manifest.json').read_text())
                self.assertEqual(manifest['n_tasks'], 2)
                self.assertEqual(manifest['extra']['model'], 'fixture-model')
                other = subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,timeout=10)
                self.assertNotEqual(other.returncode, 0)
                self.assertIn('another writer', other.stderr)
                self.assertEqual(len(requests), 2)
                proc.kill()
                proc.communicate(timeout=5)
                release.set()
                resumed = subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,timeout=15)
                self.assertEqual(resumed.returncode, 0, resumed.stderr)
                self.assertEqual(first.read_bytes(), before)
                self.assertTrue((out/'result_fixture_2.json').exists())
                self.assertEqual(len(requests), 3, 'completed task was sent to provider again')
                self.assertEqual(json.loads((out/'run_manifest.json').read_text())['extra']['resumed_tasks'], 1)
            finally:
                if proc.poll() is None:
                    proc.kill()
                    proc.communicate(timeout=5)
                release.set()

if __name__ == '__main__':
    unittest.main()
