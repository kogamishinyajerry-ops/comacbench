"""Study-only large initial-field reader; mesh and inlet tests stay unchanged."""
import re
from runners.solvers.backward_step import mesh_data
from runners.solvers.foam_text import field_values
from studies.cfd_fourth_grid import field_dictionary


def read_initial_inlet(case,count):
    return field_values(field_dictionary(case/'0/U')['boundaryField']['inlet']['value'],count,True)


def inspect_mesh(case,config,log):
    mesh=mesh_data(case)
    if mesh['cells']!=config['expected_cells'] or 'Mesh OK.' not in log or not re.search(r'Number of regions:\s+1\b',log):
        raise ValueError('native mesh count/quality/region mismatch')
    points=mesh['points'];bounds=[[min(p[d] for p in points),max(p[d] for p in points)] for d in range(3)]
    expected=[[-config['upstream_h']*.01,config['downstream_h']*.01],[0,.02],[0,.01]]
    if any(abs(a-b)>1e-10 for row,other in zip(bounds,expected) for a,b in zip(row,other)):raise ValueError('native domain mismatch')
    centres=mesh['centres'];ids=mesh['ranges']['inlet']
    v=read_initial_inlet(case,len(ids))
    for i,value in zip(ids,v):
        eta=(centres[i][1]-.01)/.01
        if abs(value[0]-6*eta*(1-eta))>1e-8 or abs(value[1])+abs(value[2])>1e-12:raise ValueError('native inlet face/profile mismatch')
    near=sorted(centres[i][0]/.01 for i in mesh['ranges']['lowerWall'] if abs(centres[i][1])<1e-10 and 0<centres[i][0]<.1)
    expected_x=[(i+.5)*.1/config['scale'] for i in range(100*config['scale'])]
    if len(near)!=len(expected_x) or max(abs(a-b) for a,b in zip(near,expected_x))>1e-6:raise ValueError('near-step mesh changed with domain length')
    return mesh,{'cells':mesh['cells'],'bounds_m':bounds,'inlet_faces':len(ids),'near_wall_x_h':near}
