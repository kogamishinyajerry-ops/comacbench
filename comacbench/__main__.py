"""CLI orchestration only: all scoring stays in existing runner modules."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import time

import yaml

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback
    import msvcrt

    def _msvcrt_flock(fd, _flags):
        fd.seek(0)
        msvcrt.locking(fd.fileno(), msvcrt.LK_NBLCK, 1)

    class fcntl:  # minimal shim of the POSIX module surface we use
        LOCK_EX = 1
        LOCK_NB = 2
        flock = staticmethod(_msvcrt_flock)

from .agent import identity as agent_identity, load_agent
from .pack import validate_pack, fingerprint, digest
from .report import write_report

REPO=Path(__file__).resolve().parents[1]
MODULES={'code_exec':'runners.code_exec','simulation_agent':'runners.simulation_agent'}


def save(path, data):
    path=Path(path)
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    tmp.replace(path)


def engine_identity():
    files={str(p.relative_to(REPO)):digest(p) for directory in ('runners','comacbench')
           for p in sorted((REPO/directory).rglob('*'))
           if p.is_file() and p.suffix in {'.py','.html'} and '__pycache__' not in p.parts}
    return files


def execution_environment(validation):
    result={'python':{'path':sys.executable,'sha256':digest(sys.executable)},
            'dependencies':{},'solvers':{}}
    for name in ('PyYAML','numpy','scipy','scikit-learn'):
        try:
            result['dependencies'][name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            raise ValueError(f'missing runtime dependency: {name}; use the repository evaluation environment')
    if any(t['adapter']=='simulation_agent' and t.get('exec_kind','ccx_fea')=='ccx_fea' for t in validation['tasks']):
        from runners.solvers.calculix import ccx_binary
        try:
            executable=ccx_binary()
            if not os.access(executable,os.X_OK): raise ValueError('solver is not executable')
            result['solvers']['calculix']={'path':executable,'sha256':digest(executable)}
        except (RuntimeError,OSError) as e:
            raise ValueError(f'solver preflight: {e}') from e
    if any(t.get('exec_kind')=='cfd_step' for t in validation['tasks']):
        from runners.solvers.cfd_step_runtime import environment
        result['openfoam']=environment()
    return result


def run_suite(root, suite, out, provider, seed, env, resume):
    rows=[r for r in validate_pack(root)['tasks'] if r['suite']==suite]
    adapters={r['adapter'] for r in rows}
    if len(adapters)!=1:
        raise ValueError('each suite must use one adapter')
    command=[sys.executable,'-m',MODULES[adapters.pop()],'--tasks',str(root/'tasks'/suite),
             '--out',str(out),'--provider',provider,'--seed',str(seed)]
    if resume:
        command.append('--resume')
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.with_suffix('.log').open('ab') as log:
        proc=subprocess.run(command,cwd=REPO,env=env,stdout=log,stderr=subprocess.STDOUT)
    if proc.returncode:
        raise ValueError(f'runner failed ({proc.returncode}); see {out.with_suffix(".log")}')
    return command


def result_rows(root, report, runs, provider):
    rows=[]
    for task in report['tasks']:
        p=runs/task['suite']/f'result_{task["id"]}.json'
        if not p.exists():
            continue
        r=json.loads(p.read_text())
        try:
            details=json.loads(r.get('artifacts',{}).get('grade_details','{}'))
        except (ValueError,TypeError):
            details={}
        spec=yaml.safe_load((root/task['path']).read_text())
        rows.append({**task,'validity_gate':r.get('validity_gate'),'score':r.get('score'),
                     'subscores':r.get('subscores'),'failure_mode':r.get('failure_mode'),
                     'gate_failures':r.get('gate_failures'), 'details':details,
                     'full_pass':r.get('validity_gate')==1 and r.get('score')==1,
                     'result_file':str(p), 'result_sha256':digest(p),
                     'requirements':spec.get('evaluation',{}).get('requirements',[]),
                     'scope':spec.get('evaluation',{}).get('scope',''),
                     'evidence_level': 'solver_executed' if details.get('solver_executed') or details.get('kind')=='ccx_fea' and details.get('ccx_s') is not None else 'executable_checks' if details.get('kind')=='unit_tests' else 'input_audit' if details.get('deck_audit') or details.get('cfd_audit') else 'no_completed_execution',
                     'provider':provider})
    return rows


def execute(args):
    root=Path(args.pack).resolve()
    validation=validate_pack(root)
    if not validation['runnable']:
        print(json.dumps(validation,ensure_ascii=False,indent=2))
        return 2
    out=Path(args.out).resolve()
    if out==root or out.is_relative_to(root):
        raise ValueError('output directory must be outside the immutable pack')
    calibration=args.command=='calibrate'
    agent=None if calibration else Path(args.agent).resolve()
    if agent:
        load_agent(agent)
    ident={'protocol':'comacbench.run.v1','pack_sha256':fingerprint(root),
           'engine':engine_identity(),'seed':args.seed,'mode':args.command,
           'execution_environment':execution_environment(validation),
           'agent':{'name':'oracle','kind':'grader_calibration'} if calibration else agent_identity(agent)}
    out.mkdir(parents=True,exist_ok=True)
    with (out/'.lock').open('a+') as lock:
        try:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:  # POSIX: BlockingIOError; Windows: PermissionError from msvcrt
            raise ValueError('output directory is already running')
        state=out/'run.json'
        if state.exists():
            previous=json.loads(state.read_text())
            if not args.resume or previous.get('identity') != ident:
                raise ValueError('run identity mismatch or --resume missing; use a new --out')
        elif any(p.name!='.lock' for p in out.iterdir()):
            raise ValueError('output directory is not empty; use a new --out')
        rerun=[sys.executable,'-m','comacbench',args.command,str(root),'--out',str(out),'--seed',str(args.seed),'--resume']
        if agent:
            rerun+=['--agent',str(agent)]
        doc={'identity':ident,'validation':validation,'pack':validation['pack'],'status':'running',
             'started_at':time.strftime('%Y-%m-%dT%H:%M:%S%z'),'results':[],
             'mode':args.command,'agent':ident['agent'],'rerun':shlex.join(rerun)}
        save(state,doc)
        save(out/'validation.json',validation)
        env=dict(os.environ)
        env['PYTHONDONTWRITEBYTECODE']='1'
        env['COMAC_CFD_EVIDENCE_ROOT']=str(out/'cfd-evidence')
        provider='oracle' if calibration else 'external'
        if agent:
            env.update(COMAC_AGENT_CONFIG=str(agent),COMAC_AGENT_PACK_ROOT=str(root),COMAC_AGENT_AUDIT=str(out/'agent-audit'))
        try:
            for suite in dict.fromkeys(t['suite'] for t in validation['tasks']):
                run_suite(root,suite,out/'runs'/suite,provider,args.seed,env,args.resume)
                doc['results']=result_rows(root,validation,out/'runs',provider)
                save(state,doc)
                write_report(out/'report.html',doc)
            if calibration:
                controls=[]
                for task in validation['tasks']:
                    spec=yaml.safe_load((root/task['path']).read_text())
                    for ci,control in enumerate(spec['evaluation']['negative_controls']):
                        stage=out/'control-packs'/f'{task["id"]}-{ci}'
                        if not stage.exists():
                            shutil.copytree(root,stage)
                            for f in (stage/'tasks'/task['suite']).glob('*.yaml'):
                                if f.name!=Path(task['path']).name:
                                    f.unlink()
                            np=stage/task['path']
                            neg=yaml.safe_load(np.read_text())
                            neg['grader']['oracle_source']=control['script']
                            np.write_text(yaml.safe_dump(neg,allow_unicode=True,sort_keys=False))
                        dest=out/'controls'/f'{task["id"]}-{ci}'
                        # Same adapter invocation, one task. Control copies are private calibration inputs.
                        module=MODULES[task['adapter']]
                        command=[sys.executable,'-m',module,'--tasks',str(stage/'tasks'/task['suite']),
                                 '--out',str(dest),'--provider','oracle','--seed',str(args.seed)]
                        if args.resume: command.append('--resume')
                        dest.parent.mkdir(parents=True,exist_ok=True)
                        with dest.with_suffix('.log').open('ab') as log:
                            rr=subprocess.run(command,cwd=REPO,env=env,stdout=log,stderr=subprocess.STDOUT)
                        if rr.returncode: raise ValueError(f'negative control runner failed: {dest}')
                        result=json.loads((dest/f'result_{task["id"]}.json').read_text())
                        details=json.loads(result.get('artifacts',{}).get('grade_details','{}'))
                        actual_issues=[i['code'] for i in (details.get('deck_audit') or details.get('cfd_audit') or {}).get('issues',[])]
                        expected=control.get('expected_issue')
                        controls.append({'task_id':task['id'],'control':control['script'],'score':result['score'],
                                         'max_score':control['max_score'],'passed':result['score']<=control['max_score'] and not result.get('voided') and (expected is None or expected in actual_issues),
                                         'expected_issue':expected, 'actual_issues':actual_issues,
                                         'gate_failures':result.get('gate_failures'),'failure_mode':result.get('failure_mode')})
                doc['controls']=controls
                doc['calibration_passed']=all(r['full_pass'] for r in doc['results']) and all(c['passed'] for c in controls)
            doc['status']='complete'
        except Exception as e:
            doc['status']='interrupted'
            doc['error']=str(e)
            doc['results']=result_rows(root,validation,out/'runs',provider)
            save(state,doc)
            write_report(out/'report.html',doc)
            raise
        save(state,doc)
        write_report(out/'report.html',doc)
        print(json.dumps({'status':doc['status'],'tasks':len(doc['results']),
                          'full_pass':sum(r['full_pass'] for r in doc['results']),
                          'calibration_passed':doc.get('calibration_passed'),
                          'report':str(out/'report.html'),'result':str(state)},ensure_ascii=False))
        return 0 if not calibration or doc['calibration_passed'] else 3


def main():
    ap=argparse.ArgumentParser(description='航空工程 Benchmark：连接 agent、预检贡献、校准判分、查看报告')
    sub=ap.add_subparsers(dest='command',required=True)
    val=sub.add_parser('validate',help='只读检查评测包，不调用 agent 或执行贡献代码')
    val.add_argument('pack'); val.add_argument('--out',help='新建目录，写入 JSON 和可视化反馈')
    init=sub.add_parser('init',help='复制一个完整可运行的三能力示例包作为贡献起点')
    init.add_argument('destination')
    sub.add_parser('catalog',help='列出仓库中的评测包与当前预检状态')
    for cmd in ('run','calibrate'):
        p=sub.add_parser(cmd,help='运行工程师 agent' if cmd=='run' else '执行参考实现与错误负例（管线自检）')
        p.add_argument('pack');p.add_argument('--out',required=True)
        p.add_argument('--seed',type=int,default=0);p.add_argument('--resume',action='store_true')
        if cmd=='run':p.add_argument('--agent',required=True)
    args=ap.parse_args()
    try:
        if args.command=='validate':
            v=validate_pack(args.pack)
            if args.out:
                out=Path(args.out).resolve()
                root=Path(args.pack).resolve()
                if out.is_relative_to(root): raise ValueError('output must be outside pack')
                out.mkdir(parents=True,exist_ok=False)
                save(out/'validation.json',v)
                write_report(out/'report.html',{'validation':v,'pack':v['pack'],'mode':'validation','results':[]})
            print(json.dumps(v,ensure_ascii=False,indent=2))
            return 0 if v['runnable'] else 2
        if args.command=='init':
            dest=Path(args.destination).resolve()
            shutil.copytree(REPO/'packs/aviation-core-v1',dest)
            print(json.dumps({'pack':str(dest),'next':f'{sys.executable} -m comacbench validate {shlex.quote(str(dest))}'},ensure_ascii=False))
            return 0
        if args.command=='catalog':
            print(json.dumps({'packs':[{'path':str(p.parent),**validate_pack(p.parent)} for p in sorted((REPO/'packs').glob('*/pack.yaml'))]},ensure_ascii=False))
            return 0
        return execute(args)
    except (OSError,ValueError,TypeError,KeyError,yaml.YAMLError) as e:
        print(json.dumps({'error':str(e)},ensure_ascii=False),file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
