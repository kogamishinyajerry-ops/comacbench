"""Reference-free mutual correspondence of sampled negative wall-shear branches."""
import numpy as np
from studies.cfd_zero_crossing_audit import crossings


def negative_branches(curve):
    branches=[];start=None
    for i,(_,value) in enumerate(curve):
        if value<0 and start is None:start=i
        if value>0 and start is not None:
            branches.append([start,i-1]);start=None
    if start is not None:branches.append([start,len(curve)-1])
    return branches


def match_diagnostic_branch(native,diagnostic,primary):
    audits=[crossings(curve) for curve in (native,diagnostic)]
    if any(a['zero_samples_x_h'] for a in audits):raise ValueError('zero samples or plateau require adjudication')
    if len(native)!=len(diagnostic) or not np.allclose([p[0] for p in native],[p[0] for p in diagnostic],atol=1e-8,rtol=0):
        raise ValueError('diagnostic and native samples are not aligned')
    selected=primary.get('selected',{})
    roots=[r for r in audits[0]['crossings'] if r['direction']=='negative_to_positive' and r['bracket_indices']==selected.get('bracket_indices')]
    if selected.get('primary_member') is not True or len(roots)!=1 or any(selected.get(k)!=v for k,v in roots[0].items()):
        raise ValueError('verified native primary root required')
    native_branches=negative_branches(native);diagnostic_branches=negative_branches(diagnostic)
    main=next(b for b in native_branches if b[1]==roots[0]['bracket_indices'][0])
    def overlaps(a,b):return max(a[0],b[0])<=min(a[1],b[1])
    candidates=[b for b in diagnostic_branches if overlaps(main,b)]
    if len(candidates)!=1:raise ValueError('primary branch has no unique diagnostic correspondence')
    matched=candidates[0]
    if [b for b in native_branches if overlaps(b,matched)]!=[main]:raise ValueError('diagnostic branch merges distinct native branches')
    if matched[1]==len(diagnostic)-1:raise ValueError('diagnostic branch remains open at outlet')
    chosen=next(r for r in audits[1]['crossings'] if r['direction']=='negative_to_positive' and r['bracket_indices'][0]==matched[1])
    up=[dict(r,primary_member=r==chosen) for r in audits[1]['crossings'] if r['direction']=='negative_to_positive']
    return {'selected':dict(chosen,primary_member=True),'all_upcrossings':up,'all_crossings':audits[1]['crossings'],
            'association_method':'mutual_negative_branch_overlap/v1','native_branch_indices':main,
            'diagnostic_branch_indices':matched,'overlap_indices':[max(main[0],matched[0]),min(main[1],matched[1])],
            'native_negative_branches':native_branches,'diagnostic_negative_branches':diagnostic_branches}


def one_time(case,mesh,plan,iteration):
    """Frozen primary and native QoI; only quadratic branch correspondence changes."""
    from studies.reprocess_cfd_primary import read_flux,read_velocity
    from studies.cfd_primary_recirculation import primary_region,match_root
    from studies.cfd_fourth_grid import native_qoi
    psi,flux=read_flux(case,mesh,plan,iteration)
    labels,region=primary_region(plan['x'],plan['y'],psi)
    native=native_qoi(case,mesh,iteration);association=match_root(native['curve'],plan['x'],labels,region['label'])
    velocity,psi_u,first,quad=read_velocity(case,mesh,plan,iteration)
    labels_u,region_u=primary_region(plan['xc'],plan['yc'],psi_u)
    native_u=match_root(native['curve'],plan['xc'],labels_u,region_u['label'])
    first_u=match_root(first,plan['xc'],labels_u,region_u['label'])
    quad_u=match_diagnostic_branch(native['curve'],quad,association)
    if native_u['selected']['bracket_indices']!=association['selected']['bracket_indices']:
        raise ValueError('phi and U disagree on primary wall interval')
    q=association['selected']['x_h'];q1=first_u['selected']['x_h'];q2=quad_u['selected']['x_h']
    data={'iteration':iteration,'x_over_h':q,'frozen_first_upcrossing_x_h':native['x_over_h'],
          'flux':flux,'region':region,'velocity_region':region_u,'native_association':association,
          'first_layer_association':first_u,'quadratic_association':quad_u,
          'first_layer_x_h':q1,'quadratic_x_h':q2,'near_wall_gap':abs(q2-q)/q,
          'phi_U_same_wall_interval':True,'native_curve':native['curve']}
    visual={'x':plan['x'],'y':plan['y'],'psi':psi,'xc':plan['xc'],'yc':plan['yc'],
            'U':velocity[:,:,0],'V':velocity[:,:,1],'psi_U':psi_u,'labels':labels,
            'quadratic_wall_shear':np.asarray(quad)}
    return data,visual
