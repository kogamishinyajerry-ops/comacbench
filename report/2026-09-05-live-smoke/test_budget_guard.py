"""Budget transport must stop before contacting an endpoint past its allowance."""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import json
import tempfile
import threading
import unittest
import urllib.request

from budget_guard import BudgetGuard, BudgetStop


class BudgetGuardTests(unittest.TestCase):
    def test_request_limit_and_restart_refuse_without_a_second_http_call(self):
        calls = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_POST(self):
                body = self.rfile.read(int(self.headers['Content-Length']))
                calls.append(body)
                response = json.dumps({'id':'fixture-response','model':'fixture',
                    'choices':[{'message':{'content':'1'},'finish_reason':'stop'}],
                    'usage':{'prompt_tokens':10,'completion_tokens':2,'total_tokens':12}}).encode()
                self.send_response(200)
                self.send_header('Content-Length',str(len(response)))
                self.end_headers()
                self.wfile.write(response)
        server = HTTPServer(('127.0.0.1',0),Handler)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        with tempfile.TemporaryDirectory() as temp:
            url=f'http://127.0.0.1:{server.server_port}/chat/completions'
            config={'endpoint':url,'model':'fixture','max_requests':1,
                    'max_completion_tokens':10,'max_request_bytes':1000,'max_seconds':120}
            path=Path(temp)/'ledger.json'
            request=urllib.request.Request(url,data=json.dumps({'model':'fixture','max_tokens':5}).encode())
            guard=BudgetGuard(path,config,'fixture-hash')
            with guard.urlopen(request) as response:
                self.assertEqual(json.load(response)['choices'][0]['message']['content'],'1')
            restarted=BudgetGuard(path,config,'fixture-hash')
            with self.assertRaises(BudgetStop):
                restarted.urlopen(request)
            self.assertEqual(len(calls),1)
            self.assertEqual(json.loads(path.read_text())['requests'][0]['usage']['completion_tokens'],2)

    def test_reservation_blocks_before_network_and_unknown_usage_stays_reserved(self):
        with tempfile.TemporaryDirectory() as temp:
            config={'endpoint':'http://127.0.0.1:1/chat/completions','model':'fixture',
                    'max_requests':12,'max_completion_tokens':4,'max_request_bytes':1000,'max_seconds':120}
            request=urllib.request.Request(config['endpoint'],data=b'{"model":"fixture","max_tokens":5}')
            guard=BudgetGuard(Path(temp)/'ledger.json',config,'fixture-hash')
            with self.assertRaises(BudgetStop):
                guard.urlopen(request)
            self.assertEqual(guard.state['requests'],[])
            config['max_completion_tokens']=10
            guard=BudgetGuard(Path(temp)/'other.json',config,'another-hash')
            with self.assertRaises(BudgetStop):
                guard.urlopen(request)
            self.assertEqual(guard.state['requests'][0]['reserved_completion_tokens'],5)
            self.assertEqual(guard.used_completion_tokens(),5)


if __name__ == '__main__':
    unittest.main()
