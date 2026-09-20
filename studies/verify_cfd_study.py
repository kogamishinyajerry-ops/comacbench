"""Check source identity, full native evidence, declared matrix and analysis."""
from pathlib import Path
import json
import math
import contextlib
import io
import shutil
import tempfile
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from studies.cfd_step_sensitivity import sha, verify_case, grid_convergence, POLICY, DOMAINS, REFERENCES, write_case
from runners.solvers.cfd_profile import TEMPLATES
from runners.solvers.backward_step import mesh_data


def require(condition,message):
    if not condition:raise ValueError(message)


def verify_inputs(case,config):
    with tempfile.TemporaryDirectory() as tmp:
        expected=Path(tmp)
        generated=write_case(expected,config['scale'],config['upstream_h'],config['downstream_h'],config['reynolds'])
        require(generated==config,'Study input configuration mismatch')
        for name in TEMPLATES:
            require(sha(case/name)==sha(expected/name),'Native input disagrees with declared study: '+name)


def verify_decision(rows,groups,decision):
    require(decision['policy']==POLICY,'Decision policy changed')
    complete=len(rows)==12 and all(r['status']=='complete' and r['valid'] for r in rows)
    grids=len(groups)==4 and all(g['gci']['applicable'] and g['gci']['fine_gci']<=POLICY['fine_gci_max'] for g in groups)
    domain=decision['fine_domain_effect']
    domains=isinstance(domain,(int,float)) and math.isfinite(domain) and 0<=domain<=POLICY['fine_domain_effect_max']
    expected=complete and grids and domains
    require(decision['gate_passed'] is expected,'Tolerance gate contradicts native results')
    if not expected:require(decision['suggested_tolerance'] is None,'Failed gate cannot publish a tolerance')


def verify_common_domain(root):
    rows=[]
    for scale in (1,2,4):
        reference=None
        for up,down in DOMAINS:
            case=root/'re100'/f're100-u{up}-d{down}-g{scale}'/'case';mesh=mesh_data(case)
            cells=sorted((x,y) for x,y,z in mesh['centres'] if abs(z)<1e-12 and 0<x<.3)
            require(len(cells)==5600*scale**2,'Common-domain cell count changed')
            if reference is None:reference=cells
            delta=max(abs(a-b) for p,q in zip(cells,reference) for a,b in zip(p,q))
            require(delta<=1e-10,'Extending domain also changed common-region cell centres')
            rows.append({'scale':scale,'upstream_h':up,'downstream_h':down,'common_downstream_cells':len(cells),
                         'max_xy_difference_m':delta,'points_sha256':sha(case/'constant/polyMesh/points'),
                         'faces_sha256':sha(case/'constant/polyMesh/faces')})
    saved=json.loads((root/'geometry-check.json').read_text())
    require(saved['passed'] is True and saved['rows']==rows,'Geometry report does not reproduce')
    return True


def verify(root):
    root=Path(root).resolve();reports=[]
    if not (root/'re100/analysis.json').is_file():raise ValueError('Re=100 analysis missing; study is not verified')
    prior=json.loads((root/'prior-artifacts.json').read_text())
    for name,digest in prior.items():
        require(sha(ROOT/name)==digest,'Prior artifact changed: '+name)
    total_files=0
    for directory in (root/'re100',root/'re200'):
        if not directory.exists():continue
        if not (directory/'analysis.json').exists():raise ValueError('Study still incomplete: '+str(directory))
        protocol=json.loads((directory/'protocol.json').read_text());analysis=json.loads((directory/'analysis.json').read_text())
        identity=protocol['identity']
        require(analysis['protocol_sha256']==sha(directory/'protocol.json'),'Protocol digest mismatch')
        require(len(protocol['case_ids'])==len(protocol['configs'])==12 and len(set(protocol['case_ids']))==12,'Incomplete declared matrix')
        require(identity['policy']==POLICY,'Protocol policy changed')
        require(sha(directory/'frozen-source/cfd_step_sensitivity.py')==identity['study_source'],'Study source digest mismatch')
        for name,digest in identity['engine'].items():
            require(sha(directory/'frozen-source'/name)==digest,'Frozen engine changed: '+name)
        rows=[]
        for cid,config in zip(protocol['case_ids'],protocol['configs']):
            p=directory/cid/'result.json';r=json.loads(p.read_text())
            require(r['identity']==identity and r['config']==config and r['id']==cid,'Native run identity mismatch: '+cid)
            require(sha(p)==analysis['results_sha256'][cid],'Result digest mismatch: '+cid)
            verify_inputs(directory/cid/'case',config)
            verify_case(directory/cid,r)
            total_files+=r['evidence']['file_count'];rows.append(r)
        expected={(up,down,scale) for up,down in DOMAINS for scale in (1,2,4)}
        require({(r['config']['upstream_h'],r['config']['downstream_h'],r['config']['scale']) for r in rows}==expected,'Domain/grid factorial mismatch')
        require(all(r['config']['reynolds']==protocol['reynolds'] for r in rows),'Mixed Reynolds numbers')
        require({(g['upstream_h'],g['downstream_h']) for g in analysis['groups']}==set(DOMAINS),'Missing/duplicate domain analysis')
        for r in rows:
            if r.get('qoi'):
                reference=REFERENCES[protocol['reynolds']]
                require(r['reference']==reference and r['relative_error']==abs(r['qoi']['x_over_h']-reference)/reference,'Reference error mismatch')
        for group in analysis['groups']:
            values=sorted((r for r in rows if r['config']['upstream_h']==group['upstream_h'] and r['config']['downstream_h']==group['downstream_h']),key=lambda r:r['config']['scale'])
            require([r['config']['scale'] for r in values]==[1,2,4],'Grid family mismatch')
            if all(r.get('qoi') for r in values):require(grid_convergence([r['qoi']['x_over_h'] for r in values])==group['gci'],'GCI reduction mismatch')
        fine=[r for r in rows if r['config']['scale']==4 and r.get('qoi')]
        domain=(max(r['qoi']['x_over_h'] for r in fine)-min(r['qoi']['x_over_h'] for r in fine))/fine[0]['reference'] if len(fine)>1 else None
        require(domain==analysis['tolerance_decision']['fine_domain_effect'],'Domain effect mismatch')
        require(analysis['case_count']==len(rows) and analysis['valid_count']==sum(r['valid'] for r in rows),'Run counts mismatch')
        verify_decision(rows,analysis['groups'],analysis['tolerance_decision'])
        if protocol['reynolds']==200:
            p=Path(identity['prior_decision']['path']);require(sha(p)==identity['prior_decision']['sha256'],'Prior decision digest mismatch')
            require(p==root/'re100/analysis.json','Unexpected prior decision')
            require(json.loads(p.read_text())['tolerance_decision']['gate_passed'],'Re=200 expanded before Re=100 gate passed')
        reports.append({'reynolds':protocol['reynolds'],'cases':len(rows),'valid':sum(r['valid'] for r in rows),
                        'decision':analysis['tolerance_decision']})
    resolved=root/'re100-resolved'
    if resolved.exists():
        from studies.cfd_study_continuation import verify_continuation
        from studies.cfd_step_sensitivity import analyze
        protocol=json.loads((resolved/'protocol.json').read_text())
        original=json.loads((root/'re100/protocol.json').read_text())
        require(protocol['initial_study']==str(root/'re100') and protocol['initial_protocol_sha256']==sha(root/'re100/protocol.json'),'Resolved study origin drift')
        require(protocol['case_ids']==original['case_ids'] and protocol['configs']==original['configs'],'Resolved matrix drift')
        continued=[]
        for cid in protocol['case_ids']:
            origin=protocol['case_origins'][cid];work=(resolved/cid).resolve()
            require(str(work)==origin['directory'] and sha(work/'result.json')==origin['result_sha256'],'Resolved source drift')
            row=json.loads((work/'result.json').read_text())
            if work!=root/'re100'/cid:
                verify_continuation(work,row);continued.append(cid);total_files+=row['evidence']['file_count']
            require(row['valid'] and row['status']=='complete','Resolved case is not converged')
        saved=json.loads((resolved/'analysis.json').read_text())
        # Reproduce the entire derived decision without modifying the delivered report.
        with tempfile.TemporaryDirectory() as tmp:
            temp=Path(tmp);shutil.copyfile(resolved/'protocol.json',temp/'protocol.json')
            for cid in protocol['case_ids']:(temp/cid).symlink_to((resolved/cid).resolve(),target_is_directory=True)
            with contextlib.redirect_stdout(io.StringIO()):fresh=analyze(temp)
        require(saved==fresh,'Resolved analysis cannot be reproduced')
        reports.append({'reynolds':100,'resolved':True,'cases':saved['case_count'],'valid':saved['valid_count'],
                        'continued_cases':continued,'decision':saved['tolerance_decision']})
    geometry=verify_common_domain(root) if (root/'geometry-check.json').exists() else None
    result={'verified':True,'prior_files_unchanged':len(prior),'native_files_verified':total_files,'common_domain_geometry_verified':geometry,
            'new_model_calls':0,'studies':reports}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result


if __name__=='__main__':verify(sys.argv[1])
