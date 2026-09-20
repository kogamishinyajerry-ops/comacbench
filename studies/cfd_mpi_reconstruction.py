"""Verify reconstructed fields directly against native rank-addressed data."""
import math
from pathlib import Path
from runners.solvers.foam_text import Reader,counted,field_values
from studies.cfd_fourth_grid import field_dictionary


def verify_partition(full,shards):
    visited=bytearray(len(full));worst=0.
    for ids,values in shards:
        if len(ids)!=len(values):raise ValueError('partition count mismatch')
        for index,value in zip(ids,values):
            if type(index)!=int or index<0 or index>=len(full) or visited[index]:raise ValueError('duplicate or invalid global address')
            a=full[index] if isinstance(full[index],(list,tuple)) else [full[index]]
            b=value if isinstance(value,(list,tuple)) else [value]
            if len(a)!=len(b):raise ValueError('field dimension mismatch')
            for x,y in zip(a,b):
                if not math.isfinite(x) or not math.isfinite(y) or not math.isclose(x,y,rel_tol=1e-12,abs_tol=1e-12):raise ValueError('reconstructed field differs from native rank data')
                worst=max(worst,abs(x-y))
            visited[index]=1
    if not all(visited):raise ValueError('incomplete partition coverage')
    return {'verified_entries':len(full),'max_absolute_error':worst}


def signed_addresses(path):
    reader=Reader(Path(path).read_text())
    if reader.take()!='FoamFile' or reader.take()!='{' or reader.mapping('}').get('format')!=['ascii']:raise ValueError('address header')
    count=int(reader.take());body=reader.value()
    if not isinstance(body,list) or len(body)!=count or reader.peek() is not None:raise ValueError('address count')
    result=[int(v) for v in body]
    if any(str(v)!=s or v==0 for v,s in zip(result,body)):raise ValueError('invalid signed face address')
    return result


def verify_reconstruction(case,iteration,cells,ranks=4):
    case=Path(case);result={}
    for field,vector in [('U',True),('p',False)]:
        full=field_values(field_dictionary(case/str(iteration)/field)['internalField'],cells,vector)
        def shards():
            for rank in range(ranks):
                root=case/f'processor{rank}';ids=counted(root/'constant/polyMesh/cellProcAddressing','labels')
                yield ids,field_values(field_dictionary(root/str(iteration)/field)['internalField'],len(ids),vector)
        result[field]=verify_partition(full,shards())
    boundary=counted(case/'constant/polyMesh/boundary','boundary')['lowerWall'];start=int(boundary['startFace'][0]);n=int(boundary['nFaces'][0])
    full=field_values(field_dictionary(case/str(iteration)/'wallShearStress')['boundaryField']['lowerWall']['value'],n,True)
    def wall_shards():
        for rank in range(ranks):
            root=case/f'processor{rank}';b=counted(root/'constant/polyMesh/boundary','boundary')['lowerWall']
            s=int(b['startFace'][0]);n=int(b['nFaces'][0]);face_ids=signed_addresses(root/'constant/polyMesh/faceProcAddressing')[s:s+n]
            if any(v<=0 for v in face_ids):raise ValueError('unexpected reversed physical wall face')
            ids=[v-1-start for v in face_ids]
            yield ids,field_values(field_dictionary(root/str(iteration)/'wallShearStress')['boundaryField']['lowerWall']['value'],n,True)
    result['lower_wall_shear']=verify_partition(full,wall_shards())
    return result
