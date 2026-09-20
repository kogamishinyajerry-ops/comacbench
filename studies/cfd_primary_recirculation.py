"""Reference-free, bounded primary-eddy identity for the rectangular BFS study."""
import numpy as np
import contourpy
from scipy.ndimage import label as connected_labels
from matplotlib.path import Path as Polygon

from studies.cfd_zero_crossing_audit import crossings


def axes(x,y):
    x=np.asarray(x,dtype=float);y=np.asarray(y,dtype=float)
    if any(a.ndim!=1 or len(a)<4 or not np.isfinite(a).all() or not (np.diff(a)>0).all() for a in (x,y)):
        raise ValueError('finite increasing rectangular coordinates required')
    if x[0]<0 or y[0]<0 or y[-1]<=1 or y[0]>=1:
        raise ValueError('downstream geometry must include the step lip y/h=1')
    return x,y


def flux_streamfunction(x,y,qx,qy):
    """Fluxes per span / (Umean*h); rows are y, columns are x."""
    x,y=axes(x,y);qx=np.asarray(qx,dtype=float);qy=np.asarray(qy,dtype=float)
    if qx.shape!=(len(y)-1,len(x)) or qy.shape!=(len(y),len(x)-1) or not np.isfinite(qx).all() or not np.isfinite(qy).all():
        raise ValueError('missing or nonfinite face flux grid')
    psi=np.vstack((np.zeros(len(x)),np.cumsum(qx,axis=0)))
    flow=float(np.mean(psi[-1]))
    if flow<=0:raise ValueError('positive downstream bulk flux required')
    defect=float(np.max(np.abs(np.diff(psi,axis=1)+qy))/flow)
    if defect>1e-6:raise ValueError('streamfunction flux paths do not close')
    return psi,{'path_defect_relative':defect,'bulk_flux_over_Uh':flow,
                'top_flux_spread_relative':float(np.ptp(psi[-1])/flow)}


def primary_region(x,y,psi):
    """Select the unique negative-psi component adjacent to the step lip."""
    x,y=axes(x,y);psi=np.asarray(psi,dtype=float)
    if psi.shape!=(len(y),len(x)) or not np.isfinite(psi).all():
        raise ValueError('invalid streamfunction grid')
    labels,count=connected_labels(psi<0)
    first=int(np.searchsorted(x,0,side='right'))
    j=int(np.searchsorted(y,1));dy=max(y[j]-y[j-1],y[min(j+1,len(y)-1)]-y[j])
    lip_rows=np.where((y>0)&(np.abs(y-1)<=2*dy+1e-12))[0]
    candidates=sorted(set(int(v) for v in labels[lip_rows,first] if v))
    if len(candidates)!=1:raise ValueError(f'primary lip component not unique: {candidates}')
    chosen=candidates[0];mask=labels==chosen
    if mask[:,-1].any() or mask[-1].any():raise ValueError('primary region open at domain boundary')
    iy,ix=np.unravel_index(np.argmin(np.where(mask,psi,np.inf)),psi.shape)
    if iy in (0,len(y)-1) or ix in (0,len(x)-1):raise ValueError('primary minimum is not interior')
    centre=(float(x[ix]),float(y[iy]));minimum=float(psi[iy,ix])
    generator=contourpy.contour_generator(x=x,y=y,z=psi,name='serial')
    contours=[]
    for fraction in (.25,.5,.75):
        enclosed=[line for line in generator.lines(fraction*minimum)
                  if len(line)>3 and np.allclose(line[0],line[-1],rtol=0,atol=1e-10)
                  and Polygon(line).contains_point(centre)]
        if len(enclosed)!=1:raise ValueError('no unique closed primary streamline around minimum')
        contours.append({'fraction':fraction,'level':fraction*minimum,'xy_h':enclosed[0].tolist()})
    components=[]
    for key in range(1,count+1):
        jj,ii=np.where(labels==key)
        components.append({'label':key,'nodes':len(ii),'x_h':[float(x[ii].min()),float(x[ii].max())],
                           'y_h':[float(y[jj].min()),float(y[jj].max())],'psi_min':float(psi[jj,ii].min()),
                           'selected':key==chosen})
    return labels,{'label':chosen,'centre_xy_h':centre,'psi_min_over_Uh':minimum,
                   'lip_column_x_h':float(x[first]),'lip_y_resolution_h':float(dy),
                   'closed_levels':[.25,.5,.75],'contours':contours,'components':components}


def match_root(curve,x,labels,primary_label):
    """Associate every upcrossing with the negative-side wall cell's region."""
    audit=crossings(curve)
    if audit['zero_samples_x_h']:raise ValueError('zero wall samples/plateau require explicit adjudication')
    x=np.asarray(x);labels=np.asarray(labels)
    if labels.ndim!=2 or labels.shape[1]!=len(x) or labels.shape[0]<2:
        raise ValueError('wall association shape mismatch')
    if not isinstance(primary_label,(int,np.integer)) or primary_label<=0 or not np.any(labels==primary_label):
        raise ValueError('positive existing primary component label required')
    xc=np.asarray([p[0] for p in curve]);nodal=abs(x[0])<1e-12
    expected=(x[:-1]+x[1:])/2 if nodal else x
    if len(expected)!=len(xc) or not np.allclose(expected,xc,rtol=0,atol=1e-8):
        raise ValueError('wall samples not aligned to flow grid')
    roots=[]
    for r in audit['crossings']:
        if r['direction']!='negative_to_positive':continue
        i=r['bracket_indices'][0]
        member=bool(primary_label in labels[1,i:i+2]) if nodal else bool(labels[0,i]==primary_label)
        roots.append(dict(r,primary_member=member))
    selected=[r for r in roots if r['primary_member']]
    if len(selected)!=1:raise ValueError(f'primary wall root not unique: {len(selected)}')
    return {'selected':selected[0],'all_upcrossings':roots,'all_crossings':audit['crossings']}
