"""Runnable stdio wrapper for a model-backed code agent, using an OpenAI-compatible endpoint.

Replace the HTTP call with your own agent invocation while preserving request/response.
Credentials come from named environment variables; stdout contains only protocol JSON.
"""
from pathlib import Path
import json
import os
import sys
import urllib.request

request=json.load(sys.stdin)
if request.get('protocol')!='comacbench.agent.v1':
    raise ValueError('unknown protocol')
if request.get('assets'):
    raise ValueError('this text-only example does not support public file assets; supply your own agent wrapper')
body={'model':os.environ['COMAC_MODEL_NAME'],'messages':[
    {'role':'system','content':'You are an engineering coding agent. Complete the user task. Return only the final requested source code, without private reasoning. Do not claim to have run tools you did not run.'},
    {'role':'user','content':request['prompt']}], 'max_tokens':32768}
url=os.environ['COMAC_MODEL_BASE'].rstrip('/')+'/chat/completions'
req=urllib.request.Request(url,data=json.dumps(body).encode(),headers={
    'Content-Type':'application/json','Authorization':'Bearer '+os.environ['COMAC_MODEL_KEY']})
with urllib.request.urlopen(req,timeout=840) as response:
    result=json.load(response)
Path('provider-response.json').write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8')
choice=result['choices'][0]
if choice.get('finish_reason')=='length':
    raise ValueError('model output truncated; keep this failed attempt and use a new protocol/version for a larger cap')
answer=choice['message'].get('content')
if not isinstance(answer,str) or not answer.strip():
    raise ValueError('empty final answer')
print(json.dumps({'protocol':'comacbench.agent.v1','task_id':request['task_id'],
                  'answer':answer,'usage':result.get('usage'),
                  'model':result.get('model'),'finish_reason':choice.get('finish_reason')},ensure_ascii=False))
