"""Real HTTP evidence, with full public responses and no hidden answer persistence."""
import hashlib
import io
import json
import time
import urllib.request
from runners.common import write_json_atomic


class EvidenceStop(BaseException):
    pass


class Ledger:
    def __init__(self,path,config,protocol_sha256):
        self.path,self.config=path,config
        self.transport=urllib.request.urlopen
        self.phase,self.group,self.task_id='live',None,None
        if path.exists():
            self.state=json.loads(path.read_text())
            if self.state['config']!=config or self.state['protocol_sha256']!=protocol_sha256:
                raise EvidenceStop('ledger identity changed')
            if any(r['status']!='received' for r in self.state['requests']):
                raise EvidenceStop('unresolved transport uncertainty; preserve and use a recovery directory')
        else:
            self.state={'config':config,'protocol_sha256':protocol_sha256,'requests':[]}
            self.save()

    def save(self):
        write_json_atomic(self.path,self.state)

    def urlopen(self,request,*args,**kwargs):
        if self.phase!='live':
            raise EvidenceStop('HTTP forbidden during verification')
        if request.full_url!=self.config['endpoint'] or request.get_method()!='POST':
            raise EvidenceStop('unexpected endpoint or method')
        body=request.data or b''
        data=json.loads(body)
        if data.get('model')!=self.config['model'] or data.get('stream') or not self.task_id:
            raise EvidenceStop('unexpected model, stream or missing task context')
        row={'sequence':len(self.state['requests'])+1,'task_id':self.task_id,'group':self.group,
             'hidden':self.group=='hidden','started_at_epoch':time.time(),'status':'in_flight',
             'request_model':data['model'],'request_sha256':hashlib.sha256(body).hexdigest(),
             'request_bytes':len(body),'temperature':data.get('temperature'),
             'max_tokens':data.get('max_tokens'),'thinking':data.get('thinking')}
        self.state['requests'].append(row);self.save()
        print(f'[live] {row["sequence"]}: {self.task_id}',flush=True)
        try:
            kwargs['timeout']=self.config['transport_timeout_s']
            with self.transport(request,*args,**kwargs) as response:
                raw=response.read()
            result=json.loads(raw)
            row.update(response_id=result.get('id'),response_model=result.get('model'),
                usage=result.get('usage'),response_sha256=hashlib.sha256(raw).hexdigest(),
                finish_reasons=[c.get('finish_reason') for c in result.get('choices',[])])
            if str(result.get('model')).lower()!=self.config['model'].lower() or not result.get('id'):
                raise ValueError('response identity mismatch')
            if not row['hidden']:
                path=self.path.parent/'responses'/f'{row["sequence"]:03d}.json'
                path.parent.mkdir(exist_ok=True)
                path.write_bytes(raw)
                row['public_response_file']=str(path.relative_to(self.path.parent))
            row['status']='received'
            print(f'[received] {self.task_id}: {row["usage"]}',flush=True)
            return io.BytesIO(raw)
        except Exception as error:
            row.update(status='uncertain',error_type=type(error).__name__)
            if hasattr(error,'code'):
                row['http_status']=error.code
            raise EvidenceStop(f'transport/identity uncertainty: {type(error).__name__}') from None
        finally:
            row['elapsed_s']=round(time.time()-row['started_at_epoch'],3)
            self.save()
