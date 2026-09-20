"""Display-only progress adapter for OpenFOAM's Time = <n>s log format."""
import argparse
import json
from pathlib import Path
import re
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from studies.render_cfd_re300_v3 import render
from studies.cfd_step_sensitivity import save


def update(out):
    state=render(out);progress=[]
    for cid in json.loads((out/'protocol.json').read_text())['matrix']:
        work=out/cid
        if (work/'result.json').exists() or not (work/'running.json').exists():continue
        row=json.loads((work/'running.json').read_text());p=work/'log.simpleFoam'
        if row.get('phase')!='simpleFoam' or not p.exists():continue
        with p.open('rb') as f:
            f.seek(max(0,p.stat().st_size-65536));tail=f.read().decode(errors='replace')
        values=re.findall(r'^Time = (\d+)(?:s)?\s*$',tail,re.M)
        if values:progress.append({'case':cid,'simple_iteration':int(values[-1])})
    text=(out/'index.html').read_text()
    for row in progress:
        pattern=r'(<tr><td>'+re.escape(row['case'])+r'</td><td>)[^<]*(</td>)'
        text=re.sub(pattern,lambda m:m[1]+'正在求解：第 '+str(row['simple_iteration'])+' 步'+m[2],text)
    temp=out/'index.progress.tmp';temp.write_text(text);temp.replace(out/'index.html')
    save(out/'live-progress.json',{'display_only':True,'matrix':state,'active':progress})
    return dict(state,active=progress)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--watch',action='store_true');a=p.parse_args()
    while True:
        state=update(a.out);print(json.dumps(state),flush=True)
        if state['analysis'] or not a.watch:break
        time.sleep(30)
