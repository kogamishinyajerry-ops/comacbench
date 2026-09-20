"""Re=300 v2 reduction; preserves frozen solver and primary recirculation identity."""
import numpy as np
from studies.cfd_re300 import config_for,write_case,verify_phi,REFERENCE,decide as frozen_decide
from studies.cfd_fourth_grid import field_dictionary,inlet_check,wall_check,POLICY
from studies.cfd_step_sensitivity import inspect_mesh
from studies.reprocess_cfd_primary import geometry
from studies.cfd_wall_branch import one_time
from studies.analyze_cfd_fourth_grid import geometric_inlet
from studies.cfd_mpi_reconstruction import verify_reconstruction
from runners.solvers.backward_step import residuals
from runners.solvers.foam_text import field_values


def reduce(work,config,write_visual=False,historical=False):
    if config['reynolds'] not in (200,300):raise ValueError('unsupported replay Reynolds number')
    reference=4.982 if config['reynolds']==200 else REFERENCE
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
                if (not historical and available!=times[-2:]) or not set(times[-2:]).issubset(available):raise ValueError('MPI time pair differs')
            reconstruction[str(t)]=verify_reconstruction(case,t,config['expected_cells'])
            reconstruction[str(t)]['phi']=verify_phi(case,t)
        snap,visual=one_time(case,mesh,plan,t);snapshots.append(snap)
    before,last=snapshots
    branch_keys=('native_branch_indices','diagnostic_branch_indices','overlap_indices')
    branch_stable=all(before['quadratic_association'][k]==last['quadratic_association'][k] for k in branch_keys)
    change=abs(last['x_over_h']-before['x_over_h'])/last['x_over_h']
    if write_visual:np.savez_compressed(work/'visual.npz',**visual)
    inlet=inlet_check(case,mesh,it);geometric=geometric_inlet(case,mesh,it);wall=wall_check(case,mesh,it)
    wall.update(first_cell_x_over_h=last['first_layer_x_h'],quadratic_x_over_h=last['quadratic_x_h'],relative_native_gap=last['near_wall_gap'])
    data=field_dictionary(case/str(it)/'phi');flux={p:sum(field_values(data['boundaryField'][p]['value'],len(ids))) for p,ids in mesh['ranges'].items() if p!='frontAndBack'}
    imbalance=abs(sum(flux.values()))/abs(flux['inlet']);leak=(abs(flux['lowerWall'])+abs(flux['upperWall']))/abs(flux['inlet'])
    checks={'native_convergence':f'SIMPLE solution converged in {it} iterations' in log and '\nEnd\n' in log,
            'strict_residuals':final['p']<=POLICY['p_residual_max'] and max(final['Ux'],final['Uy'])<=POLICY['U_residual_max'],
            'primary_identity_stable':before['native_association']['selected']['bracket_indices']==last['native_association']['selected']['bracket_indices'],
            'diagnostic_branch_stable':branch_stable,'qoi_stable':change<=POLICY['qoi_change_max'],'mass_conserved':imbalance<=POLICY['mass_imbalance_max'] and leak<1e-8,
            'inlet_verified':inlet['passed'],'wall_contract':wall['passed'],'mpi_log':not parallel or ('nProcs : 4' in log and '\nEnd\n' in (work/'log.reconstructPar').read_text())}
    return {'valid':all(checks.values()),'checks':checks,'qoi':{'x_over_h':last['x_over_h'],'iteration':it},
            'previous_iteration':times[-2],'previous_qoi':before['x_over_h'],'relative_change':change,
            'snapshots':snapshots,'mesh':info,'convergence':{'iteration':it,'final':final},
            'mass':{'relative_imbalance':imbalance,'wall_leak':leak,'flux':flux},'inlet':inlet,'geometric_inlet':geometric,
            'wall':wall,'reconstruction':reconstruction,'reference':reference,'relative_error':abs(last['x_over_h']/reference-1)}


def decide(rows,retention_passed):
    result=frozen_decide(rows,retention_passed)
    result['identity']='comacbench.cfd-re300.v2'
    result['wall_diagnostic']='mutual_negative_branch_overlap/v1'
    return result
