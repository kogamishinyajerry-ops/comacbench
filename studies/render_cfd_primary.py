"""Source-linked primary-region figures and a small case browser."""
import argparse
import csv
import html
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def render(out):
    data=json.loads((out/'analysis.json').read_text());rows=data['rows']
    plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
    catalogue=[]
    for row in rows:
        cid=row['id'];detail=json.loads((out/(cid+'.json')).read_text());s=detail['snapshots'][-1]
        with np.load(out/(cid+'.npz')) as field:
            x,y,psi,xc,yc,U,V=[field[k] for k in ('x','y','psi','xc','yc','U','V')]
        q=s['x_over_h'];view=min(float(x[-1]),q*1.3)
        fig,ax=plt.subplots(2,2,figsize=(13,7.4),layout='constrained',gridspec_kw={'height_ratios':[1.3,1]})
        a=ax[0,0];m=a.pcolormesh(x,y,U,cmap='RdBu_r',vmin=-.2,vmax=1.4,shading='flat',rasterized=True)
        a.contour(x,y,psi,levels=[0],colors='#293a42',linewidths=.8)
        for c in s['region']['contours']:
            xy=np.asarray(c['xy_h']);a.plot(xy[:,0],xy[:,1],color='#fff',lw=.8)
        a.plot(*s['region']['centre_xy_h'],'wo',ms=4)
        a.plot(q,0,'o',color='#c76d13',ms=7,clip_on=False)
        a.annotate(f'X1/h = {q:.6f}',(q,0),(q-.6,.32),arrowprops={'arrowstyle':'->'},fontsize=9)
        a.set(xlim=(0,view),ylim=(0,2),xlabel='x / h',ylabel='y / h',title='Primary eddy: flux streamfunction + cell velocity')
        a.axvline(0,ymin=0,ymax=.5,color='#253235',lw=5)
        fig.colorbar(m,ax=a,label='u / Umean',shrink=.65)
        b=ax[0,1];b.pcolormesh(x,y,psi,cmap='BrBG',vmin=-2e-6,vmax=2e-6,shading='gouraud',rasterized=True)
        b.contour(x,y,psi,levels=[0],colors='#293a42',linewidths=1)
        step=max(1,len(y)//50);ix=np.where(xc<.3)[0][::max(1,int(row['config']['scale']/2))];iy=np.where(yc<.3)[0][::step]
        b.quiver(xc[ix],yc[iy],U[np.ix_(iy,ix)],V[np.ix_(iy,ix)],color='#253235',angles='xy')
        b.set(xlim=(0,.3),ylim=(0,.3),xlabel='x / h',ylabel='y / h',title='Corner detail: psi = 0; all signals retained')
        curve=np.asarray(s['native_curve'])
        for a in ax[1]:
            a.plot(curve[:,0],curve[:,1],color='#126f70',lw=1.5,label='native shear')
            a.axhline(0,color='#333',lw=.6);a.set_xlabel('x / h');a.grid(alpha=.15)
        ax[1,0].set(xlim=(0,view),ylabel='Kinematic wall shear (m2/s2)',title='Every wall zero; membership selects X1')
        for root in s['native_association']['all_upcrossings']:
            color='#c76d13' if root['primary_member'] else '#bc4c4c'
            ax[1,0].plot(root['x_h'],0,'o',color=color,ms=6)
        ax[1,1].set(xlim=(0,.035),ylim=(-1e-6,2e-5),title='Corner wall samples (display window only)')
        ax[1,1].plot(curve[:,0],curve[:,1],'.',color='#126f70',ms=4)
        fig.suptitle(f"Re=200 | G{(1,2,4,8).index(row['config']['scale'])} | Lu={row['config']['upstream_h']}h, Ld={row['config']['downstream_h']}h | saved t={s['iteration']}",fontsize=13)
        fig.savefig(out/(cid+'.png'),dpi=145);plt.close(fig)
        catalogue.append({'id':cid,'image':cid+'.png','q':q,'old':row['old_x_over_h'],
                          'gap_percent':100*row['wall']['relative_native_gap'],
                          'centre':s['region']['centre_xy_h'],'path':s['flux']['path_defect_relative']})
    fig,axes=plt.subplots(1,2,figsize=(11,3.6),layout='constrained')
    for group in data['groups']:
        selected=sorted([r for r in rows if r['config']['upstream_h']==group['upstream_h'] and r['config']['downstream_h']==group['downstream_h']],key=lambda r:r['config']['scale'])
        axes[0].plot([(1,2,4,8).index(r['config']['scale']) for r in selected],[r['qoi']['x_over_h'] for r in selected],'o-',label=f"{group['upstream_h']}h / {group['downstream_h']}h",alpha=.75)
    axes[0].axhline(4.982,color='#888',ls='--',label='Paper X1/h = 4.982');axes[0].set(xticks=[0,1,2,3],xticklabels=['G0','G1','G2','G3'],ylabel='Primary X1 / h',title='Same identity across four grids');axes[0].legend(fontsize=8)
    values=[g['gci'].get('fine_gci',np.nan)*100 for g in data['groups']]
    labels=[f"{g['upstream_h']}h / {g['downstream_h']}h" for g in data['groups']]
    axes[1].bar(labels,values,color='#126f70',width=.5);axes[1].axhline(.5,color='#c76d13',ls='--',label='Gate 0.5%')
    axes[1].set(ylabel='Finest-three GCI (%)',title='Grid uncertainty check');axes[1].legend(fontsize=8)
    axes[1].set_ylim(0,max(.6,max((v for v in values if np.isfinite(v)),default=0)*1.2))
    fig.savefig(out/'convergence.svg');fig.savefig(out/'convergence.png',dpi=160);plt.close(fig)
    fields=['id','grid','upstream_h','downstream_h','old_x_h','primary_x_h','near_wall_gap_percent','iteration_change','path_defect_relative']
    with (out/'results.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for row,item in zip(rows,catalogue):
            writer.writerow(dict(zip(fields,[row['id'],(1,2,4,8).index(row['config']['scale']),row['config']['upstream_h'],row['config']['downstream_h'],row['old_x_over_h'],item['q'],item['gap_percent'],row['relative_change'],item['path']])))
    passed=data['gate_passed'];band=data.get('screening_tolerance_candidate');band_text=f"±{band['relative_band']*100:g}%" if band else '未形成'
    fine=[r for r in rows if r['config']['scale']==8]
    table=''.join(f"<tr><td><a href='{r['id']}.json'>{r['id']}</a></td><td>{r['old_x_over_h']:.9f}</td><td>{r['qoi']['x_over_h']:.9f}</td><td>{100*r['wall']['relative_native_gap']:.5f}%</td><td>{r['relative_change']:.2e}</td></tr>" for r in rows)
    options=''.join(f"<option value='{r['id']}'{' selected' if r['id']=='re200-u5-d30-g8' else ''}>{r['id']}</option>" for r in rows)
    first=next((r for r in catalogue if r['id']=='re200-u5-d30-g8'),catalogue[0] if catalogue else None)
    warnings=''.join('<li>'+html.escape(v['issue'])+'</li>' for v in data['feedback'])
    summary='16 组主涡身份复核通过' if passed else '复核尚有未通过项'
    conclusion='允许规划下一档工况；本次没有启动新求解。' if passed else '暂停容差校准与工况扩展，先处理下列反馈。'
    doc=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Re=200 主回流区复核 · COMACBench</title>
<style>*{{box-sizing:border-box}}body{{margin:0;background:#f3f4ef;color:#23383c;font:16px/1.65 -apple-system,"PingFang SC",sans-serif}}main{{max-width:1220px;margin:auto;padding:32px}}h1{{font-size:34px;line-height:1.3;margin:12px 0}}h2{{font-size:22px}}a{{color:#126f70}}.label{{letter-spacing:2px;font-size:13px;color:#426f71}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:26px 0}}.card,section{{background:white;border:1px solid #dce3dc;border-radius:10px;padding:22px}}.card strong{{display:block;font-size:27px;color:#126f70}}.card small{{font-size:13px}}section{{margin:20px 0}}.notice{{border-left:5px solid #126f70;padding:16px 20px;background:#e6f0e9}}img{{display:block;width:100%;height:auto}}select{{font:inherit;padding:8px;max-width:100%;margin:8px 0}}.scroll{{overflow:auto}}table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{text-align:left;padding:10px;border-bottom:1px solid #dce3dc;white-space:nowrap}}code{{overflow-wrap:anywhere}}.muted{{color:#577074}}@media(max-width:760px){{main{{padding:18px}}.cards{{grid-template-columns:repeat(2,1fr)}}h1{{font-size:27px}}section{{padding:16px}}}}</style>
<main><div class="label">COMACBENCH / CFD / PRIMARY RECIRCULATION v2</div><h1>{summary}</h1><p>同一批 Re=200 原生场，使用论文中的主回流区 X₁ 定义重新测量。面流量与单元速度分别重建区域，确认主涡后才匹配壁面零点。</p>
<div class="cards"><div class="card"><strong>{len(rows)} / 16</strong><small>四网格 × 四域</small></div><div class="card"><strong>{data['field_snapshots_verified']}</strong><small>保存时刻独立复核</small></div><div class="card"><strong>{band_text}</strong><small>研究筛查候选容差</small></div><div class="card"><strong>10%</strong><small>原公开评分容差保持</small></div></div>
<div class="notice">{conclusion} v1 的失败、旧零点与所有原生场均保留。候选容差来自本组样本的保守误差核算，不是盲测通过率或统计置信区间。</div>
<section><h2>为什么旧规则会选错</h2><p>“第一个负转正零点”在 G3 选中角部约 0.00649h。新规则先找到与台阶上缘分离位置相连的唯一负流函数区域，并验证内部极小值及三条闭合等值线；只有归属该区域的壁面零点才能成为 X₁。所有角部候选仍可查看。</p><p>论文 Fig. 1c 区分主涡 X₁ 与角部涡 X₀–Y₀，Table 5 给出 Re=200、扩张比 2 的 X₁/h=4.982。此参考值仅在选根完成后用于误差分析。<a href="https://doi.org/10.1016/j.compfluid.2007.09.003">参考论文</a> · <a href="https://www.researchgate.net/publication/223115490_Numerical_solutions_of_2-D_steady_incompressible_flow_over_a_backward-facing_step_Part_I_High_Reynolds_number_solutions">作者上传全文</a></p></section>
<section><h2>逐个查看流场与零点</h2><label for="case">算例</label> <select id="case">{options}</select><p id="detail" class="muted"></p><img id="field" src="{first['image'] if first else ''}" alt="主回流区、角部流函数与完整壁面零点的原生场证据"><p><a id="case-data" href="{first['id']+'.json' if first else 'analysis.json'}">本算例完整证据 JSON</a> · 白线为主涡闭合等值线，黑线为 ψ=0。角部单元级微小负值不足以确认为独立物理涡；图中放大窗口不参与选择。</p></section>
<section><h2>网格与域敏感性</h2><img src="convergence.svg" alt="四档网格主再附着点与最细三档 GCI"><p>最大 GCI：{max(values,default=float('nan')):.5f}%；G3 最大近壁差：{max((r['wall']['relative_native_gap']*100 for r in fine),default=float('nan')):.5f}%；G3 域差：{(data['fine_domain_effect'] or 0)*100:.7f}%。门槛沿用上一阶段，未随复核结果调整。</p></section>
<section><h2>16 组复核明细</h2><div class="scroll"><table><thead><tr><th>算例 / 证据</th><th>旧 x/h</th><th>主涡 X₁/h</th><th>近壁差</th><th>末两场变化</th></tr></thead><tbody>{table}</tbody></table></div></section>
<section><h2>边界、反馈与下一步</h2><ul>{warnings or '<li>主涡身份与数值门槛无阻断项；角部微小信号仍属未充分解析的诊断。</li>'}</ul><p>本研究仅覆盖二维稳态层流、矩形网格和当前四种域。论文使用更长的上游/下游及不同离散和边界处理。新的选择算法是本项目的离散实现，不能称为论文原算法。新工况须延续身份规则并重新验证，三维非定常工业工况另行建立证据。</p><p><a href="analysis.json">完整分析</a> · <a href="results.csv">CSV</a> · <a href="identity.json">新身份</a> · <a href="protocol-freeze.json">协议冻结</a> · <a href="README.md">复跑与决策说明</a> · <a href="../2026-09-07-cfd-re200/index.html">原失败报告</a></p></section>
<script>const cases={json.dumps(catalogue)};const select=document.getElementById('case');function update(){{const c=cases.find(x=>x.id===select.value);if(!c)return;document.getElementById('field').src=c.image;document.getElementById('case-data').href=c.id+'.json';document.getElementById('detail').textContent=`旧测量 ${{c.old.toFixed(9)}} → 主涡 ${{c.q.toFixed(9)}}；近壁差 ${{c.gap_percent.toFixed(5)}}%；流量路径不闭合 ${{c.path.toExponential(2)}}。`;}}select.addEventListener('change',update);update();</script></main></html>'''
    (out/'index.html').write_text(doc)
    print(json.dumps({'case_images':len(catalogue),'csv_rows':len(rows),'gate_passed':passed}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);render(p.parse_args().out)
