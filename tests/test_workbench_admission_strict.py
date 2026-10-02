"""Audit failures and legitimate error paths. All solver processes are test doubles."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest import mock
import test_workbench_public as fixtures
from comacbench import workbench as wb
from comacbench.workbench_public import dispatch
from comacbench.workbench_admission import audit_trial, _digest, MAX_RECORD


class StrictAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.PublicBoundaryTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.data, self.audit = self.fixture.audit_fixture()
        self.rows = self.read('boundary.jsonl')
        self.stream = self.read('dsh-events.jsonl')

    def read(self, name):
        return [json.loads(x) for x in (self.audit/name).read_text().splitlines()]

    def save(self):
        for name,rows in [('boundary.jsonl',self.rows),('dsh-events.jsonl',self.stream)]:
            (self.audit/name).write_text(''.join(json.dumps({**r,**({'seq':i+1} if name=='boundary.jsonl' else {})})+'\n' for i,r in enumerate(rows)))

    def result(self, expected=False):
        self.save(); result=audit_trial(self.data,self.audit,session=self.fixture.session)
        self.assertEqual(result['score_admissible'],expected,result)
        return result

    def append(self, request, value=None, **broker_fields):
        if value is None: value=dispatch(self.fixture.session,request)
        output=json.dumps(value); key='call-'+str(len([r for r in self.stream if r['type']=='tool_call'])+1)
        self.rows += [{'type':'broker','call_id':key,'request':request,'exit_code':0,'stdout':output,**broker_fields},
                      {'type':'tool_result','call_id':key,'name':'workbench','arguments':{'request':request},'is_error':False,'content':[{'type':'text','text':output}]}]
        self.stream[-2:-2]=[{'type':'tool_call','callId':key,'tool':'workbench','input':{'request':request}},
                            {'type':'tool_result','callId':key,'result':output}]
        self.data=wb.snapshot(self.fixture.session)

    def test_each_duplicate_and_extra_id_is_rejected(self):
        for source,typ,key in [('rows','broker','call_id'),('rows','tool_result','call_id'),('stream','tool_call','callId'),('stream','tool_result','callId')]:
            for replacement in (None,'extra'):
                with self.subTest(source=source,typ=typ,replacement=replacement):
                    target=getattr(self,source); item=deepcopy(next(r for r in target if r['type']==typ))
                    if replacement: item[key]=replacement
                    target.append(item);self.result();target.pop()

    def test_wrong_association_and_result_order(self):
        self.stream[1],self.stream[2]=self.stream[2],self.stream[1]
        self.result()
        self.stream[1],self.stream[2]=self.stream[2],self.stream[1]
        next(r for r in self.rows if r['type']=='broker')['request']={'op':'advance'}
        self.result()

    def test_strict_json_records(self):
        self.save()
        p=self.audit/'execution.json'; original=p.read_text()
        for raw in ('{"exit_code":1,"exit_code":0}', '{"value":NaN}', '{"value":Infinity}', '{"value":1e999}', '[]', '{', '{"x":"'+'x'*(MAX_RECORD+1)+'"}'):
            with self.subTest(prefix=raw[:60]):
                p.write_text(raw); result=audit_trial(self.data,self.audit,session=self.fixture.session)
                self.assertFalse(result['score_admissible']);self.assertTrue(result['deviation_reasons'])
        p.write_text(original)
        p=self.audit/'boundary.jsonl'; original=p.read_text()
        for raw in ('{"type":"assembly","type":"ready"}\n','[]\n',original.rstrip('\n')):
            p.write_text(raw);self.assertFalse(audit_trial(self.data,self.audit)['score_admissible'])

    def test_each_actual_response_rejects_private_fields(self):
        for mutation in ('root','observation','result','contract','source'):
            with self.subTest(mutation=mutation):
                original=deepcopy((self.rows,self.stream)); b=next(r for r in self.rows if r['type']=='broker');v=json.loads(b['stdout'])
                target={'root':v,'observation':v['observation'],'result':v['result'],'contract':v['observation']['contract'],'source':v['observation']['sources']['model']}[mutation]
                target['manifest']={'future':'private'};b['stdout']=json.dumps(v)
                next(r for r in self.rows if r['type']=='tool_result')['content'][0]['text']=b['stdout']
                next(r for r in self.stream if r['type']=='tool_result')['result']=b['stdout']
                self.result();self.rows,self.stream=original

    def test_legal_task_rejection_stays_task_rejection(self):
        self.append({'op':'check','target':'review'})
        result=self.result(True)
        self.assertEqual(result['call_paths'][-1]['path'],'task_action_rejected')
        self.assertEqual(self.data['observation']['actions_used'],1)

    def test_native_raw_text_is_accepted_and_bound_to_archive(self):
        self.append({'op':'solve','target':'solution_limit'})
        self.append({'op':'read_native','target':'solution_limit','name':'model.dat'})
        self.result(True)
        b=self.rows[-2];v=json.loads(b['stdout']);v['result']['text']+='private extra'
        b['stdout']=json.dumps(v);self.rows[-1]['content'][0]['text']=b['stdout'];self.stream[-3]['result']=b['stdout']
        self.result()

    def test_gateway_denial_does_not_consume_action(self):
        self.append({'op':'observe','target':'review'})
        self.result(True);self.assertEqual(self.data['events'],[])

    def test_broker_failure_with_real_receipt_is_classified(self):
        for code,error in ((1,None),(None,'ENOENT')):
            self.append({'op':'observe'},{'result':{'ok':False,'code':'broker_process_failed'}},exit_code=code,process_error=error,stdout='')
        result=self.result(True)
        self.assertEqual([p['path'] for p in result['call_paths'][1:]],['broker_failure','broker_failure'])

    def test_invalid_broker_output_is_not_success(self):
        self.append({'op':'observe'},{'result':{'ok':False,'code':'broker_invalid_json'}},stdout='{')
        r=self.result()
        self.assertEqual(r['call_paths'][-1]['path'],'broker_failure')
        self.assertFalse(r['audit_checks']['broker_payload_parseable'])

    def test_pre_gateway_validation_does_not_require_fake_receipt(self):
        self.rows=[r for r in self.rows if r['type']!='broker']
        h=next(r for r in self.rows if r['type']=='tool_result');msg='invalid arguments: "request" must be an object'
        h.update(arguments={'request':'bad'},is_error=True,error={'message':msg,'info':{'name':'ToolArgsError','code':'INVALID_ARGS'}},content=[{'type':'text','text':'Error: '+msg}])
        next(r for r in self.stream if r['type']=='tool_call')['input']=h['arguments']
        next(r for r in self.stream if r['type']=='tool_result')['result']='Error: '+msg
        result=self.result(True);self.assertEqual(result['call_paths'][0]['path'],'pre_gateway_denial')

    def test_actual_prompt_body_not_operator_digest_is_authority(self):
        a=next(r for r in self.rows if r['type']=='assembly');a['sections'][0]['text']='private'
        a['public_system_sha256']=__import__('hashlib').sha256(b'private').hexdigest()
        a['input_sha256']=_digest({k:a[k] for k in ('sections','contexts','tools')})
        c=json.loads((self.audit/'control.json').read_text());c['complete_public_system']='private';(self.audit/'control.json').write_text(json.dumps(c))
        self.result()

    def test_final_model_request_mutations_are_rejected(self):
        for field in ('system','user','tools','extra'):
            original=deepcopy(self.rows)
            r=next(r for r in self.rows if r['type']=='model_input')
            if field in ('system','user'):r['messages'][0 if field=='system' else 1]['content'][0]['text']='private'
            elif field=='tools':r['tools'][0]['description']='private'
            else:r['messages'].append({'role':'developer','content':[{'type':'text','text':'private'}]})
            r['input_sha256']=_digest({k:r[k] for k in ('messages','tools')})
            self.result();self.rows=original

    def test_old_contract_remains_unknown(self):
        c=json.loads((self.audit/'control.json').read_text());c['protocol']='comacbench.public-boundary.v1';(self.audit/'control.json').write_text(json.dumps(c))
        r=self.result();self.assertEqual(r['protocol_conformance'],'unknown');self.assertEqual(r['reference_exposure'],'unknown')

    def test_audit_never_executes_solver(self):
        with mock.patch('subprocess.run',side_effect=AssertionError('no process in audit')):
            self.result(True)

    def test_report_does_not_turn_unknown_or_conflict_into_pass(self):
        from comacbench.workbench_report import render
        for conformance,exposure in [('unknown','unknown'),('conformant','unknown')]:
            data=deepcopy(self.data)
            data.update(protocol_conformance=conformance,reference_exposure=exposure,score_admissible=True,deviation_reasons=[])
            html=render(data)
            self.assertIn('score_admissible: <strong>false</strong>',html)
            self.assertNotIn('主机控制与工具记录核对通过',html)

    def test_contract_transport_crlf_and_mutation(self):
        from comacbench.workbench_admission import _contract_sha, CONTRACT_SHA256
        raw=(Path(__file__).resolve().parents[1]/'comacbench/public_input_v2.json').read_bytes().replace(b'\r\n',b'\n')
        p=self.fixture.root/'contract.json';p.write_bytes(raw.replace(b'\n',b'\r\n'))
        self.assertEqual(_contract_sha(p),CONTRACT_SHA256)
        p.write_bytes(raw.replace(b'workbench',b'changed-tool',1))
        self.assertNotEqual(_contract_sha(p),CONTRACT_SHA256)

    def test_native_text_uses_gateway_decoding_with_original_byte_identity(self):
        from comacbench.workbench_admission import ResponseAudit
        import hashlib
        p=self.fixture.session/'native/000001';p.mkdir()
        raw=b'raw output\r\nnon-UTF8: \xff\r\n';(p/'model.solver.log').write_bytes(raw)
        self.data['native_receipts']={'000001':{'files':{'model.solver.log':hashlib.sha256(raw).hexdigest()}}}
        a=ResponseAudit(self.data,self.fixture.session)
        a.state['artifacts']['solution_limit']={'payload':{'job_id':'000001'}}
        request={'op':'read_native','target':'solution_limit','name':'model.solver.log'}
        value={'result':{'ok':True,'code':'native_text','target':'solution_limit','name':'model.solver.log','text':(p/'model.solver.log').read_text(encoding='utf-8',errors='replace')}}
        a.check(request,value)
        value['result']['text']+='extra'
        with self.assertRaisesRegex(ValueError,'archive mismatch'):a.check(request,value)

    def test_schema_denial_cannot_be_misreported_as_broker_entry(self):
        self.append('not-an-object',{'result':{'ok':False,'code':'public_request_denied'}})
        r=self.result()
        self.assertIn('schema-rejected arguments',' '.join(r['deviation_reasons']))
