"""Pass-through live API evidence; no cost, request-count, or token budget cap."""
import hashlib
import io
import json
import time
import urllib.request
from runners.common import write_json_atomic


class EvidenceStop(BaseException):
    """Stop on evidence/transport uncertainty without hidden provider retries."""


class ResponseLedger:
    def __init__(self, path, config, protocol_hash):
        self.path, self.config = path, config
        self.transport = urllib.request.urlopen
        self.phase, self.group = 'live', None
        if path.exists():
            self.state = json.loads(path.read_text())
            if self.state['protocol_sha256'] != protocol_hash or self.state['config'] != config:
                raise EvidenceStop('ledger identity mismatch')
            if any(r['status'] != 'received' for r in self.state['requests']):
                raise EvidenceStop('previous transport uncertainty requires a new experiment')
        else:
            self.state = {'protocol_sha256':protocol_hash, 'config':config, 'requests':[]}
            self.save()

    def save(self):
        write_json_atomic(self.path, self.state)

    def urlopen(self, request, *args, **kwargs):
        if self.phase != 'live':
            raise EvidenceStop('HTTP forbidden during cache-only verification')
        if request.full_url != self.config['endpoint'] or request.get_method() != 'POST':
            raise EvidenceStop('unexpected endpoint or HTTP method')
        body = request.data or b''
        data = json.loads(body)
        if data.get('model') != self.config['model'] or data.get('stream'):
            raise EvidenceStop('unexpected model or streaming request')
        row = {'sequence':len(self.state['requests'])+1, 'group':self.group,
               'started_at_epoch':time.time(), 'request_model':data['model'],
               'request_sha256':hashlib.sha256(body).hexdigest(), 'request_bytes':len(body),
               'max_tokens':data.get('max_tokens'), 'temperature':data.get('temperature'),
               'thinking':data.get('thinking'), 'status':'in_flight'}
        self.state['requests'].append(row)
        self.save()
        print(f'[live] request {row["sequence"]}, group={self.group}, model={data["model"]}',flush=True)
        try:
            with self.transport(request,*args,**kwargs) as response:
                raw = response.read()
            received = json.loads(raw)
            row.update(response_id=received.get('id'),response_model=received.get('model'),
                       usage=received.get('usage'),response_sha256=hashlib.sha256(raw).hexdigest(),
                       finish_reasons=[c.get('finish_reason') for c in received.get('choices',[])])
            if str(received.get('model')).lower() != data['model'].lower():
                raise ValueError('response model identity does not match requested model')
            if not received.get('id') or not received.get('choices'):
                raise ValueError('missing response ID or choices')
            row['status'] = 'received'
            print(f'[live] received {row["sequence"]}, usage={row["usage"]}',flush=True)
            return io.BytesIO(raw)
        except Exception as error:
            row.update(status='uncertain',error_type=type(error).__name__)
            if hasattr(error,'code'):
                row['http_status'] = error.code
            raise EvidenceStop(f'API/evidence uncertainty: {type(error).__name__}') from None
        finally:
            row['elapsed_s'] = round(time.time()-row['started_at_epoch'],3)
            self.save()
