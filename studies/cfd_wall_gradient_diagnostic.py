"""Independent wall-derivative diagnosis; never replaces the declared native QoI."""
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runners.solvers.backward_step import mesh_data
from runners.solvers.foam_text import dictionary, field_values
from studies.cfd_step_sensitivity import grid_convergence, sha, save, DOMAINS


def wall_gradient(y1,y2,u1,u2):
    """Derivative at no-slip wall of quadratic through 0, (y1,u1), (y2,u2)."""
    if not all(math.isfinite(v) for v in (y1,y2,u1,u2)) or not 0<y1<y2:
        raise ValueError('Need two finite velocities at increasing positive wall distances')
    return (u1*y2*y2-u2*y1*y1)/(y1*y2*(y2-y1))


def crossing(curve):
    for (x0,v0),(x1,v1) in zip(curve,curve[1:]):
        if v0<0<=v1:return x0-v0*(x1-x0)/(v1-v0)
    raise ValueError('No negative-to-positive wall derivative crossing')


def diagnose(work):
    row=json.loads((work/'result.json').read_text())
    if not row['valid'] or row['status']!='complete':raise ValueError('Diagnostic requires converged native data')
    case=work/'case';iteration=row['qoi']['iteration'];mesh=mesh_data(case)
    # In this declared extruded orthogonal mesh, a z=0 face gives cell-centre x,y.
    centres={}
    for i,c in enumerate(mesh['centres']):
        if abs(c[2])<1e-12:centres[mesh['owner'][i]]=(c[0],c[1])
    if len(centres)!=mesh['cells']:raise ValueError('Expected one planar face per cell')
    columns={}
    for cell,(x,y) in centres.items():columns.setdefault(round(x,10),[]).append((y,cell))
    for column in columns.values():column.sort()
    U=field_values(dictionary(case/str(iteration)/'U')['internalField'],mesh['cells'],True)
    nu=.02/row['config']['reynolds'];first=[];second=[]
    for face in mesh['ranges']['lowerWall']:
        x,y,_=mesh['centres'][face]
        if abs(y)>1e-12 or x<=0:continue
        owner=mesh['owner'][face];xc,y1=centres[owner]
        if abs(xc-x)>1e-10 or y1<=0:raise ValueError('Non-orthogonal wall stencil')
        column=columns[round(x,10)]
        if len(column)<2 or column[0][1]!=owner:raise ValueError('Missing first/second wall-normal cell')
        y2,upper=column[1]
        if abs(centres[upper][0]-x)>1e-10:raise ValueError('Wall-normal cells are not aligned')
        first.append((x/.01,nu*U[owner][0]/y1))
        second.append((x/.01,nu*wall_gradient(y1,y2,U[owner][0],U[upper][0])))
    first.sort();second.sort();native=row['qoi']['x_over_h'];linear=crossing(first)
    return {'id':row['id'],'config':row['config'],'result_sha256':sha(work/'result.json'),
            'native_x_over_h':native,'first_cell_x_over_h':linear,
            'first_cell_minus_native':linear-native,
            'quadratic_x_over_h':crossing(second),'diagnostic_only':True}


def run(directory):
    directory=Path(directory).resolve();protocol=json.loads((directory/'protocol.json').read_text())
    rows=[diagnose(directory/cid) for cid in protocol['case_ids']]
    groups=[]
    for up,down in DOMAINS:
        subset=sorted((r for r in rows if r['config']['upstream_h']==up and r['config']['downstream_h']==down),key=lambda r:r['config']['scale'])
        groups.append({'upstream_h':up,'downstream_h':down,
                       'quadratic_gci':grid_convergence([r['quadratic_x_over_h'] for r in subset])})
    result={'diagnostic_only':True,'formal_gate_unchanged':True,'source_sha256':sha(__file__),
            'protocol_sha256':sha(directory/'protocol.json'),'rows':rows,'groups':groups,
            'interpretation':'Same converged U fields, different no-slip wall derivative reconstruction. Velocity-only du/dy is not identical to native tensor shear; their difference is retained. A smaller GCI is diagnostic evidence only; adoption needs a separately declared QoI version and validation.'}
    save(directory.parent/'wall-gradient-diagnostic.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result


if __name__=='__main__':run(sys.argv[1])
