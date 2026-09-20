"""New identity over immutable Re=200 fields; no native solver execution."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from studies.cfd_primary_recirculation import flux_streamfunction,primary_region,match_root
from studies.cfd_fourth_grid import field_dictionary,native_qoi,inlet_check,wall_check,POLICY
from studies.cfd_wall_gradient_diagnostic import wall_gradient
from studies.cfd_step_sensitivity import sha,save,DOMAINS
from studies.analyze_cfd_fourth_grid import decide,geometric_inlet
from runners.solvers.backward_step import mesh_data
from runners.solvers.foam_text import field_values,dictionary

SOURCES=['studies/cfd_primary_recirculation.py','studies/reprocess_cfd_primary.py',
         'docs/specs/cfd-primary-recirculation-v2.md','tests/test_cfd_primary_recirculation.py',
         'studies/render_cfd_primary.py']


def check_manifest(source):
    manifest=json.loads((source/'delivery-manifest.json').read_text())
    for name,digest in manifest['files'].items():
        if sha(ROOT/name)!=digest:raise ValueError('frozen artifact drift: '+name)
    return len(manifest['files'])


def geometry(mesh):
    """Build a complete downstream rectangular face/cell map from actual points."""
    points=np.asarray(mesh['points']);faces=np.asarray(mesh['faces']);p=points[faces]
    lo=p.min(axis=1);hi=p.max(axis=1);span=hi-lo
    normals=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0])
    x=np.unique(points[points[:,0]>=-1e-12,0])/.01
    y=np.unique(points[:,1])/.01
    nx=len(x);ny=len(y)
    if abs(x[0])+abs(y[0])+abs(y[-1]-2)>1e-9:raise ValueError('unsupported downstream bounds')
    xf=np.where((span[:,0]<1e-12)&(lo[:,0]>=-1e-12)&(span[:,1]>0)&(span[:,2]>0))[0]
    yf=np.where((span[:,1]<1e-12)&(lo[:,0]>=-1e-12)&(span[:,0]>0)&(span[:,2]>0))[0]
    def mapped(ids,vertical):
        ix=np.searchsorted(x,lo[ids,0]/.01)
        iy=np.searchsorted(y,lo[ids,1]/.01)
        shape=(ny-1,nx) if vertical else (ny,nx-1)
        if len(ids)!=np.prod(shape) or len(set(zip(iy,ix)))!=len(ids):
            raise ValueError('downstream face grid missing/duplicate')
        # Every face must be exactly one adjacent strip, not spanning grid nodes.
        if vertical:
            if not np.allclose(hi[ids,1]/.01,y[iy+1],atol=1e-9,rtol=0):raise ValueError('nonrectangular y strip')
        elif not np.allclose(hi[ids,0]/.01,x[ix+1],atol=1e-9,rtol=0):raise ValueError('nonrectangular x strip')
        axis=0 if vertical else 1
        factor=np.sign(normals[ids,axis])/span[ids,2]/.01
        return ids,iy,ix,shape,factor
    centres=np.asarray(mesh['centres']);owner=np.asarray(mesh['owner'])
    front=np.where((np.abs(centres[:,2])<1e-12)&(centres[:,0]>0))[0]
    xc=(x[:-1]+x[1:])/2;yc=(y[:-1]+y[1:])/2
    ix=np.searchsorted(x,centres[front,0]/.01)-1;iy=np.searchsorted(y,centres[front,1]/.01)-1
    if len(front)!=(nx-1)*(ny-1) or len(set(zip(iy,ix)))!=len(front):raise ValueError('cell grid missing/duplicate')
    if not np.allclose(centres[front,0]/.01,xc[ix],rtol=0,atol=1e-8) or not np.allclose(centres[front,1]/.01,yc[iy],rtol=0,atol=1e-8):raise ValueError('cell coordinates not rectangular centres')
    return {'x':x,'y':y,'xf':mapped(xf,True),'yf':mapped(yf,False),
            'cell_ids':owner[front],'cell_y':iy,'cell_x':ix,'xc':xc,'yc':yc}


def read_flux(case,mesh,plan,iteration):
    data=field_dictionary(case/str(iteration)/'phi')
    if data['dimensions']!=[['0','3','-1','0','0','0','0']]:raise ValueError('phi units')
    phi=np.zeros(len(mesh['faces']));n=len(mesh['neighbour'])
    phi[:n]=field_values(data['internalField'],n)
    for patch,ids in mesh['ranges'].items():
        bc=data['boundaryField'][patch]
        if bc.get('type')==['empty']:continue
        phi[ids]=field_values(bc['value'],len(ids))
    fields=[]
    for key in ('xf','yf'):
        ids,iy,ix,shape,factor=plan[key];field=np.full(shape,np.nan)
        field[iy,ix]=phi[ids]*factor;fields.append(field)
    return flux_streamfunction(plan['x'],plan['y'],*fields)


def read_velocity(case,mesh,plan,iteration):
    data=field_dictionary(case/str(iteration)/'U')
    if data['dimensions']!=[['0','1','-1','0','0','0','0']]:raise ValueError('velocity units')
    vel=np.asarray(field_values(data['internalField'],mesh['cells'],True))
    grid=np.full((len(plan['yc']),len(plan['xc']),3),np.nan)
    grid[plan['cell_y'],plan['cell_x']]=vel[plan['cell_ids']]
    if not np.isfinite(grid).all():raise ValueError('missing cell velocity')
    if abs(grid[:,:,2]).max()>1e-12:raise ValueError('not two-dimensional velocity')
    # Integrate actual nonuniform cell-centre samples, anchored at no-slip wall.
    yy=np.r_[0,plan['yc']];uu=np.vstack((np.zeros(len(plan['xc'])),grid[:,:,0]))
    psi=np.cumsum((uu[1:]+uu[:-1])*.5*np.diff(yy)[:,None],axis=0)
    nu=float(dictionary(case/'constant/transportProperties')['nu'][-1])
    y1,y2=plan['yc'][:2]*.01
    first=nu*grid[0,:,0]/y1
    quadratic=[nu*wall_gradient(y1,y2,u1,u2) for u1,u2 in zip(grid[0,:,0],grid[1,:,0])]
    return grid,psi,list(zip(plan['xc'].tolist(),first.tolist())),list(zip(plan['xc'].tolist(),quadratic))


def one_time(case,mesh,plan,iteration):
    psi,flux=read_flux(case,mesh,plan,iteration)
    labels,region=primary_region(plan['x'],plan['y'],psi)
    native=native_qoi(case,mesh,iteration);association=match_root(native['curve'],plan['x'],labels,region['label'])
    velocity,psi_u,first,quad=read_velocity(case,mesh,plan,iteration)
    labels_u,region_u=primary_region(plan['xc'],plan['yc'],psi_u)
    native_u=match_root(native['curve'],plan['xc'],labels_u,region_u['label'])
    first_u=match_root(first,plan['xc'],labels_u,region_u['label'])
    quad_u=match_root(quad,plan['xc'],labels_u,region_u['label'])
    if native_u['selected']['bracket_indices']!=association['selected']['bracket_indices']:
        raise ValueError('phi and U disagree on primary wall interval')
    q=association['selected']['x_h'];q1=first_u['selected']['x_h'];q2=quad_u['selected']['x_h']
    data={'iteration':iteration,'x_over_h':q,'frozen_first_upcrossing_x_h':native['x_over_h'],
          'flux':flux,'region':region,'velocity_region':region_u,'native_association':association,
          'first_layer_association':first_u,'quadratic_association':quad_u,
          'first_layer_x_h':q1,'quadratic_x_h':q2,'near_wall_gap':abs(q2-q)/q,
          'phi_U_same_wall_interval':True,'native_curve':native['curve']}
    visual={'x':plan['x'],'y':plan['y'],'psi':psi,'xc':plan['xc'],'yc':plan['yc'],
            'U':velocity[:,:,0],'V':velocity[:,:,1],'psi_U':psi_u,'labels':labels}
    return data,visual


def reprocess_case(work):
    old=json.loads((work/'result.json').read_text());case=work/'case'
    if old['config']['reynolds']!=200 or not old['valid']:raise ValueError('not a valid Re=200 saved case')
    times=sorted(int(p.name) for p in case.iterdir() if p.name.isdecimal() and int(p.name)>0 and (p/'wallShearStress').is_file())
    if len(times)<2 or times[-1]!=old['qoi']['iteration'] or times[-2]!=old['previous_iteration']:
        raise ValueError('last two saved times disagree with native result')
    names=['case/constant/polyMesh/'+s for s in ('points','faces','owner','neighbour','boundary')]
    names+=['case/constant/'+s for s in ('transportProperties','turbulenceProperties')]
    names+=[f'case/{t}/{f}' for t in times[-2:] for f in ('U','phi','wallShearStress')]
    evidence=json.loads((work/'evidence.json').read_text())['files'];digests={}
    for name in names:
        p=work/name
        if p.is_symlink() or not p.is_file() or name not in evidence or sha(p)!=evidence[name]['sha256']:
            raise ValueError('consumed native evidence drift: '+name)
        digests[name]=sha(p)
    mesh=mesh_data(case);plan=geometry(mesh);snapshots=[];visual=None
    for t in times[-2:]:
        data,visual=one_time(case,mesh,plan,t);snapshots.append(data)
    a,b=snapshots
    if a['native_association']['selected']['bracket_indices']!=b['native_association']['selected']['bracket_indices']:
        raise ValueError('primary wall interval changes between saved times')
    change=abs(a['x_over_h']-b['x_over_h'])/b['x_over_h']
    inlet=inlet_check(case,mesh,times[-1]);geom_inlet=geometric_inlet(case,mesh,times[-1])
    wall=wall_check(case,mesh,times[-1]);wall.update(first_cell_x_over_h=b['first_layer_x_h'],quadratic_x_over_h=b['quadratic_x_h'],relative_native_gap=b['near_wall_gap'])
    checks={'identity_both_times':True,'qoi_stable':change<=POLICY['qoi_change_max'],
            'inlet_reproduced':inlet==old['inlet'],'wall_boundary_passed':wall['passed']}
    row={'id':old['id'],'config':old['config'],'valid':all(checks.values()),'checks':checks,
         'qoi':{'x_over_h':b['x_over_h'],'iteration':times[-1]},'snapshots':snapshots,
         'relative_change':change,'inlet':inlet,'geometric_inlet':geom_inlet,'wall':wall,
         'old_x_over_h':old['qoi']['x_over_h'],'old_near_wall_gap':old['wall']['relative_native_gap'],
         'evidence_sha256':sha(work/'evidence.json'),'result_sha256':sha(work/'result.json'),
         'consumed_file_hashes':digests}
    return row,visual


def provenance(source,out):
    freeze=json.loads((out/'protocol-freeze.json').read_text())
    if freeze['spec_sha256']!=sha(ROOT/SOURCES[2]) or freeze['old_delivery_sha256']!=sha(source/'delivery-manifest.json') or freeze['old_analysis_sha256']!=sha(source/'analysis.json'):
        raise ValueError('protocol or legacy identity drift')
    receipt=json.loads((out/'legacy-verification-receipt.json').read_text())
    if receipt['exit_code']!=0 or receipt['log_sha256']!=sha(out/'legacy-native-verification.log') or receipt['old_analysis_sha256']!=freeze['old_analysis_sha256']:
        raise ValueError('legacy verification not completed or receipt drift')
    expected={'protocol_freeze_sha256':sha(out/'protocol-freeze.json'),
              'legacy_verification_receipt_sha256':sha(out/'legacy-verification-receipt.json'),
              'source_hashes':{name:sha(ROOT/name) for name in SOURCES}}
    path=out/'identity.json'
    if path.exists():
        if json.loads(path.read_text())!=expected:raise ValueError('new postprocessor identity drift; use a new output identity')
    else:save(path,expected)
    return expected


def analyze(source,out,verify=False):
    if verify and not (out/'identity.json').is_file():raise ValueError('missing saved identity')
    identity=provenance(source,out);unchanged=check_manifest(source)
    old=json.loads((source/'analysis.json').read_text());rows=[];feedback=[]
    for u,d in DOMAINS:
        for scale in (1,2,4,8):
            cid=f're200-u{u}-d{d}-g{scale}'
            try:
                row,visual=reprocess_case(source/cid)
                if not verify:
                    save(out/(cid+'.json'),row)
                    np.savez_compressed(out/(cid+'.npz'),**visual)
                elif json.loads((out/(cid+'.json')).read_text())!=json.loads(json.dumps(row)):
                    raise ValueError('saved case reprocessing differs')
                rows.append(row)
                print(json.dumps({'case':cid,'x_h':row['qoi']['x_over_h'],'wall_gap':row['wall']['relative_native_gap']}),flush=True)
            except (ValueError,OSError,KeyError,IndexError) as error:
                if verify:raise
                feedback.append({'case':cid,'issue':str(error),'action':'补齐原生材料或澄清区域归属，保留失败，不扩展。'})
                print(json.dumps(feedback[-1],ensure_ascii=False),flush=True)
    parent=Path(old['parent_verified']['path'])
    bridges=[json.loads((parent/f'bridge-u5-d{d}/result.json').read_text()) for d in (30,60)]
    compact=[{k:v for k,v in r.items() if k not in ('snapshots','consumed_file_hashes')} for r in rows]
    decision=decide(compact,bridges,200)
    if feedback:
        decision.update(gate_passed=False,screening_tolerance_candidate=None)
        decision['failed_gates'].append('primary identity / material feedback')
    decision.update(identity='comacbench.cfd-primary-recirculation.v2',identity_sha256=sha(out/'identity.json'),
                    old_analysis_sha256=sha(source/'analysis.json'),old_gate_passed=old['gate_passed'],
                    old_files_unchanged=unchanged,feedback=feedback,native_solver_calls=0,model_calls=0,
                    field_snapshots_verified=len(rows)*2,
                    next_condition_authorized_for_execution=False,
                    expansion_decision='ready_for_next_condition_planning' if decision['gate_passed'] else 'hold',
                    source_path=str(source.relative_to(ROOT)),
                    parent_gate_verified=True)
    # v1's expanded_re200 field is inappropriate for a read-only reprocessing run.
    decision['expanded_re200']=False
    check_manifest(source)
    if verify:
        if json.loads((out/'analysis.json').read_text())!=json.loads(json.dumps(decision)):raise ValueError('saved decision differs')
    else:save(out/'analysis.json',decision)
    print(json.dumps({'gate_passed':decision['gate_passed'],'failed_gates':decision['failed_gates'],'cases':len(rows),'snapshots':len(rows)*2}),flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['run','verify']);p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.command=='run' and (a.out/'analysis.json').exists():raise ValueError('analysis exists; use verify or a new identity')
    analyze(a.source.resolve(),a.out.resolve(),a.command=='verify')


if __name__=='__main__':main()
