"""Platform-owned OpenFOAM 10 execution; no contributed shell commands."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import uuid

from .backward_step import INPUTS, STAGES, audit_inputs, audit_mesh, audit_solution

IMAGE='sha256:d6ff1f9a2e7bc3c9177f373bebbdeb542fd8b49144afc24d5e3a3cd9bfae253d'
WALL_SHEAR='''
functions { wallShear { type wallShearStress; libs ("libfieldFunctionObjects.so");
patches (lowerWall); writeControl writeTime; } }
'''


def environment():
    r=subprocess.run(['docker','image','inspect',IMAGE],capture_output=True,text=True,timeout=15)
    if r.returncode:raise RuntimeError('需要本地 OpenFOAM 10 镜像 '+IMAGE+'；未自动下载镜像。')
    data=json.loads(r.stdout)[0]
    if data['Id']!=IMAGE:raise RuntimeError('OpenFOAM 镜像身份不匹配')
    return {'image_id':data['Id'],'architecture':data['Architecture'],'solver':'OpenFOAM Foundation 10'}


def native_step(work, name, deadline):
    if name not in {'blockMesh','checkMesh','simpleFoam'}:raise ValueError('unsupported native step')
    container='comac-cfd-'+uuid.uuid4().hex
    command=['docker','run','--rm','--pull','never','--name',container,'--network','none',
             '--platform','linux/amd64','--cpus','2','--memory','4g','--pids-limit','128',
             '-v',str(work)+':/work','-w','/work','--entrypoint','bash',IMAGE,'-c',
             'source /opt/openfoam10/etc/bashrc && '+name+' -case /work/case']
    started=time.monotonic();remaining=deadline-started
    if remaining<=0:return {'exit':None,'timeout':True,'seconds':0,'step':name}
    timed_out=False
    with (work/('log.'+name)).open('wb') as log:
        try:
            r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=remaining)
            code=r.returncode
        except subprocess.TimeoutExpired:
            timed_out=True;code=None
        finally:
            # Only the unique container of this stage is affected, also on interrupt.
            subprocess.run(['docker','rm','-f',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15)
    return {'exit':code,'timeout':timed_out,'seconds':round(time.monotonic()-started,3),'step':name}


def capture(work):
    files={}
    for path in sorted(work.rglob('*')):
        if path.is_symlink():raise ValueError('evidence contains symlink')
        if not path.is_file() or path.name=='evidence.json':continue
        raw=path.read_bytes();name=str(path.relative_to(work))
        origin='candidate_input' if name.startswith('submitted/') else 'candidate_script' if name=='make_case.py' else 'platform' if name.startswith('case/') and name[5:] in INPUTS else 'native_solver'
        if name=='script-result.json':origin='candidate_execution'
        files[name]={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'origin':origin}
    manifest={'protocol':'comacbench.cfd-evidence.v1','files':files}
    p=work/'evidence.json';p.write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    return {'directory':str(work),'manifest':str(p),'manifest_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'file_count':len(files)}


def evaluate(task, code, timeout):
    from ..sandbox import IsolatedRun
    root=os.environ.get('COMAC_CFD_EVIDENCE_ROOT')
    if root:Path(root).mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='cfd-step-',dir=root)).resolve()
    (work/'make_case.py').write_text(code)
    deadline=time.monotonic()+timeout
    audit={'profile':'openfoam10.backward_step.v1','checks':{k:'not_checked' for k in STAGES},'issues':[]}
    details={'kind':'cfd_step','cfd_audit':audit,'native_steps':[],'solver_executed':False}
    def failed(stage,code,message):
        audit['checks'][stage]='failed'
        audit['issues'].append({'code':code,'field':stage,'message':message,'suggested_fix':'对照公开契约修复后建立新运行；原始证据已保留。'})
    try:
        iso=IsolatedRun()
        try:
            run=iso.run(iso.write('make_case.py',code),min(120,max(.01,deadline-time.monotonic())))
            if isinstance(run['stdout'],bytes):run['stdout']=run['stdout'].decode('utf-8',errors='replace')
            (work/'script-result.json').write_text(json.dumps(run,ensure_ascii=False,indent=2))
            if run['timeout'] or run['exit']!=0:
                failed('inputs','script_failed','生成算例脚本未正常结束。')
                return details
            checked=audit_inputs(iso.dir/'case')
            audit['issues'].extend(checked['issues'])
            audit['checks']['inputs']='passed' if checked['passed'] else 'failed'
            # Never copy untrusted output trees into the native solver's workspace.
            for name in INPUTS:
                src=iso.dir/'case'/name
                if src.is_file() and not any(p.is_symlink() for p in [src,*src.parents] if p.is_relative_to(iso.dir)) and src.stat().st_size<=16*1024*1024:
                    dest=work/'submitted'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
            if not checked['passed']:return details
        finally:
            shutil.rmtree(iso.dir)
        shutil.copytree(work/'submitted',work/'case')
        control=work/'case/system/controlDict'
        control.write_text(control.read_text()+WALL_SHEAR)
        details['environment']=environment()
        for name in ('blockMesh','checkMesh'):
            rr=native_step(work,name,deadline);details['native_steps'].append(rr)
            if rr['exit']!=0 or rr['timeout']:
                failed('mesh','mesh_invalid',name+' 未成功结束。');return details
        try:
            mesh,summary=audit_mesh(work/'case',(work/'log.checkMesh').read_text(),checked['parsed'])
        except (ValueError,TypeError,KeyError,IndexError,OSError) as e:
            reason=str(e)
            code=reason if reason in {'mesh_below_minimum','inlet_profile_mismatch'} else 'mesh_invalid'
            failed('mesh',code,reason);return details
        audit['checks']['mesh']='passed';audit['mesh']=summary
        rr=native_step(work,'simpleFoam',deadline);details['native_steps'].append(rr)
        details['solver_executed']=True
        if rr['exit']!=0 or rr['timeout']:
            failed('solver','solver_failed','simpleFoam 非零退出或超时。');return details
        audit['checks']['solver']='passed'
        solution=audit_solution(work/'case',(work/'log.simpleFoam').read_text(),mesh,task['reference']['values']['reattachment_x_over_h'])
        audit['checks'].update(solution.pop('checks'));audit['issues'].extend(solution.pop('issues'));audit.update(solution)
        if audit.get('qoi') and not audit['qoi']['within_reference']:
            failed('qoi','qoi_outside_reference','再附着长度超出声明的 10% 参考带。')
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as e:
        failed('solver','solver_failed',str(e))
    finally:
        try:details['evidence']=capture(work)
        except (OSError,ValueError) as e:failed('solver','evidence_capture_failed',str(e))
        audit['passed']=all(v=='passed' for v in audit['checks'].values())
    return details
