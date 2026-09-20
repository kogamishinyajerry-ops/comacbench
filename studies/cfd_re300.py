"""Bounded Re=300 physics, retention, field verification and decision rules."""
import math
from pathlib import Path
import re
import numpy as np
from studies.cfd_fourth_grid import write_case as old_writer,field_dictionary,inlet_check,wall_check,POLICY
from studies.cfd_step_sensitivity import DOMAINS,grid_convergence,inspect_mesh
from studies.reprocess_cfd_primary import geometry,one_time
from studies.analyze_cfd_fourth_grid import geometric_inlet
from studies.cfd_mpi_reconstruction import verify_reconstruction,signed_addresses
from runners.solvers.backward_step import residuals
from runners.solvers.foam_text import field_values,counted

REFERENCE=6.751


def config_for(scale,upstream,downstream):
    if type(scale)!=int or scale not in (1,2,4,8) or (upstream,downstream) not in DOMAINS:
        raise ValueError('unsupported Re=300 grid/domain')
    return {'scale':scale,'upstream_h':upstream,'downstream_h':downstream,'reynolds':300,
            'expected_cells':(5*upstream+2*(140+(33 if downstream==60 else 0)))*20*scale**2,
            'near_step_dx_h':.1/scale,'spanwise_layers':1,
            'grading_sections':[[10,100,1],[20,40,4]]+([[30,33,1]] if downstream==60 else [])}


def write_case(case,scale,upstream,downstream,purge=2):
    config=config_for(scale,upstream,downstream)
    if type(purge)!=int or purge not in (0,2):raise ValueError('retention must be paired control 0 or production 2')
    old_writer(case,scale,upstream,downstream,200);case=Path(case)
    p=case/'constant/transportProperties'
    text,n=re.subn(r'(nu\s+\[0 2 -1 0 0 0 0\]\s+)0\.0001;',lambda m:m[1]+format(.02/300,'.14g')+';',p.read_text())
    if n!=1:raise ValueError('frozen viscosity template changed')
    p.write_text(text)
    p=case/'system/controlDict';text,n=re.subn(r'(purgeWrite\s+)0;',lambda m:m[1]+str(purge)+';',p.read_text())
    if n!=1:raise ValueError('frozen retention template changed')
    p.write_text(text)
    return config


def verify_flux_partition(full,shards):
    seen=[0]*len(full);worst=0.
    for addresses,values in shards:
        if len(addresses)!=len(values):raise ValueError('phi partition size mismatch')
        local=set()
        for address,value in zip(addresses,values):
            if type(address)!=int or address==0 or abs(address)>len(full):raise ValueError('invalid signed phi address')
            i=abs(address)-1
            if i in local:raise ValueError('duplicate face in one rank')
            local.add(i)
            if full[i] is None:continue
            actual=value*(1 if address>0 else -1)
            if not math.isfinite(actual) or not math.isfinite(full[i]) or not math.isclose(actual,full[i],rel_tol=1e-12,abs_tol=1e-15):raise ValueError('phi differs from signed rank face')
            seen[i]+=1;worst=max(worst,abs(actual-full[i]))
            if seen[i]>2:raise ValueError('face present in more than two ranks')
    if any(v is not None and seen[i]==0 for i,v in enumerate(full)):raise ValueError('missing reconstructed phi face')
    return {'verified_faces':sum(v is not None for v in full),'shared_faces':seen.count(2),'max_absolute_error':worst}


def phi_values(case,iteration):
    base=case/'constant/polyMesh';owners=counted(base/'owner','owner');n=len(counted(base/'neighbour','neighbour'))
    boundary=counted(base/'boundary','boundary');data=field_dictionary(case/str(iteration)/'phi')
    if data['dimensions']!=[['0','3','-1','0','0','0','0']]:raise ValueError('phi dimensions')
    values=[None]*len(owners);values[:n]=field_values(data['internalField'],n)
    for patch,b in boundary.items():
        if data['boundaryField'][patch].get('type')==['empty']:continue
        start=int(b['startFace'][0]);count=int(b['nFaces'][0])
        values[start:start+count]=field_values(data['boundaryField'][patch]['value'],count)
    return values


def verify_phi(case,iteration):
    full=phi_values(case,iteration)
    def shards():
        for rank in range(4):
            root=case/f'processor{rank}';addresses=signed_addresses(root/'constant/polyMesh/faceProcAddressing')
            values=phi_values(root,iteration)
            if len(addresses)!=len(values):raise ValueError('rank phi address count')
            if any(type(a)!=int or a==0 or abs(a)>len(full) for a in addresses):raise ValueError('invalid signed phi address')
            # Empty faces have no phi; they map only to the global empty boundary.
            for a,v in zip(addresses,values):
                if v is None and full[abs(a)-1] is not None:raise ValueError('rank omitted an active phi face')
            yield addresses,[0. if v is None else v for v in values]
    return verify_flux_partition(full,shards())


def reduce(work,config,write_visual=False):
    case=work/'case';mesh,info=inspect_mesh(case,config,(work/'log.checkMesh').read_text());plan=geometry(mesh)
    log=(work/'log.simpleFoam').read_text();convergence=residuals(log);it=convergence['iteration'];final=convergence['final']
    times=sorted(int(p.name) for p in case.iterdir() if p.is_dir() and p.name.isdecimal() and int(p.name)>0 and all((p/f).is_file() for f in ('U','p','phi','wallShearStress')))
    if len(times)<2 or times[-1]!=it:raise ValueError('two complete saved fields at convergence required')
    snapshots=[];reconstruction={}
    parallel=(case/'processor0').is_dir()
    for t in times[-2:]:
        if parallel:
            for rank in range(4):
                available=sorted(int(p.name) for p in (case/f'processor{rank}').iterdir() if p.name.isdecimal() and int(p.name)>0 and all((p/f).is_file() for f in ('U','p','phi','wallShearStress')))
                if available!=times[-2:]:raise ValueError('MPI rolling time pair differs')
            reconstruction[str(t)]=verify_reconstruction(case,t,config['expected_cells'])
            reconstruction[str(t)]['phi']=verify_phi(case,t)
        snap,visual=one_time(case,mesh,plan,t);snapshots.append(snap)
    before,last=snapshots;change=abs(last['x_over_h']-before['x_over_h'])/last['x_over_h']
    if write_visual:np.savez_compressed(work/'visual.npz',**visual)
    inlet=inlet_check(case,mesh,it);geometric=geometric_inlet(case,mesh,it);wall=wall_check(case,mesh,it)
    wall.update(first_cell_x_over_h=last['first_layer_x_h'],quadratic_x_over_h=last['quadratic_x_h'],relative_native_gap=last['near_wall_gap'])
    data=field_dictionary(case/str(it)/'phi');flux={p:sum(field_values(data['boundaryField'][p]['value'],len(ids))) for p,ids in mesh['ranges'].items() if p!='frontAndBack'}
    imbalance=abs(sum(flux.values()))/abs(flux['inlet']);leak=(abs(flux['lowerWall'])+abs(flux['upperWall']))/abs(flux['inlet'])
    checks={'native_convergence':f'SIMPLE solution converged in {it} iterations' in log and '\nEnd\n' in log,
            'strict_residuals':final['p']<=POLICY['p_residual_max'] and max(final['Ux'],final['Uy'])<=POLICY['U_residual_max'],
            'primary_identity_stable':before['native_association']['selected']['bracket_indices']==last['native_association']['selected']['bracket_indices'],
            'qoi_stable':change<=POLICY['qoi_change_max'],'mass_conserved':imbalance<=POLICY['mass_imbalance_max'] and leak<1e-8,
            'inlet_verified':inlet['passed'],'wall_contract':wall['passed'],'mpi_log':not parallel or ('nProcs : 4' in log and '\nEnd\n' in (work/'log.reconstructPar').read_text())}
    return {'valid':all(checks.values()),'checks':checks,'qoi':{'x_over_h':last['x_over_h'],'iteration':it},
            'previous_iteration':times[-2],'previous_qoi':before['x_over_h'],'relative_change':change,
            'snapshots':snapshots,'mesh':info,'convergence':{'iteration':it,'final':final},
            'mass':{'relative_imbalance':imbalance,'wall_leak':leak,'flux':flux},'inlet':inlet,'geometric_inlet':geometric,
            'wall':wall,'reconstruction':reconstruction,'reference':REFERENCE,'relative_error':abs(last['x_over_h']/REFERENCE-1)}


def decide(rows,retention_passed):
    groups=[]
    for u,d in DOMAINS:
        group=sorted([r for r in rows if (r['config']['upstream_h'],r['config']['downstream_h'])==(u,d)],key=lambda r:r['config']['scale'])
        vals=[r['qoi']['x_over_h'] for r in group if r.get('valid') and r.get('qoi')]
        groups.append({'upstream_h':u,'downstream_h':d,'old_gci':grid_convergence(vals[:3]),'gci':grid_convergence(vals[-3:]) if len(vals)==4 else {'applicable':False,'reason':'need four valid grids'}})
    fine=[r for r in rows if r['config']['scale']==8 and r.get('valid') and r.get('qoi')]
    domain=(max(r['qoi']['x_over_h'] for r in fine)-min(r['qoi']['x_over_h'] for r in fine))/REFERENCE if len(fine)==4 else None
    diagnostics=len(fine)==4 and all(r['inlet']['passed'] and abs(r['inlet']['relative_bias'])<=POLICY['fine_inlet_bias_max'] and r['wall']['passed'] and r['wall']['relative_native_gap']<=POLICY['fine_wall_gap_max'] and r['wall']['relative_native_gap']<next((p['wall']['relative_native_gap'] for p in rows if p.get('wall') and p['config']['scale']==4 and p['config']['upstream_h']==r['config']['upstream_h'] and p['config']['downstream_h']==r['config']['downstream_h']),-1) for r in fine)
    expected={(u,d,s) for u,d in DOMAINS for s in (1,2,4,8)}
    complete=len(rows)==16 and {(r['config']['upstream_h'],r['config']['downstream_h'],r['config']['scale']) for r in rows}==expected and all(r.get('valid') and r['config']['reynolds']==300 for r in rows)
    gates={'native validity / completeness':complete,'retention paired fields':retention_passed,
           'finest-three GCI':all(g['gci']['applicable'] and g['gci']['fine_gci']<=POLICY['fine_gci_max'] for g in groups),
           'domain sensitivity':domain is not None and domain<=POLICY['fine_domain_effect_max'],'inlet / near-wall':diagnostics}
    result={'identity':'comacbench.cfd-re300.v1','reynolds':300,'reference':REFERENCE,'rows':rows,'groups':groups,
            'fine_domain_effect':domain,'diagnostics_passed':diagnostics,'retention_passed':retention_passed,
            'gate_passed':all(gates.values()),'failed_gates':[k for k,v in gates.items() if not v],
            'policy':POLICY,'current_benchmark_tolerance':.1,'calibrated_tolerance':None,'screening_tolerance_candidate':None,
            'expanded_re400':False}
    if result['gate_passed']:
        terms={'observed_error':max(r['relative_error'] for r in rows),
               'fine_gci':max(g['gci']['fine_gci']*next(r['qoi']['x_over_h'] for r in fine if r['config']['upstream_h']==g['upstream_h'] and r['config']['downstream_h']==g['downstream_h'])/REFERENCE for g in groups),
               'domain':domain,'iteration':max(r['relative_change']*r['qoi']['x_over_h']/REFERENCE for r in rows),'reference_rounding':.0005/REFERENCE}
        result['screening_tolerance_candidate']={'relative_band':math.ceil(sum(terms.values())/.005)*.005,'terms':terms,'policy':'prior conservative screening sum; not a confidence interval; no public scoring change'}
    return result
