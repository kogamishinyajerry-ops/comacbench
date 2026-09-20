"""Independent evidence verification and four-grid decision; no native execution."""
import argparse
import json
import math
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from studies.cfd_step_sensitivity import sha,save,grid_convergence,DOMAINS,REFERENCES,verify_case
from studies.cfd_fourth_grid import POLICY,reduce,write_case,field_dictionary,expansion_allowed,inlet_check,wall_check
from runners.solvers.backward_step import mesh_data
from runners.solvers.foam_text import field_values
from studies.cfd_mpi_reconstruction import verify_reconstruction


def verify_origin(work,row,root):
    if row.get('policy')==POLICY:
        fresh,_=verify_new(work,root)
        if not fresh['valid'] or fresh['status']!='complete':raise ValueError('new-protocol initialization source is invalid')
    else:
        verify_case(work,row)


def verify_new(work,root):
    row=json.loads((work/'result.json').read_text());protocol=json.loads((root/'protocol.json').read_text())
    runner_source=protocol.get('runner_source','studies/cfd_fourth_grid.py')
    if row['source_sha256']!=protocol['source_hashes'][runner_source]:raise ValueError('run source identity drift')
    if row['policy']!=POLICY:raise ValueError('policy drift')
    manifest=work/'evidence.json'
    if sha(manifest)!=row['evidence']['manifest_sha256']:raise ValueError('manifest drift')
    files=json.loads(manifest.read_text())['files']
    for name,item in files.items():
        path=Path(name)
        if path.is_absolute() or '..' in path.parts or sha(work/path)!=item['sha256']:raise ValueError('native evidence drift: '+name)
    origin=Path(row['origin']['path']);old=json.loads((origin/'result.json').read_text())
    if sha(origin/'result.json')!=row['origin']['result_sha256'] or sha(origin/'evidence.json')!=row['origin']['evidence_sha256']:raise ValueError('origin drift')
    verify_origin(origin,old,root)
    # Regenerate templates; verify both untouched settings and restored boundaries.
    with tempfile.TemporaryDirectory() as tmp:
        generated=Path(tmp)/'case';c=row['config']
        generator=write_case
        if runner_source=='studies/cfd_fourth_grid_fast.py':
            from studies.cfd_fourth_grid_fast import write_case as generator
        elif runner_source=='studies/cfd_fourth_grid_balanced.py':
            from studies.cfd_fourth_grid_balanced import write_case as generator
        elif runner_source!='studies/cfd_fourth_grid.py':raise ValueError('unknown execution version')
        generator(generated,c['scale'],c['upstream_h'],c['downstream_h'],c['reynolds'])
        for p in generated.rglob('*'):
            if not p.is_file():continue
            rel=p.relative_to(generated)
            if sha(p)!=sha(work/'generated-inputs'/rel):raise ValueError('generated inputs drift: '+str(rel))
            if str(rel) not in ('0/U','0/p'):
                expected_bytes=p.read_bytes()
                if row.get('continuation') and str(rel)=='system/controlDict':
                    expected_bytes=expected_bytes.replace(b'startFrom       startTime',b'startFrom       latestTime')
                if expected_bytes!=(work/'case'/rel).read_bytes():raise ValueError('solver settings drift: '+str(rel))
        for field in ('U','p'):
            p=work/'case/0'/field
            if sha(p)!=sha(work/'mapped-initial-fields'/field):raise ValueError('mapped initial state drift')
            actual=field_dictionary(p)['boundaryField'];expected=field_dictionary(generated/'0'/field)['boundaryField']
            if row['kind']=='inlet-pair' and field=='U':
                # Face-average formula checked independently with native geometry below.
                actual=dict(actual);expected=dict(expected);actual.pop('inlet');expected.pop('inlet')
            if actual!=expected:raise ValueError('mapping changed boundary condition')
    if row.get('continuation'):
        cont=row['continuation'];source=Path(cont['source'])
        if cont['source_sha256']!=protocol['source_hashes']['studies/continue_cfd_fourth_grid.py']:raise ValueError('continuation source version')
        if sha(source/'result.json')!=cont['source_result_sha256'] or sha(source/'evidence.json')!=cont['source_evidence_sha256']:raise ValueError('continuation origin drift')
        for name,item in json.loads((source/'evidence.json').read_text())['files'].items():
            if sha(source/name)!=item['sha256']:raise ValueError('continuation origin artifact drift')
        for field,digest in cont['restart_field_hashes'].items():
            if sha(work/'restart-inputs'/field)!=digest or sha(source/'case'/str(cont['checkpoint'])/field)!=digest:raise ValueError('restart snapshot drift')
            if field!='wallShearStress' and sha(work/'case'/str(cont['checkpoint'])/field)!=digest:raise ValueError('restart field overwritten')
        if sha(work/'log.simpleFoam.initial')!=sha(source/'log.simpleFoam'):raise ValueError('initial raw log drift')
        if sha(work/'case/constant/polyMesh/points')!=sha(source/'case/constant/polyMesh/points'):raise ValueError('restart mesh drift')
    if row.get('parallel'):
        parallel=row['parallel']
        allowed={protocol['source_hashes'][name] for name in ('studies/cfd_mpi_bridge.py','studies/cfd_mpi_fourth.py','studies/cfd_mpi_re200.py') if name in protocol['source_hashes']}
        if parallel['source_sha256'] not in allowed or parallel['ranks']!=4:raise ValueError('MPI execution identity')
        if parallel.get('execution_source_sha256') and parallel['execution_source_sha256']!=protocol['source_hashes']['studies/cfd_mpi_fourth.py']:raise ValueError('MPI native execution source identity')
        if parallel.get('decompose_source_sha256') and parallel['decompose_source_sha256']!=protocol['source_hashes']['studies/cfd_mpi_bridge.py']:raise ValueError('MPI decomposition source identity')
        if parallel.get('replay_source') and sha(Path(parallel['replay_source'])/'result.json')!=parallel['replay_result_sha256']:raise ValueError('MPI bridge replay identity')
        from studies.cfd_mpi_bridge import DECOMPOSE
        if (work/'case/system/decomposeParDict').read_text()!=DECOMPOSE or sha(work/'case/system/decomposeParDict')!=parallel['decompose_dict_sha256']:raise ValueError('MPI decomposition contract')
        if parallel.get('restart'):
            restart=parallel['restart'];source=Path(restart['source'])
            if sha(source/'result.json')!=restart['source_result_sha256'] or sha(source/'evidence.json')!=restart['source_evidence_sha256']:raise ValueError('MPI restart source identity')
            verify_case(source,json.loads((source/'result.json').read_text()))
            for field,digest in restart['fields'].items():
                if sha(work/'parallel-restart-inputs'/field)!=digest or sha(source/'case'/str(restart['checkpoint'])/field)!=digest:raise ValueError('MPI checkpoint snapshot')
                if field!='wallShearStress' and sha(work/'case'/str(restart['checkpoint'])/field)!=digest:raise ValueError('MPI checkpoint changed')
            if sha(work/'log.simpleFoam.serial')!=sha(source/'log.simpleFoam'):raise ValueError('serial log changed')
            for field in ('points','faces','owner','neighbour','boundary'):
                if sha(work/'case/constant/polyMesh'/field)!=sha(source/'case/constant/polyMesh'/field):raise ValueError('MPI restart mesh changed')
        if row['status']=='complete':
            if 'nProcs : 4' not in (work/'log.simpleFoam').read_text() or '\nEnd\n' not in (work/'log.reconstructPar').read_text():raise ValueError('native MPI/reconstruction proof missing')
            times=[row['previous_iteration'],row['qoi']['iteration']]
            if parallel.get('reconstructed_times',times)!=times:raise ValueError('MPI reconstructed times differ from stability pair')
            for rank in range(parallel['ranks']):
                available=sorted(int(p.name) for p in (work/f'case/processor{rank}').iterdir() if p.name.isdecimal() and int(p.name)>0 and all((p/f).is_file() for f in ('U','p','phi','wallShearStress')))
                if available[-2:]!=times:raise ValueError('MPI processor stability fields incomplete or inconsistent')
            row['reconstruction_check']={str(it):verify_reconstruction(work/'case',it,row['config']['expected_cells']) for it in times}
    if row['status']=='complete':
        fresh=json.loads(json.dumps(reduce(work,row['config'])))
        for key in fresh:
            if fresh[key]!=row[key]:raise ValueError('reduction differs: '+key)
        if row['kind']=='bridge':
            delta=abs(row['qoi']['x_over_h']-old['qoi']['x_over_h'])/old['qoi']['x_over_h']
            if row['bridge_relative_change']!=delta or row['bridge_passed']!=(row['valid'] and delta<=POLICY['bridge_qoi_change_max']):raise ValueError('bridge decision differs')
    return row,len(files)


def geometric_inlet(case,mesh,iteration,face_average=False):
    """Polygon vector area and two-point Gauss quadrature, separate from writer."""
    import math
    ids=mesh['ranges']['inlet'];data=field_dictionary(case/str(iteration)/'U')
    velocity=field_values(data['boundaryField']['inlet']['value'],len(ids),True)
    phi=field_values(field_dictionary(case/str(iteration)/'phi')['boundaryField']['inlet']['value'],len(ids))
    area=quadrature=discrete=0.;worst=0.;normal_error=0.;phi_error=0.
    for face,u,f in zip(ids,velocity,phi):
        points=[mesh['points'][p] for p in mesh['faces'][face]];sf=[0.,0.,0.]
        for a,b in zip(points,points[1:]+points[:1]):
            sf[0]+=(a[1]*b[2]-a[2]*b[1])/2
            sf[1]+=(a[2]*b[0]-a[0]*b[2])/2
            sf[2]+=(a[0]*b[1]-a[1]*b[0])/2
        mag=math.sqrt(sum(v*v for v in sf));normal_error=max(normal_error,abs(sf[0]/mag+1),abs(sf[1]/mag),abs(sf[2]/mag))
        lo=min(p[1] for p in points);hi=max(p[1] for p in points);mid=(lo+hi)/2;half=(hi-lo)/2
        def profile(y):
            z=(y-.01)/.01
            return 6*z*(1-z)
        average=(profile(mid-half/math.sqrt(3))+profile(mid+half/math.sqrt(3)))/2
        expected=average if face_average else profile(mid)
        worst=max(worst,abs(u[0]-expected));q=-sum(a*b for a,b in zip(u,sf))
        phi_error=max(phi_error,abs(q+f)/max(abs(q),1e-30));area+=mag;quadrature+=average*mag;discrete+=q
    passed=normal_error<=1e-10 and abs(area/1e-4-1)<=1e-10 and abs(quadrature/1e-4-1)<=1e-10 and worst<=1e-9 and phi_error<=1e-8
    if not passed:raise ValueError('independent polygon/Gauss inlet check failed')
    return {'passed':passed,'polygon_area_m2':area,'gauss_integral_m3_s':quadrature,
            'velocity_dot_area_flux_m3_s':discrete,'max_outward_normal_error':normal_error,
            'max_profile_error_m_s':worst,'max_phi_relative_error':phi_error,'face_average':face_average}


def common_geometry(root,reynolds=100):
    baseline=None;checks=[]
    for up,down in DOMAINS:
        work=root/f're{reynolds}-u{up}-d{down}-g8';mesh=mesh_data(work/'case')
        xy=sorted((c[0],c[1]) for c in mesh['centres'] if abs(c[2])<1e-12 and 0<c[0]<.3)
        if len(xy)!=5600*64:raise ValueError('common-domain cell count')
        if baseline is None:baseline=xy
        delta=max(abs(a-b) for p,q in zip(xy,baseline) for a,b in zip(p,q))
        if delta>1e-10:raise ValueError('common-domain geometry changed')
        checks.append({'id':work.name,'common_cells':len(xy),'max_coordinate_delta_m':delta,
                       'points_sha256':sha(work/'case/constant/polyMesh/points'),
                       'faces_sha256':sha(work/'case/constant/polyMesh/faces'),
                       'geometric_inlet':geometric_inlet(work/'case',mesh,json.loads((work/'result.json').read_text())['qoi']['iteration'])})
        del mesh
    return {'passed':True,'rows':checks}


def decide(rows,bridges,reynolds=100):
    """Derive all decision fields from rows, never trust a stored passed flag."""
    groups=[]
    for u,d in DOMAINS:
        group=sorted([r for r in rows if (r['config']['upstream_h'],r['config']['downstream_h'])==(u,d)],key=lambda r:r['config']['scale'])
        vals=[r['qoi']['x_over_h'] for r in group if r.get('qoi')]
        groups.append({'upstream_h':u,'downstream_h':d,'old_gci':grid_convergence(vals[:3]),'gci':grid_convergence(vals[-3:]) if len(vals)==4 else {'applicable':False,'reason':'missing fourth result'}})
    fine=[r for r in rows if r['config']['scale']==8 and r.get('qoi')]
    domain=(max(r['qoi']['x_over_h'] for r in fine)-min(r['qoi']['x_over_h'] for r in fine))/REFERENCES[reynolds] if len(fine)==4 else None
    diagnostics=len(fine)==4 and all(r.get('inlet',{}).get('passed') and abs(r['inlet']['relative_bias'])<=POLICY['fine_inlet_bias_max'] and r.get('wall',{}).get('passed') and r['wall']['relative_native_gap']<=POLICY['fine_wall_gap_max'] and r['wall']['relative_native_gap']<next((p['wall']['relative_native_gap'] for p in rows if p['config']['scale']==4 and p['config']['upstream_h']==r['config']['upstream_h'] and p['config']['downstream_h']==r['config']['downstream_h']),-1) for r in fine)
    result={'reynolds':reynolds,'rows':rows,'groups':groups,'fine_domain_effect':domain,'diagnostics_passed':diagnostics,
            'bridges_passed':len(bridges)==2 and all(r.get('bridge_passed') for r in bridges),'policy':POLICY,
            'current_benchmark_tolerance':.1,'calibrated_tolerance':None,'expanded_re200':False}
    expected={(u,d,k) for u,d in DOMAINS for k in (1,2,4,8)}
    complete=len(rows)==16 and {(r['config']['upstream_h'],r['config']['downstream_h'],r['config']['scale']) for r in rows}==expected and all(r['valid'] and r['config'].get('reynolds')==reynolds for r in rows)
    result['gate_passed']=complete and all(g['gci']['applicable'] and g['gci']['fine_gci']<=POLICY['fine_gci_max'] for g in groups) and domain is not None and domain<=POLICY['fine_domain_effect_max'] and diagnostics and result['bridges_passed']
    result['screening_tolerance_candidate']=None
    if result['gate_passed']:
        ref=REFERENCES[reynolds]
        terms={'observed_error':max(abs(r['qoi']['x_over_h']-ref)/ref for r in rows),
               'fine_gci':max(g['gci']['fine_gci']*next(r['qoi']['x_over_h'] for r in fine if r['config']['upstream_h']==g['upstream_h'] and r['config']['downstream_h']==g['downstream_h'])/ref for g in groups),
               'domain':domain,'iteration':max(r.get('relative_change',0)*r['qoi']['x_over_h']/ref for r in rows),'reference_rounding':.0005/ref}
        result['screening_tolerance_candidate']={'relative_band':math.ceil(sum(terms.values())/.005)*.005,'terms':terms,
                                                'policy':'Prior v1 conservative screening sum rounded upward in 0.5 percentage-point steps; not a statistical confidence interval; old scores unchanged.'}
    result['failed_gates']=[]
    if not complete:result['failed_gates'].append('native validity / completeness')
    if not all(g['gci']['applicable'] and g['gci']['fine_gci']<=POLICY['fine_gci_max'] for g in groups):result['failed_gates'].append('finest-three grid GCI > 0.5% or inapplicable')
    if domain is None or domain>POLICY['fine_domain_effect_max']:result['failed_gates'].append('domain sensitivity')
    if not diagnostics:result['failed_gates'].append('inlet / wall independent checks')
    if not result['bridges_passed']:result['failed_gates'].append('linear solver bridge')
    return result


def analyze(root):
    root=Path(root).resolve();protocol=json.loads((root/'protocol.json').read_text());prior=(root/protocol['prior']).resolve();count=0
    if sha(root/'prior-artifacts.json')!=protocol['prior_manifest_sha256']:raise ValueError('prior snapshot manifest drift')
    prior_files=json.loads((root/'prior-artifacts.json').read_text())
    for name,digest in prior_files.items():
        if sha(ROOT/name)!=digest:raise ValueError('prior artifact changed: '+name)
    for name,digest in protocol['source_hashes'].items():
        if sha(root/'frozen-source'/name)!=digest or sha(ROOT/name)!=digest:raise ValueError('source snapshot drift: '+name)
    if protocol.get('parallel_source'):
        mpi=Path(protocol['mpi_bridge_directory']);verified=[]
        if sha(root/'mpi-verification.json')!=protocol['mpi_verification_sha256'] or sha(root/'mpi-speed-check.json')!=protocol['mpi_speed_check_sha256']:raise ValueError('MPI adoption record drift')
        for downstream in (30,60):
            row,n=verify_new(mpi/f'bridge-u5-d{downstream}',root)
            source=Path(row['parallel']['replay_source'])
            for field in ('points','faces','owner','neighbour','boundary'):
                if sha(mpi/f'bridge-u5-d{downstream}/case/constant/polyMesh'/field)!=sha(source/'case/constant/polyMesh'/field):raise ValueError('MPI bridge mesh changed')
            verified.append({'domain_downstream_h':downstream,'valid':row['valid'],'bridge_passed':row['bridge_passed'],'relative_change':row['bridge_relative_change'],'files':n,'mesh_identical':True,'native_ranks':4})
        if json.loads((root/'mpi-verification.json').read_text())!={'passed':all(r['bridge_passed'] for r in verified),'rows':verified}:raise ValueError('MPI bridge verification differs')
        if not all(r['bridge_passed'] for r in verified):raise ValueError('MPI bridge did not pass')
    checks=json.loads((root/'prior-independent-checks.json').read_text());checkrows={r['id']:r for r in checks['rows']};rows=[]
    for cid in json.loads((prior/'protocol.json').read_text())['case_ids']:
        work=prior/cid;row=json.loads((work/'result.json').read_text());verify_case(work,row);diag=checkrows[cid]
        if diag['result_sha256']!=sha(work/'result.json'):raise ValueError('prior diagnostic provenance')
        mesh=mesh_data(work/'case');it=row['qoi']['iteration'];inlet=inlet_check(work/'case',mesh,it);wall=wall_check(work/'case',mesh,it)
        wall['relative_native_gap']=abs(wall['quadratic_x_over_h']-row['qoi']['x_over_h'])/row['qoi']['x_over_h']
        if inlet!=diag['inlet'] or wall!=diag['wall']:raise ValueError('prior diagnostic reduction changed')
        row['geometric_inlet']=geometric_inlet(work/'case',mesh,it)
        row.update(inlet=diag['inlet'],wall=diag['wall'],artifact_path=str(work.resolve()))
        rows.append(row)
    bridges=[]
    for down in (30,60):
        row,n=verify_new(root/f'bridge-u5-d{down}',root);bridges.append(row);count+=n
    for up,down in DOMAINS:
        path=root/f're100-u{up}-d{down}-g8'
        if not (path/'result.json').exists():raise ValueError('fourth-grid result missing: '+str(path))
        row,n=verify_new(path,root);row['artifact_path']=str(path);rows.append(row);count+=n
    pair_path=root/'inlet-face-average-u5-d30-g4'
    pair,n=verify_new(pair_path,root);count+=n
    pair['geometric_inlet']=geometric_inlet(pair_path/'case',mesh_data(pair_path/'case'),pair['qoi']['iteration'],True)
    decision=decide(rows,bridges)
    decision['common_domain_geometry']=common_geometry(root)
    # A diagnostic run must be valid to close the requested independent inlet study.
    decision['inlet_pair']={k:pair[k] for k in ('valid','qoi','inlet','wall','seconds','status','geometric_inlet') if k in pair}
    if not pair['valid'] or abs(pair.get('inlet',{}).get('relative_bias',1))>1e-10:
        decision['gate_passed']=False;decision['failed_gates'].append('face-average paired diagnostic invalid')
    decision['verification']={'passed':True,'native_files':count,'prior_files_unchanged':len(prior_files),'new_model_calls':0}
    decision['provenance']={'protocol_sha256':sha(root/'protocol.json'),'analysis_source_sha256':sha(__file__),
                            'reconstruction_source_sha256':sha(ROOT/'studies/cfd_mpi_reconstruction.py'),
                            'result_hashes':{r['id']:sha(Path(r['artifact_path'])/'result.json') for r in rows}}
    # Keep report data compact; original logs and full fields remain linked.
    for r in decision['rows']:
        r.pop('identity',None);r.pop('convergence',None)
        if r.get('qoi'):r['qoi'].pop('curve',None)
    decision['inlet_pair'].get('qoi',{}).pop('curve',None)
    return decision


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['analyze','verify','check-expansion']);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    data=analyze(a.out)
    path=a.out/'analysis.json'
    if a.command=='analyze':save(path,data)
    elif json.loads(path.read_text())!=data:raise ValueError('saved analysis changed')
    print(json.dumps({'gate_passed':data['gate_passed'],'failed_gates':data['failed_gates'],'verification':data['verification']}))
    if a.command=='check-expansion' and not data['gate_passed']:sys.exit(2)

if __name__=='__main__':main()
