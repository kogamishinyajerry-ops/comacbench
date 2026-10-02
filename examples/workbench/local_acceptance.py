"""Non-destructive local handoff: preflight, scoped tests, native controls, evidence ZIP.

No installation, downloads, git writes, credentials, model calls or source edits.
Works in a clean Git checkout or a verified SOURCE_SNAPSHOT.json scoped export.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import subprocess
import sys
import zipfile

REPOSITORY = 'kogamishinyajerry-ops/comacbench'
BASE = '59f3dbe659b750964f5a81c99eb619352657c2ae'


def hashed(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
    return h.hexdigest()


def git(repo, *args):
    p=subprocess.run(['git','-C',str(repo),*args],capture_output=True,text=True,
                     encoding='utf-8',errors='replace',timeout=30)
    if p.returncode:raise ValueError('git_metadata_failed: '+args[0])
    return p.stdout.strip()


def source_identity(repo: Path, expected: str | None = None) -> dict:
    marker=repo/'SOURCE_SNAPSHOT.json'
    if marker.is_file():
        data=json.loads(marker.read_text(encoding='utf-8'))
        if data.get('repository')!=REPOSITORY or not re.fullmatch(r'[0-9a-f]{40}',data.get('base_commit','')):
            raise ValueError('snapshot_identity')
        files=data.get('files')
        if not isinstance(files,dict) or not 1<=len(files)<=500:raise ValueError('snapshot_inventory')
        for name,digest in files.items():
            path=PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name:
                raise ValueError('snapshot_path')
            f=repo/name
            if any(p.is_symlink() for p in [f,*f.parents] if p!=repo.parent):raise ValueError('snapshot_link')
            if not f.is_file() or hashed(f)!=digest:raise ValueError('snapshot_file_changed: '+name)
        # Python cache is derived and deliberately not part of source identity.
        actual={p.relative_to(repo).as_posix() for p in repo.rglob('*') if p.is_file()
                and '__pycache__' not in p.parts and p.name!='SOURCE_SNAPSHOT.json'}
        if actual!=set(files):raise ValueError('snapshot_unregistered_files')
        result={'kind':'scoped_source_base_plus_overlay','base_commit':data['base_commit'],'dirty':False,
                'source_sha256':hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
                'repository':REPOSITORY,'scope':data.get('scope'),'attested':False}
    else:
        if Path(git(repo,'rev-parse','--show-toplevel')).resolve()!=repo:
            raise ValueError('repo_must_be_git_root')
        remote=git(repo,'remote','get-url','origin')
        allowed=(f'https://github.com/{REPOSITORY}', f'https://github.com/{REPOSITORY}.git',
                 f'git@github.com:{REPOSITORY}.git', f'ssh://git@github.com/{REPOSITORY}.git')
        if remote not in allowed:raise ValueError('unexpected_remote; inspect locally, do not dump credential-bearing URLs')
        head=git(repo,'rev-parse','HEAD')
        ancestor=subprocess.run(['git','-C',str(repo),'merge-base','--is-ancestor',BASE,head],capture_output=True)
        if ancestor.returncode:raise ValueError('PR7_base_not_in_history; use the pinned native branch')
        status=git(repo,'status','--porcelain=v1','--untracked-files=all')
        result={'kind':'git_checkout','commit':head,'branch':git(repo,'branch','--show-current'),
                'dirty':bool(status),'status':status,'repository':REPOSITORY,'attested':False}
    if expected and result.get('commit')!=expected:raise ValueError('unexpected_HEAD; --expected-head applies to Git checkouts, not source overlays')
    return result


def run_step(repo, out, name, args, timeout=900):
    log=out/(name+'.log')
    env=dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1')
    # An opt-in test flag must not make the normal fixture suite run undocumented solves.
    env.pop('COMACBENCH_TEST_CCX',None)
    with log.open('xb') as f:
        try:
            p=subprocess.run([sys.executable,*args],cwd=repo,stdout=f,stderr=subprocess.STDOUT,
                             env=env,timeout=timeout)
            code=p.returncode
        except subprocess.TimeoutExpired:
            # Do not retry a timed-out solver workflow automatically. Its session and
            # pending jobs are retained; inspect remaining children on the target host.
            code=124
    return {'step':name,'returncode':code,'log':log.name}


def finish(out, result):
    (out/'handoff-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    files={p.relative_to(out).as_posix():hashed(p) for p in sorted(out.rglob('*')) if p.is_file()}
    (out/'evidence-manifest.json').write_text(json.dumps(files,indent=2)+'\n',encoding='utf-8')
    archive=out.with_name(out.name+'.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(out.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(out).as_posix())
    print(json.dumps({'status':result['status'],'evidence_zip':str(archive),
                      'native_calibration_verified':result['native_calibration_verified']},ensure_ascii=False))


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--ccx')
    p.add_argument('--expected-head')
    p.add_argument('--run-native',action='store_true',help='Explicitly run real solver controls after preflight/tests')
    a=p.parse_args(argv)
    repo,out=a.repo.resolve(),a.out.resolve()
    if out==repo or repo in out.parents or out in repo.parents:
        p.error('--out must be a new directory outside the source workspace')
    if out.exists() or out.with_name(out.name+'.zip').exists():p.error('output or evidence ZIP already exists')
    out.mkdir(parents=True)
    result={'protocol':'comacbench.native-handoff.v1','status':'BLOCKED',
            'created_at':datetime.now(timezone.utc).isoformat(),'steps':[],
            'native_calibration_verified':False,'model_experiment_verified':False,
            'isolated_transfer_verified':False,'full_repository_tested':False,
            'python':sys.version,'platform':platform.platform(),'repo_path':str(repo)}
    try:
        if sys.version_info<(3,11):raise ValueError('Python_3.11_or_later_required')
        result['source']=source_identity(repo,a.expected_head)
        binary=a.ccx or os.environ.get('CCX_BIN') or shutil.which('ccx')
        if not binary and Path('/opt/homebrew/bin/ccx').is_file():binary='/opt/homebrew/bin/ccx'
        result['ccx_discovered']=str(Path(binary).expanduser().resolve()) if binary else None
        if not a.run_native:
            result['status']='PREFLIGHT_RECORDED; native not executed'
            returncode=0
        else:
            if result['source']['dirty']:raise ValueError('dirty_worktree; preserve changes, isolate or commit before acceptance')
            if not binary or not Path(binary).expanduser().is_file():raise ValueError('ccx_missing; install/authorize separately, never substitute a fixture')
            binary=str(Path(binary).expanduser().resolve())
            step=run_step(repo,out,'01-scoped-tests',['-m','unittest','discover','-s','tests','-p','test_workbench*.py','-v'])
            result['steps'].append(step)
            if step['returncode']!=0:raise ValueError('scoped_tests_failed')
            for label,negative in (('reference',None),('stale','stale'),('false-ready','false-ready')):
                args=['examples/workbench/native_reference.py','--out',str(out/label),'--ccx',binary]
                if negative:args+=['--negative',negative]
                step=run_step(repo,out,'02-native-'+label,args,900)
                result['steps'].append(step)
                if step['returncode']!=0:raise ValueError('native_control_failed: '+label)
                record=json.loads((out/label/'report/report.json').read_text(encoding='utf-8'))
                obs=record['observation']
                if label=='reference':
                    if not (obs['complete'] and obs['counts'].get('solver_calls')==3 and obs['actions_used']==15
                            and obs['artifacts']['review']['payload']['claim']=='needs_review'):
                        raise ValueError('native_reference_semantics')
                else:
                    expected='unverified_targets' if label=='stale' else 'false_completion_claim'
                    if obs['complete'] or record['events'][-1]['result']['code']!=expected:
                        raise ValueError('native_negative_semantics')
            # Test a relocated archive and a tampered COPY. Never edit original evidence.
            relocated=out/'relocated-session';shutil.copytree(out/'reference/session',relocated)
            step=run_step(repo,out,'03-relocation',['-m','comacbench.workbench','observe',str(relocated)])
            result['steps'].append(step)
            if step['returncode']!=0:raise ValueError('relocation_replay_failed')
            altered=out/'tampered-copy';shutil.copytree(relocated,altered)
            dat=next((altered/'native').glob('*/model.dat'))
            with dat.open('ab') as f:f.write(b'\nINTENTIONAL_TAMPER_TEST\n')
            step=run_step(repo,out,'04-tamper-rejection',['-m','comacbench.workbench','observe',str(altered)])
            result['steps'].append(step)
            log=(out/step['log']).read_text(encoding='utf-8',errors='replace')
            if step['returncode']!=2 or 'native_archive_changed' not in log:raise ValueError('tamper_not_detected_by_expected_guard')
            after=source_identity(repo,a.expected_head)
            if after!=result['source']:raise ValueError('source_changed_during_acceptance')
            result['native_calibration_verified']=True
            result['status']='NATIVE_CALIBRATION_PASS; model/engineering approval not evaluated'
            returncode=0
    except (ValueError,OSError,KeyError,StopIteration,subprocess.SubprocessError) as exc:
        result['error']=str(exc)
        returncode=2
    finish(out,result)
    return returncode


if __name__=='__main__':raise SystemExit(main())
