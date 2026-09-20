"""Experiment-only HTTP budget guard. Requests and responses pass through unchanged."""
import hashlib
import io
import json
import time
import urllib.request

from runners.common import write_json_atomic


class BudgetStop(BaseException):
    """Bypass the provider's retry loop when spending must stop."""


class BudgetGuard:
    def __init__(self, path, config, protocol_hash):
        self.path, self.config = path, config
        self.transport = urllib.request.urlopen
        self.phase = 'live'
        if path.exists():
            self.state = json.loads(path.read_text())
            if self.state['config'] != config or self.state['protocol_sha256'] != protocol_hash:
                raise BudgetStop('budget ledger identity mismatch')
        else:
            self.state = {'protocol_sha256':protocol_hash,'config':config,
                          'created_at_epoch':time.time(),'requests':[]}
            self.save()

    def save(self):
        write_json_atomic(self.path,self.state)

    def used_completion_tokens(self):
        return sum(row.get('usage',{}).get('completion_tokens',row['reserved_completion_tokens'])
                   for row in self.state['requests'])

    def urlopen(self, request, *args, **kwargs):
        if self.phase != 'live':
            raise BudgetStop('HTTP forbidden during cache-only verification')
        cfg = self.config
        body = request.data or b''
        if request.full_url != cfg['endpoint'] or request.get_method() != 'POST':
            raise BudgetStop('unexpected endpoint or method')
        data = json.loads(body)
        maximum = data.get('max_tokens')
        if data.get('model') != cfg['model'] or type(maximum) is not int or maximum <= 0:
            raise BudgetStop('unexpected model or output limit')
        if data.get('stream') or len(body) > cfg['max_request_bytes']:
            raise BudgetStop('streaming or oversized payload is outside this experiment')
        remaining_s = cfg['max_seconds'] - (time.time()-self.state['created_at_epoch'])
        if remaining_s <= 0 or len(self.state['requests']) >= cfg['max_requests']:
            raise BudgetStop('request or elapsed-time budget exhausted')
        if self.used_completion_tokens()+maximum > cfg['max_completion_tokens']:
            raise BudgetStop('insufficient output-token budget to reserve the next request')
        row = {'sequence':len(self.state['requests'])+1,'started_at_epoch':time.time(),
               'reserved_completion_tokens':maximum,'request_sha256':hashlib.sha256(body).hexdigest(),
               'request_bytes':len(body),'status':'reserved'}
        self.state['requests'].append(row)
        self.save()  # persist the reservation before making a potentially billable request
        print(f'[budget] request {row["sequence"]}/{cfg["max_requests"]}; '
              f'output reserved/used {self.used_completion_tokens()}/{cfg["max_completion_tokens"]}',flush=True)
        try:
            kwargs['timeout'] = min(kwargs.get('timeout',180),180,remaining_s)
            with self.transport(request,*args,**kwargs) as response:
                raw = response.read()
            received = json.loads(raw)
            usage = received.get('usage') or {}
            completion = usage.get('completion_tokens')
            if type(completion) is not int or not 0 <= completion <= maximum:
                raise ValueError('missing or invalid completion usage')
            row.update(status='received',response_id=received.get('id'),
                       response_model=received.get('model'),usage=usage,
                       response_sha256=hashlib.sha256(raw).hexdigest(),
                       finish_reasons=[c.get('finish_reason') for c in received.get('choices',[])])
            self.save()
            print(f'[budget] received {row["sequence"]}; completion={completion}; '
                  f'total={self.used_completion_tokens()}',flush=True)
            return io.BytesIO(raw)
        except Exception as error:
            row.update(status='uncertain',error_type=type(error).__name__)
            if hasattr(error,'code'):
                row['http_status'] = error.code
            self.save()  # leave the complete reservation charged; never auto-retry uncertainty
            raise BudgetStop(f'transport/usage uncertainty: {type(error).__name__}') from None
        finally:
            row['elapsed_s'] = round(time.time()-row['started_at_epoch'],3)
            self.save()
