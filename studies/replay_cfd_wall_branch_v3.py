"""Recompute 36 saved fields before releasing the Re=300 v3 matrix."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from studies.cfd_re300_v3 import reduce
from studies.cfd_step_sensitivity import sha,save,DOMAINS
from studies.run_cfd_re300_v3 import identity
from studies.verify_cfd_primary_delivery import verify_files

PILOTS=('retention-control-u5-d30-g1','re300-u5-d30-g1')


def compare_snapshot(new,old,reynolds):
    if reynolds==200:
        for key,value in old.items():
            if key=='quadratic_association':
                if any(new[key][k]!=v for k,v in value.items()):raise ValueError('Re=200 diagnostic estimate changed')
            elif new[key]!=value:raise ValueError('Re=200 primary/native quantity changed: '+key)
    else:
        mapping={'iteration':'iteration','native_association':'native_primary','first_layer_association':'first_layer',
                 'region':'primary_region','velocity_region':'velocity_region','flux':'flux'}
        for a,b in mapping.items():
            if new[a]!=old[b]:raise ValueError('Re=300 primary/native quantity changed: '+a)
        if new['native_association']!=old['native_U']:raise ValueError('Re=300 independent U identity changed')
        root=new['quadratic_association']['selected']
        if len(old['quadratic_upcrossings'])!=1 or any(root[k]!=old['quadratic_upcrossings'][0][k] for k in ('x_h','direction','bracket_indices','bracket')):
            raise ValueError('unexpected pilot diagnostic root')
        if new['near_wall_gap']!=old['candidate_relative_gap']:raise ValueError('pilot diagnostic magnitude changed')


def replay(out,verify=False):
    protocol=identity(out);target=out/'compatibility'
    if not verify:
        if target.exists():raise ValueError('compatibility attempt exists; retain it')
        target.mkdir()
    parent=Path(protocol['parent']);legacy=Path(protocol['legacy']);pilot=Path(protocol['pilot'])
    jobs=[(legacy/f're200-u{u}-d{d}-g{s}',200) for u,d in DOMAINS for s in (1,2,4,8)]+[(pilot/cid,300) for cid in PILOTS]
    diagnostics=json.loads((pilot/'failure-analysis.json').read_text())['cases']
    rows=[];native_files=0
    for work,reynolds in jobs:
        old=json.loads((work/'result.json').read_text());manifest=work/'evidence.json'
        if sha(manifest)!=old['evidence']['manifest_sha256']:raise ValueError('old native manifest drift')
        entries=json.loads(manifest.read_text())['files'];verify_files(work,{k:v['sha256'] for k,v in entries.items()});native_files+=len(entries)
        if old['config']['reynolds']!=reynolds:raise ValueError('unexpected native Reynolds number')
        current=json.loads(json.dumps(reduce(work,old['config'],historical=reynolds==200)))
        if not current['valid']:raise ValueError('new saved-field checks failed: '+work.name)
        reference=json.loads((parent/(work.name+'.json')).read_text()) if reynolds==200 else next(r for r in diagnostics if r['id']==work.name)
        if reynolds==200:
            if reference['result_sha256']!=sha(work/'result.json') or reference['evidence_sha256']!=sha(manifest):raise ValueError('v2 comparison origin drift')
        elif reference['result_sha256']!=sha(work/'result.json'):raise ValueError('pilot comparison origin drift')
        if len(current['snapshots'])!=2 or len(reference['snapshots'])!=2:raise ValueError('complete snapshot pairs required')
        for new,previous in zip(current['snapshots'],reference['snapshots']):compare_snapshot(new,previous,reynolds)
        current.update(id=work.name,config=old['config'],source_path=str(work),source_result_sha256=sha(work/'result.json'),
                       source_evidence_sha256=sha(manifest),primary_and_native_unchanged=True,legacy_diagnostic_unchanged=reynolds==200)
        path=target/(work.name+'.json')
        if verify:
            if json.loads(path.read_text())!=current:raise ValueError('saved compatibility result differs: '+work.name)
        else:save(path,current)
        rows.append({'id':work.name,'reynolds':reynolds,'snapshots':2,'valid':current['valid'],
                     'native_qoi':current['qoi']['x_over_h'],'quadratic_qoi':current['snapshots'][-1]['quadratic_x_h'],
                     'relative_gap':current['wall']['relative_native_gap'],'native_unchanged':True})
        print(json.dumps({'compatibility_case':work.name,'done':len(rows),'total':18,'snapshots':2,'native_unchanged':True}),flush=True)
    result={'passed':len(rows)==18,'cases':len(rows),'snapshots':sum(r['snapshots'] for r in rows),'rows':rows,
            'native_records':native_files,'re200_cases':16,'re300_cases':2,'protocol_sha256':sha(out/'protocol.json')}
    path=target/'analysis.json'
    if verify:
        if json.loads(path.read_text())!=result:raise ValueError('compatibility summary drift')
        receipt={'passed':True,'cases':18,'snapshots':36,'protocol_sha256':sha(out/'protocol.json'),
                 'files':{str(p.relative_to(out)):sha(p) for p in sorted(target.glob('*.json'))}}
        seal=out/'compatibility-verification.json'
        if seal.exists():
            if json.loads(seal.read_text())!=receipt:raise ValueError('compatibility verification seal drift')
        else:save(seal,receipt)
    else:save(path,result)
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}),flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['run','verify']);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    replay(a.out.resolve(),a.command=='verify')
