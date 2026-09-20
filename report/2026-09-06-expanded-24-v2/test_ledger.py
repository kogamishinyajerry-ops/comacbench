import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import urllib.request
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]));sys.path.insert(0,str(HERE))
from ledger import Ledger,EvidenceStop


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'requests.json'
        self.config={'endpoint':'https://example.invalid/chat/completions','model':'glm-5.3-flash','transport_timeout_s':1800}
        self.guard=Ledger(self.path,self.config,'test-protocol')
        self.guard.task_id='fixture';self.guard.group='extract'
        self.req=urllib.request.Request(self.config['endpoint'],data=json.dumps({
            'model':'glm-5.3-flash','messages':[{'role':'user','content':'private fixture prompt'}]}).encode(),
            headers={'Authorization':'Bearer fixture-secret-key'})
        self.raw=json.dumps({'id':'response-fixture','model':'glm-5.3-flash',
            'choices':[{'message':{'content':'fixture answer'},'finish_reason':'stop'}],
            'usage':{'completion_tokens':5}}).encode()

    def test_wrong_request_model_is_rejected_before_transport(self):
        self.req.data=b'{"model":"wrong-model"}'
        self.guard.transport=lambda *a,**k:self.fail('transport invoked')
        with self.assertRaises(EvidenceStop):self.guard.urlopen(self.req)
        self.assertFalse(self.guard.state['requests'])

    def test_cache_phase_rejects_without_writing_or_calling_transport(self):
        self.guard.phase='verify';before=self.path.read_bytes()
        self.guard.transport=lambda *a,**k:self.fail('transport invoked')
        with self.assertRaises(EvidenceStop):self.guard.urlopen(self.req)
        self.assertEqual(before,self.path.read_bytes())

    def test_public_response_and_request_pass_through_unchanged(self):
        seen=[]
        def transport(req,**kwargs):
            seen.append((req,kwargs));return io.BytesIO(self.raw)
        self.guard.transport=transport
        self.assertEqual(self.guard.urlopen(self.req,timeout=600).read(),self.raw)
        self.assertIs(seen[0][0],self.req);self.assertEqual(seen[0][1]['timeout'],1800)
        row=self.guard.state['requests'][0]
        self.assertEqual((self.path.parent/row['public_response_file']).read_bytes(),self.raw)
        self.assertNotIn('fixture-secret-key',self.path.read_text())
        self.assertNotIn('private fixture prompt',self.path.read_text())

    def test_hidden_answer_is_not_persisted(self):
        self.guard.group='hidden'
        self.guard.transport=lambda *a,**k:io.BytesIO(self.raw)
        self.assertEqual(self.guard.urlopen(self.req).read(),self.raw)
        self.assertNotIn('public_response_file',self.guard.state['requests'][0])
        self.assertFalse((self.path.parent/'responses').exists())
        self.assertNotIn('fixture answer',self.path.read_text())


if __name__=='__main__':unittest.main()
