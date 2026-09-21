"""One JSON request/response per local trusted agent process; no shell interpolation."""
from __future__ import annotations

import json
import hashlib
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time

from .pack import digest, safe_file, ID

PROTOCOL = 'comacbench.agent.v1'


def load_agent(path):
    path = Path(path).resolve()
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data,dict) or data.get('protocol') != PROTOCOL:
        raise ValueError('unsupported agent protocol')
    for k in ('name','revision'):
        if not isinstance(data.get(k),str) or not data[k].strip():
            raise ValueError(f'agent missing {k}')
    argv=data.get('command')
    if not isinstance(argv,list) or not argv or any(not isinstance(a,str) or not a or '\x00' in a for a in argv):
        raise ValueError('agent.command must be a nonempty argv array')
    timeout=data.get('timeout_s',300)
    if not isinstance(timeout,(int,float)) or isinstance(timeout,bool) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('agent.timeout_s must be finite and positive')
    env=data.get('env',[])
    if not isinstance(env,list) or any(not isinstance(e,str) or not e.isidentifier() for e in env):
        raise ValueError('agent.env must list environment variable names, never values')
    if any(e not in os.environ for e in env):
        raise ValueError('missing agent environment variable: '+', '.join(e for e in env if e not in os.environ))
    identity_env=data.get('identity_env',[])
    if not isinstance(identity_env,list) or any(e not in env for e in identity_env):
        raise ValueError('agent.identity_env must be a subset of declared env names')
    revision_files=data.get('revision_files',[])
    if not isinstance(revision_files,list) or not revision_files:
        raise ValueError('agent.revision_files must lock at least the wrapper source')
    files={f:digest(safe_file(path.parent,f)) for f in revision_files}
    resolved=[]
    for i,arg in enumerate(argv):
        if arg == '{python}':
            arg=sys.executable
        elif arg.startswith('./'):
            arg=str(safe_file(path.parent,arg))
        elif i==0:
            arg=shutil.which(arg) or arg
            if not Path(arg).is_file():
                raise ValueError('agent executable not found')
        resolved.append(arg)
    return data, resolved, {'config_sha256':digest(path),'revision_files':files,
                            'command_files':{str(i):digest(arg) for i,arg in enumerate(resolved) if Path(arg).is_file()},
                            'identity_env':{k:hashlib.sha256(os.environ[k].encode()).hexdigest() for k in identity_env},
                            'executable_sha256':digest(resolved[0])}


def identity(path=None):
    path=path or os.environ.get('COMAC_AGENT_CONFIG')
    if not path:
        raise ValueError('COMAC_AGENT_CONFIG is required')
    d,_,hashes=load_agent(path)
    return {'name':'external','model':d['name'],'revision':d['revision'],
            'protocol':PROTOCOL,'agent_kind':d.get('kind','user_agent'),**hashes}


def invoke(task, prompt, *, seed, expect):
    from runners.providers import ProviderError
    try:
        cfg, command, hashes=load_agent(os.environ['COMAC_AGENT_CONFIG'])
        root=Path(os.environ['COMAC_AGENT_PACK_ROOT']).resolve()
        audit=Path(os.environ['COMAC_AGENT_AUDIT']).resolve()
        if not ID.fullmatch(task.id):
            raise ValueError('invalid task id')
        audit.mkdir(parents=True,exist_ok=True)
        # Retain every attempt; reruns cannot replace the earlier failure evidence.
        attempt=Path(tempfile.mkdtemp(prefix=task.id+'-',dir=audit))
        workspace=attempt/'workspace'
        workspace.mkdir()
        assets=[]
        for a in task['input'].get('assets',[]):
            src=safe_file(root,a['path'])
            if digest(src) != a['digest'].removeprefix('sha256:'):
                raise ValueError('public asset digest mismatch')
            target=workspace/'inputs'/a['path']
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(src,target)
            assets.append({'path':str(target.relative_to(workspace)),'sha256':digest(target)})
        request={'protocol':PROTOCOL,'task_id':task.id,'seed':seed,'prompt':prompt,
                 'assets':assets,'output_contract':task['output_contract'],
                 'allowed_tools':task['allowed_tools'],'limits':task['limits'],
                 'answer_format':expect}
        raw_request=json.dumps(request,ensure_ascii=False)
        (attempt/'request.json').write_text(raw_request+'\n',encoding='utf-8')
        # The wrapper may request credentials by name; never persist their values.
        env={k:v for k,v in os.environ.items() if k in {'PATH','LANG','LC_ALL','TMPDIR','SYSTEMROOT'}}
        env.update({k:os.environ[k] for k in cfg.get('env',[])})
        env['PYTHONDONTWRITEBYTECODE']='1'
        t0=time.monotonic()
        # File-backed output bounds RAM. Contract rejects overlarge stdout after exit.
        with (attempt/'stdout.txt').open('wb') as stdout, (attempt/'stderr.txt').open('wb') as stderr:
            proc=subprocess.Popen(command,cwd=workspace,stdin=subprocess.PIPE,
                                  stdout=stdout,stderr=stderr,env=env,start_new_session=True)
            try:
                proc.communicate((raw_request+'\n').encode(),timeout=cfg.get('timeout_s',300))
                status={'exit_code':proc.returncode,'timeout':False}
            except subprocess.TimeoutExpired:
                if os.name=='nt':
                    proc.kill()
                else:
                    os.killpg(proc.pid,signal.SIGKILL)
                proc.communicate()
                status={'exit_code':proc.returncode,'timeout':True}
        status['duration_s']=round(time.monotonic()-t0,3)
        (attempt/'status.json').write_text(json.dumps(status)+'\n')
        if status['timeout']:
            raise ValueError('agent_timeout; original attempt retained')
        if proc.returncode != 0:
            raise ValueError('agent_process_failed; original stderr retained locally')
        if (attempt/'stdout.txt').stat().st_size > 4*1024*1024:
            raise ValueError('agent_response_too_large')
        response=json.loads((attempt/'stdout.txt').read_text(encoding='utf-8'))
        if not isinstance(response,dict) or response.get('protocol') != PROTOCOL or response.get('task_id') != task.id:
            raise ValueError('agent_response_identity_mismatch')
        raw=response.get('answer')
        if not isinstance(raw,str) or not raw.strip():
            raise ValueError('agent.answer must be nonempty final text or source code')
        # Existing provider normalizers keep code fences and thought handling consistent.
        from runners.providers import extract_code_block, extract_matlab_block, parse_answer
        answer = extract_code_block(raw) if expect=='code' else extract_matlab_block(raw) if expect=='matlab' else json.loads(raw) if expect=='json' else parse_answer(raw) if expect=='mcq' else raw
        if answer is None:
            raise ValueError('agent_answer_format_invalid')
        (attempt/'response.json').write_text(json.dumps(response,ensure_ascii=False)+'\n',encoding='utf-8')
        return {'answer':answer,'raw':raw,'attempts':1,
                'meta':{'provider':'external','model':cfg['name'],'revision':cfg['revision'],
                        'agent_kind':cfg.get('kind','user_agent'),'request_sha256':digest(attempt/'request.json'),
                        'response_sha256':digest(attempt/'response.json'),'audit_dir':str(attempt),**hashes}}
    except (ValueError,KeyError,TypeError,OSError) as e:
        raise ProviderError(f'external agent: {e}') from e
