"""No-network checks for the experiment's evidence recorder."""
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import urllib.request

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]))
sys.path.insert(0,str(HERE))
from response_ledger import ResponseLedger, EvidenceStop


class ResponseLedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/'requests.json'
        self.config = {'model':'glm-5.3-flash','endpoint':'https://example.invalid/chat/completions'}
        self.guard = ResponseLedger(self.path,self.config,'frozen-protocol')
        self.body = json.dumps({'model':'glm-5.3-flash','max_tokens':32768,
            'messages':[{'role':'user','content':'private test prompt'}]}).encode()
        self.request = urllib.request.Request(self.config['endpoint'],data=self.body,
            headers={'Authorization':'Bearer private-test-key'})

    def test_request_and_response_pass_through_without_persisting_private_content(self):
        response = json.dumps({'model':'glm-5.3-flash','id':'fixture-response',
            'choices':[{'message':{'content':'private test answer'},'finish_reason':'stop'}],
            'usage':{'completion_tokens':12}}).encode()
        seen = []
        def transport(request, **kwargs):
            seen.append(request)
            return io.BytesIO(response)
        self.guard.transport = transport
        self.assertEqual(self.guard.urlopen(self.request).read(),response)
        self.assertIs(seen[0],self.request)
        self.assertEqual(seen[0].data,self.body)
        self.assertEqual(self.guard.state['requests'][0]['usage']['completion_tokens'],12)
        self.assertNotIn('private',self.path.read_text())

    def test_cache_verification_rejects_before_transport_or_ledger_mutation(self):
        self.guard.phase = 'verify'
        before = self.path.read_bytes()
        self.guard.transport = lambda *a,**kw: self.fail('transport must not run')
        with self.assertRaises(EvidenceStop):
            self.guard.urlopen(self.request)
        self.assertEqual(self.path.read_bytes(),before)

    def test_wrong_response_model_is_recorded_and_cannot_be_silently_resumed(self):
        self.guard.transport = lambda *a,**kw: io.BytesIO(json.dumps({
            'id':'fixture','model':'different-model','choices':[{}]}).encode())
        with self.assertRaises(EvidenceStop):
            self.guard.urlopen(self.request)
        self.assertEqual(self.guard.state['requests'][0]['status'],'uncertain')
        with self.assertRaises(EvidenceStop):
            ResponseLedger(self.path,self.config,'frozen-protocol')


if __name__ == '__main__':
    unittest.main()
