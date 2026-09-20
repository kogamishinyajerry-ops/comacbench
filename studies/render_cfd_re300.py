"""Live progress and source-linked figures for the Re=300 native matrix."""
import argparse
import csv
import html
import json
from pathlib import Path
import re
import time


def render(out,figures=False):
    protocol=json.loads((out/'protocol.json').read_text());rows=[]
    for cid in protocol['matrix']:
        work=out/cid;row={'id':cid,'status':'pending','valid':False}
        path=work/'result.json'
        if path.exists():row=json.loads(path.read_text())
        elif (work/'running.json').exists():row=json.loads((work/'running.json').read_text())
        if row['status']=='running' and (work/'log.simpleFoam').exists():
            with (work/'log.simpleFoam').open('rb') as f:
                f.seek(max(0,(work/'log.simpleFoam').stat().st_size-65536));tail=f.read().decode(errors='replace')
            times=re.findall(r'^Time = (\d+)\s*$',tail,re.M)
            if times:row['live_iteration']=int(times[-1])
        rows.append(row)
    analysis=json.loads((out/'analysis.json').read_text()) if (out/'analysis.json').exists() else None
    valid=[r for r in rows if r['valid']];done=[r for r in rows if r['status'] in ('complete','failed')]
    if figures:
        import numpy as np
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
        for row in valid:
            cid=row['id'];s=row['snapshots'][-1]
            with np.load(out/cid/'visual.npz') as z:x,y,psi,U=[z[k] for k in ('x','y','psi','U')]
            fig,ax=plt.subplots(1,2,figsize=(12,4),layout='constrained');q=s['x_over_h']
            image=ax[0].pcolormesh(x,y,U,cmap='RdBu_r',vmin=-.2,vmax=1.4,rasterized=True)
            ax[0].contour(x,y,psi,levels=[0],colors='#23383c',linewidths=.8)
            for contour in s['region']['contours']:
                xy=np.asarray(contour['xy_h']);ax[0].plot(xy[:,0],xy[:,1],'w-',lw=1)
            ax[0].plot(*s['region']['centre_xy_h'],'wo',ms=4);ax[0].plot(q,0,'o',color='#ce7524',clip_on=False)
            ax[0].set(xlim=(0,min(float(x[-1]),q*1.3)),ylim=(0,2),xlabel='x / h',ylabel='y / h',title=f'Primary X1 / h = {q:.6f}')
            fig.colorbar(image,ax=ax[0],label='u / Umean',shrink=.7)
            curve=np.asarray(s['native_curve']);ax[1].plot(curve[:,0],curve[:,1],color='#136e70')
            ax[1].axhline(0,color='#777',lw=.6)
            for root in s['native_association']['all_upcrossings']:ax[1].plot(root['x_h'],0,'o',color='#ce7524' if root['primary_member'] else '#bd4545')
            ax[1].set(xlabel='x / h',ylabel='Kinematic wall shear (m2/s2)',title='Complete wall; primary membership required');ax[1].grid(alpha=.15)
            fig.suptitle(f"Re=300 | G{(1,2,4,8).index(row['config']['scale'])} | Lu={row['config']['upstream_h']}h, Ld={row['config']['downstream_h']}h")
            fig.savefig(out/(cid+'.png'),dpi=150);plt.close(fig)
        if analysis:
            fig,axes=plt.subplots(1,2,figsize=(11,3.6),layout='constrained')
            for group in analysis['groups']:
                selected=sorted([r for r in valid if r['config']['upstream_h']==group['upstream_h'] and r['config']['downstream_h']==group['downstream_h']],key=lambda r:r['config']['scale'])
                axes[0].plot([(1,2,4,8).index(r['config']['scale']) for r in selected],[r['qoi']['x_over_h'] for r in selected],'o-',label=f"{group['upstream_h']}h/{group['downstream_h']}h")
            axes[0].axhline(6.751,ls='--',color='#888',label='Paper 6.751');axes[0].set(xticks=range(4),xticklabels=['G0','G1','G2','G3'],ylabel='Primary X1 / h');axes[0].legend(fontsize=8)
            gs=analysis['groups'];values=[g['gci'].get('fine_gci',float('nan'))*100 for g in gs]
            axes[1].bar([f"{g['upstream_h']}/{g['downstream_h']}" for g in gs],values,color='#136e70');axes[1].axhline(.5,ls='--',color='#ce7524');axes[1].set(ylabel='Finest-three GCI (%)',ylim=(0,max(.6,max((v for v in values if np.isfinite(v)),default=0)*1.2)))
            fig.savefig(out/'convergence.svg');plt.close(fig)
    with (out/'results.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['id','status','valid','x1_h','wall_gap','iteration','seconds'])
        for r in rows:writer.writerow([r['id'],r['status'],r['valid'],r.get('qoi',{}).get('x_over_h'),r.get('wall',{}).get('relative_native_gap'),r.get('qoi',{}).get('iteration'),r.get('seconds')])
    def status(r):
        if r['status']=='pending':return '未开始'
        if r['status']=='failed':return '失败，保留证据'
        if r['status']=='complete':return '原生与主涡复核有效' if r['valid'] else '计算结束，检查未通过'
        return '求解第 '+str(r['live_iteration'])+' 步' if 'live_iteration' in r and r.get('phase')=='simpleFoam' else '处理中：'+r.get('phase','准备')
    table=''
    for r in rows:
        q=r.get('qoi',{}).get('x_over_h');gap=r.get('wall',{}).get('relative_native_gap')
        label=f"<a href='{r['id']}/result.json'>{r['id']}</a>" if r['status'] in ('complete','failed') else r['id']
        table+=f"<tr><td>{label}</td><td>{html.escape(status(r))}</td><td>{q if q is not None else '—'}</td><td>{f'{gap*100:.5f}%' if gap is not None else '—'}</td><td>{html.escape(r.get('error',''))}</td></tr>"
    band=analysis.get('screening_tolerance_candidate') if analysis else None
    band_text=f"±{100*band['relative_band']:g}%" if band else '待校核'
    state='研究通过' if analysis and analysis['gate_passed'] else ('存在未通过门槛' if analysis else '真实求解进行中')
    retention=json.loads((out/'retention-check.json').read_text()) if (out/'retention-check.json').exists() else None
    gallery=[{'id':r['id'],'image':r['id']+'.png'} for r in valid if (out/(r['id']+'.png')).exists()]
    visual=''
    if gallery:
        options=''.join(f"<option>{item['id']}</option>" for item in gallery)
        visual=f'''<section><h2>查看主涡与全部壁面零点</h2><label for="case">算例</label><select id="case">{options}</select><img id="field" src="{gallery[0]['image']}" alt="实际原生场的主回流区闭合流线与全部壁面零点"><p>白线为主涡内部闭合流线，黑线为零流函数；橙点归属主涡，其他候选全部保留。</p></section><script>const cases={json.dumps(gallery)};document.getElementById('case').addEventListener('change',e=>{{document.getElementById('field').src=cases.find(c=>c.id===e.target.value).image;}});</script>'''
    decisions=''
    if analysis:
        decisions=f"<section><h2>本阶段决策</h2><p>{html.escape('；'.join(analysis['failed_gates']) or '本组数值门槛全部通过。候选容差仅适用于本研究，未扩展 Re=400。')}</p><p><a href='analysis.json'>完整分析</a> · <a href='results.csv'>CSV</a> · <a href='README.md'>复核与适用边界</a></p>"+("<img src='convergence.svg' alt='四网格四域再附着长度与 GCI'>" if (out/'convergence.svg').exists() else '')+'</section>'
    doc=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{'' if analysis else '<meta http-equiv="refresh" content="30">'}<title>Re=300 四网格四域验证 · COMACBench</title><style>*{{box-sizing:border-box}}body{{margin:0;background:#f3f4ef;color:#23383c;font:16px/1.7 -apple-system,"PingFang SC",sans-serif}}main{{max-width:1200px;padding:32px;margin:auto}}h1{{line-height:1.3}}section,.card{{background:white;border:1px solid #dbe2db;border-radius:10px;padding:22px;margin:20px 0}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}.card strong{{display:block;color:#136e70;font-size:27px}}a{{color:#136e70}}.scroll{{overflow:auto}}table{{border-collapse:collapse;font-size:13px;width:100%}}td,th{{padding:10px;text-align:left;border-bottom:1px solid #ddd}}img{{width:100%;height:auto}}select{{font:inherit;padding:8px;margin:10px}}.note{{border-left:5px solid #136e70;padding:14px 20px;background:#e6f0e9}}@media(max-width:720px){{main{{padding:16px}}.cards{{grid-template-columns:repeat(2,1fr)}}}}</style><main><p>COMACBENCH / CFD / Re=300</p><h1>{state}</h1><p>四档网格 × 四种域，共 16 组独立原生算例。先确认主回流区，再评价再附着长度、入口流量和数值敏感性。</p><div class="cards"><div class="card"><strong>{len(done)}/16</strong>已结束算例</div><div class="card"><strong>{len(valid)}/16</strong>原生及身份有效</div><div class="card"><strong>{band_text}</strong>研究候选容差</div><div class="card"><strong>10%</strong>公开评分容差保持</div></div><p class="note">父阶段 Re=200 v2 证据已复核。两次场保存策略：{'配对已通过' if retention else '配对验证中'}。G0–G2 全部有效后才放行 G3，完成全矩阵后再决定容差。</p><section><h2>每个算例的真实状态</h2><div class="scroll"><table><thead><tr><th>域/网格与证据</th><th>状态</th><th>主涡 X1/h</th><th>近壁差</th><th>问题反馈</th></tr></thead><tbody>{table}</tbody></table></div></section>{visual}{decisions}<section><h2>本次验证的范围</h2><p>二维稳态层流，h=0.01 m，扩张比 2。域为上游 5/10h、下游 30/60h；参考论文 Table 5 给出 Re=300 的 X1/h=6.751，仅在识别主涡后用于误差比较。最细网格 GCI≤0.5%、近壁差≤0.1%、域差≤0.25%；粗网格近壁差仅作趋势诊断。</p><p>新算例保留最近两次完整场、冻结初值及全部求解日志，旧证据不清理。该层流研究不能代替三维非定常航空工业工况验收。</p><p><a href='protocol.json'>冻结协议与身份</a> · <a href='parent-verification.json'>父阶段验证</a> · <a href='../2026-09-08-cfd-primary-v2/index.html'>Re=200 主涡复核</a> · <a href='https://doi.org/10.1016/j.compfluid.2007.09.003'>参考论文</a></p></section></main></html>'''
    temp=out/'index.html.tmp';temp.write_text(doc);temp.replace(out/'index.html')
    return {'done':len(done),'valid':len(valid),'analysis':bool(analysis)}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--watch',action='store_true');p.add_argument('--figures',action='store_true');a=p.parse_args()
    while True:
        state=render(a.out,a.figures);print(json.dumps(state),flush=True)
        if not a.watch or state['analysis']:break
        time.sleep(30)
