import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml
from comacbench.agent import identity, invoke, PROTOCOL
from runners.common import TaskSpec
from runners.providers import ProviderError

ROOT=Path(__file__).resolve().parents[1]


class ExternalAgentTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.wrapper=self.root/'agent.py'
        self.config=self.root/'agent.json'
        self.config.write_text(json.dumps({'protocol':PROTOCOL,'name':'test-agent','revision':'r1',
            'command':['{python}','./agent.py'],'revision_files':['agent.py'],'timeout_s':2,'env':[]}))
        pack=ROOT/'packs/aviation-core-v1'
        p=pack/'tasks/enterprise.data/data_units_01.yaml'
        self.task=TaskSpec(yaml.safe_load(p.read_text()),p)
        self.env=patch.dict(os.environ,{'COMAC_AGENT_CONFIG':str(self.config),
            'COMAC_AGENT_PACK_ROOT':str(pack),'COMAC_AGENT_AUDIT':str(self.root/'audit')})
        self.env.start();self.addCleanup(self.env.stop)

    def call(self):
        return invoke(self.task,'public prompt',seed=7,expect='code')

    def script(self,reply):
        self.wrapper.write_text('import json,sys\nr=json.load(sys.stdin)\n'+reply+'\n')

    def test_wrong_task_rejected_and_evidence_retained(self):
        self.script("print(json.dumps({'protocol':r['protocol'],'task_id':'wrong','answer':'pass'}))")
        with self.assertRaisesRegex(ProviderError,'identity_mismatch'): self.call()
        self.assertEqual(len(list((self.root/'audit').glob('*/request.json'))),1)

    def test_invalid_json_does_not_retry(self):
        self.script("print('not json')")
        with self.assertRaises(ProviderError): self.call()
        self.assertEqual(len(list((self.root/'audit').glob('*/status.json'))),1)

    def test_timeout_retained(self):
        self.script('import time\ntime.sleep(10)')
        cfg=json.loads(self.config.read_text());cfg['timeout_s']=.05
        self.config.write_text(json.dumps(cfg))
        with self.assertRaisesRegex(ProviderError,'agent_timeout'): self.call()
        status=json.loads(next((self.root/'audit').glob('*/status.json')).read_text())
        self.assertTrue(status['timeout'])

    def test_only_public_request_and_filtered_environment(self):
        self.script("import os\nassert 'reference' not in r and 'grader' not in r\nassert 'SHOULD_NOT_LEAK' not in os.environ\nassert r['seed']==7\nprint(json.dumps({'protocol':r['protocol'],'task_id':r['task_id'],'answer':'pass'}))")
        with patch.dict(os.environ,{'SHOULD_NOT_LEAK':'secret'}): result=self.call()
        self.assertEqual(result['answer'].strip(),'pass')
        request=json.loads(next((self.root/'audit').glob('*/request.json')).read_text())
        self.assertNotIn('oracle_source',json.dumps(request))

    def test_source_change_changes_identity(self):
        self.script("print('a')")
        a=identity()
        self.script("print('b')")
        self.assertNotEqual(a,identity())

    def test_negative_timeout_rejected_before_launch(self):
        self.script("print('not reached')")
        cfg=json.loads(self.config.read_text());cfg['timeout_s']=-1
        self.config.write_text(json.dumps(cfg))
        with self.assertRaises(ValueError):identity()
        self.assertFalse((self.root/'audit').exists())


if __name__=='__main__':unittest.main()
