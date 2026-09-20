"""Resume preserved G3 attempts without changing any numerical settings."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from studies.cfd_step_sensitivity import sha,save,evidence
from studies.cfd_fourth_grid import native,reduce,run_case


def resume(source,out):
    source=source.resolve();old=json.loads((source/'result.json').read_text())
    if old['status']!='interrupted_for_separately_bridged_acceleration' or old['valid']:raise ValueError('expected preserved interrupted attempt')
    if sha(source/'evidence.json')!=old['evidence']['manifest_sha256']:raise ValueError('source manifest drift')
    for name,item in json.loads((source/'evidence.json').read_text())['files'].items():
        if sha(source/name)!=item['sha256']:raise ValueError('source native drift')
    case=source/'case';fields=('U','p','phi','wallShearStress')
    checkpoint=max(int(p.name) for p in case.iterdir() if p.name.isdecimal() and int(p.name)>0 and all((p/f).is_file() for f in fields))
    work=out/source.name
    if work.exists():raise ValueError('destination exists')
    work.mkdir(parents=True)
    def ignore(path,names):
        if Path(path)==case:return [n for n in names if n.isdecimal() and int(n)>checkpoint]
        return []
    shutil.copytree(case,work/'case',ignore=ignore)
    for name in ('generated-inputs','mapped-initial-fields'):shutil.copytree(source/name,work/name)
    for name in ('log.blockMesh','log.checkMesh','log.mapFields'):shutil.copyfile(source/name,work/name)
    shutil.copyfile(source/'log.simpleFoam',work/'log.simpleFoam.initial')
    shutil.copytree(case/str(checkpoint),work/'restart-inputs')
    p=work/'case/system/controlDict';text=p.read_text()
    if text.count('startFrom       startTime')!=1:raise ValueError('unexpected restart control')
    p.write_text(text.replace('startFrom       startTime','startFrom       latestTime'))
    continuation={'source':str(source),'source_result_sha256':sha(source/'result.json'),
                  'source_evidence_sha256':sha(source/'evidence.json'),'checkpoint':checkpoint,
                  'restart_field_hashes':{f:sha(work/'restart-inputs'/f) for f in fields},
                  'source_sha256':sha(__file__),'only_control_change':'startFrom latestTime'}
    row={k:old[k] for k in ('id','config','kind','origin','source_sha256','policy')}
    row.update(continuation=continuation,valid=False,status='running',steps=[]);save(work/'running.json',row)
    started=time.monotonic()
    try:
        row['steps'].append(native(work,'simpleFoam',deadline=started+14400))
        row.update(reduce(work,row['config']));row['status']='complete'
    except Exception as exc:row.update(status='failed',error=str(exc))
    row['seconds']=time.monotonic()-started;row['evidence']=evidence(work);save(work/'result.json',row)
    print(json.dumps({k:row.get(k) for k in ('id','status','valid','seconds','error')}),flush=True)
    return row


def main():
    source=Path(sys.argv[1]);out=Path(sys.argv[2]);prior=Path(sys.argv[3])
    jobs=[('resume',source/f're100-u{u}-d30-g8') for u in (5,10)]+[('new',(u,60)) for u in (5,10)]
    def one(job):
        kind,item=job
        if kind=='resume':return resume(item,out)
        u,d=item;scale=8
        config={'scale':scale,'upstream_h':u,'downstream_h':d,'reynolds':100,'expected_cells':(5*u+2*173)*20*scale**2,
                'near_step_dx_h':.1/scale,'spanwise_layers':1,'grading_sections':[[10,100,1],[20,40,4],[30,33,1]]}
        return run_case(out,f're100-u{u}-d{d}-g8',config,prior/f're100-u{u}-d{d}-g4')
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(one,jobs))

if __name__=='__main__':main()
