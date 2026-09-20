"""Enumerate native wall-shear sign changes without changing the study QoI."""
import argparse
import html
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from studies.cfd_step_sensitivity import sha,save,DOMAINS


def crossings(curve):
    if not isinstance(curve,(list,tuple)) or len(curve)<2:
        raise ValueError('At least two ordered finite samples are required')
    for pair in curve:
        if not isinstance(pair,(list,tuple)) or len(pair)!=2 or any(
                isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in pair):
            raise ValueError('Each sample must contain finite numeric x and shear')
    if any(b[0]<=a[0] for a,b in zip(curve,curve[1:])):
        raise ValueError('Sample coordinates must be strictly increasing')
    roots=[]
    for index,((x,u),(y,v)) in enumerate(zip(curve,curve[1:])):
        if (u<0<v) or (v<0<u):
            scale=max(abs(u),abs(v));a=abs(u)/scale;b=abs(v)/scale
            roots.append({'x_h':x+(y-x)*a/(a+b),
                          'direction':'negative_to_positive' if u<0 else 'positive_to_negative',
                          'bracket_indices':[index,index+1],'bracket':[[x,u],[y,v]]})
    zeros=[x for x,u in curve if u==0]
    up=[r for r in roots if r['direction']=='negative_to_positive']
    return {'crossings':roots,'zero_samples_x_h':zeros,
            'ambiguous_for_first_upcrossing_rule':bool(zeros) or len(up)!=1}


def audit(root,prefix):
    root=Path(root).resolve();prefix=Path(prefix).resolve()
    protocol=json.loads((root/'protocol.json').read_text());reynolds=protocol['reynolds']
    if reynolds!=200:raise ValueError('This diagnostic is scoped to the Re=200 study')
    rows=[];missing=[];curves={}
    for u,d in DOMAINS:
        for scale in (1,2,4,8):
            name=f're{reynolds}-u{u}-d{d}-g{scale}';path=root/name/'result.json'
            if not path.exists():missing.append(name);continue
            result=json.loads(path.read_text());curve=result['qoi']['curve'];entry=crossings(curve)
            entry.update(case=name,upstream_h=u,downstream_h=d,scale=scale,
                         native_valid=result['valid'],iteration=result['qoi']['iteration'],
                         frozen_selected_x_h=result['qoi']['x_over_h'],
                         near_wall_gap=result['wall']['relative_native_gap'],
                         result_sha256=sha(path),samples=len(curve))
            rows.append(entry);curves[name]=curve
    if not rows:raise ValueError('No completed native results to audit')
    data={'diagnostic_only':True,'partial':bool(missing),'missing':missing,'rows':rows,
          'reynolds':reynolds,'source_sha256':sha(__file__),'protocol_sha256':sha(root/'protocol.json'),
          'primary_root_selected':False,'frozen_qoi_changed':False,
          'feedback':[{'case':r['case'],'issue':'QoI identity ambiguous: multiple upcrossings or zero samples',
                       'action':'Define and verify the primary recirculation region in a new protocol; retain every sign change.'}
                      for r in rows if r['ambiguous_for_first_upcrossing_rule']]}
    save(prefix.with_suffix('.json'),data)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,3,figsize=(13,3.7),layout='constrained')
    colors=['#116e6a','#587ccc','#bd7b22','#9760a6']
    selected=[r for r in rows if r['upstream_h']==5 and r['downstream_h']==30]
    for row,color in zip(selected,colors):
        curve=curves[row['case']];x,y=zip(*curve)
        for axis in axes:axis.plot(x,y,color=color,label=f"G{(1,2,4,8).index(row['scale'])}")
        axes[1].plot(x,y,'.',color=color,ms=4)
    for axis in axes:
        axis.axhline(0,color='#222',lw=.7);axis.grid(alpha=.15);axis.set_xlabel('x / h')
    axes[0].set(title='Complete lower wall (Lu=5h, Ld=30h)',ylabel='Native kinematic wall shear (m2/s2)',xlim=(0,30))
    axes[0].legend(ncol=2,fontsize=8)
    axes[1].set(title='Corner: sign detail',xlim=(0,.025),ylim=(-1e-6,1.2e-5))
    for row in selected:
        if row['scale']==8:
            first=curves[row['case']][0]
            axes[1].annotate(f'First face: {first[1]:.3e}',xy=first,xytext=(.008,5e-6),
                             arrowprops={'arrowstyle':'->','color':'#ba573f'},fontsize=8,color='#ba573f')
    axes[2].set(title='Downstream sign change (diagnostic)',xlim=(4.85,5.05),ylim=(-8e-4,9e-4))
    fig.savefig(prefix.with_suffix('.svg'));fig.savefig(prefix.with_suffix('.png'),dpi=180);plt.close(fig)
    table=''
    for row in rows:
        roots='; '.join(f"{r['x_h']:.9f} ({'−→+' if r['direction']=='negative_to_positive' else '+→−'})" for r in row['crossings'])
        table+=f"<tr><td>{html.escape(row['case'])}</td><td>{row['frozen_selected_x_h']:.9f}</td><td>{roots or '无'}</td><td>{'需澄清' if row['ambiguous_for_first_upcrossing_rule'] else '单一负→正零点'}</td></tr>"
    stage='部分结果，仍在计算' if missing else '16 个算例计算完成后的诊断'
    doc=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Re={reynolds} 零点判据审计</title>
<style>body{{font:16px/1.7 -apple-system,"PingFang SC",sans-serif;background:#f4f3ee;color:#253235;margin:0}}main{{max-width:1180px;margin:auto;padding:30px}}h1{{line-height:1.35}}.alert,section{{background:white;padding:22px;margin:20px 0;border-radius:10px}}.alert{{border-left:5px solid #ba573f}}img{{width:100%}}.scroll{{overflow:auto}}table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{padding:10px;border-bottom:1px solid #ddd;text-align:left;white-space:nowrap}}a{{color:#116e6a}}</style>
<main><h1>Re={reynolds}：零点规则与原生曲线</h1><p>{stage}。本页只列举符号翻转，不重新选取主再附着点，不替换本轮 QoI、GCI 或评分。</p>
<div class="alert">当前有 {len(rows)}/16 个已完成样本，其中 {len(data["feedback"])} 个存在多负→正零点或零值样本歧义。下表列出冻结规则选中的位置及全部候选。仅靠“第一次”不能证明所选零点对应主再附着位置；曲线中的小幅符号变化是否具有物理意义，需要独立核验。</div>
<section><h2>完整曲线与两个局部放大</h2><img src="{prefix.name}.svg" alt="四档原生壁面剪切完整曲线、角部和下游零点局部放大"><p>右侧两幅的坐标范围仅用于展示，不参与判分、筛选或剔除零点。全部原生曲线保留在各算例 result.json。</p></section>
<section><h2>逐项反馈</h2><div class="scroll"><table><thead><tr><th>算例</th><th>冻结规则选中 x/h</th><th>全部符号翻转 x/h</th><th>判据反馈</th></tr></thead><tbody>{table}</tbody></table></div></section>
<section><h2>需要补充的判据</h2><p>先定义主回流区的识别与零点归属，再用独立速度场、近壁梯度和原生剪切交叉检查。多个候选无法唯一对应时应反馈异常；不能按“更接近参考答案”挑选，也不能对角部设置事后阈值来让结果通过。</p><p>用新协议单独验证修订后的后处理；当前冻结研究和原始失败判定保留。二维层流算例不能代替飞机工业工况验收。</p><p><a href="{prefix.name}.json">完整零点审计 JSON</a> · <a href="index.html">研究报告或当前进度</a></p></section></main></html>'''
    prefix.with_suffix('.html').write_text(doc)
    print(json.dumps({'partial':data['partial'],'cases':len(rows),'flagged':len(data['feedback']),'report':str(prefix.with_suffix('.html'))}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--prefix',type=Path,required=True);a=p.parse_args();audit(a.root,a.prefix)
