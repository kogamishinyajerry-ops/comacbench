"""Standalone scientific plots, CSV and offline study summary from native results."""
import csv
import html
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def render(root):
    root=Path(root).resolve();analyses=[]
    primary='re100-resolved' if (root/'re100-resolved/analysis.json').is_file() else 're100'
    for name in (primary,'re200'):
        p=root/name/'analysis.json'
        if p.exists():analyses.append((name,json.loads(p.read_text())))
    if not analyses:raise ValueError('No completed analysis')
    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
    sections=[]
    for name,data in analyses:
        re=data['reynolds'];decision=data['tolerance_decision'];rows=data['rows']
        incomplete=[r for r in rows if not r.get('qoi',{}).get('x_over_h') or not r.get('mesh')]
        if incomplete:
            reasons=''.join('<li>'+html.escape(r['id']+': '+r.get('error','missing native result'))+'</li>' for r in incomplete)
            sections.append(f'<section data-re="{re}"><h2>Re = {re} · 研究未完成</h2><p class="notice">存在缺失或失败的原生结果，不给出容差结论。</p><ul>{reasons}</ul><a href="{name}/analysis.json">查看原始分析与失败记录</a></section>')
            continue
        ref=rows[0]['reference']
        fig,ax=plt.subplots(figsize=(8,4.4),layout='constrained')
        for i,group in enumerate(data['groups']):
            up,down=group['upstream_h'],group['downstream_h']
            subset=sorted((r for r in rows if r['config']['upstream_h']==up and r['config']['downstream_h']==down),key=lambda r:r['config']['scale'])
            scales=[r['config']['scale'] for r in subset]
            ax.plot(scales,[r['qoi']['x_over_h'] for r in subset],marker=['o','s','^','x'][i],label=f'inlet {up}h / outlet {down}h',alpha=.8)
        ax.axhline(ref,color='#333333',ls='--',lw=1,label=f'Published reference {ref}')
        ax.set(xticks=[1,2,4],xticklabels=['G0 (1x)','G1 (2x)','G2 (4x)'],xlabel='In-plane refinement (same near-step spacing across domains)',ylabel='Reattachment length x/h',title=f'Re={re}: grid and domain sensitivity')
        ax.grid(alpha=.2);ax.legend(loc='best',fontsize=9)
        fig.savefig(root/f'{name}-grid.svg');fig.savefig(root/f'{name}-grid.png',dpi=180);plt.close(fig)
        fig,(gax,dax)=plt.subplots(1,2,figsize=(10,4),layout='constrained')
        labels=[f'{g["upstream_h"]}/{g["downstream_h"]}' for g in data['groups']]
        gcis=[100*g['gci']['fine_gci'] if g['gci']['applicable'] else float('nan') for g in data['groups']]
        gax.bar(labels,gcis,color=['#bc6538' if v>100*decision['policy']['fine_gci_max'] else '#087b79' for v in gcis])
        for i,g in enumerate(data['groups']):
            if not g['gci']['applicable']:gax.text(i,.02,'N/A',ha='center',color='#526976')
        gax.axhline(100*decision['policy']['fine_gci_max'],color='#7e3030',ls='--',label='Predeclared gate')
        gax.set(title='Fine-grid GCI vs gate',ylabel='GCI (%)',xlabel='Inlet / outlet length (h)');gax.legend(fontsize=9)
        fine=[r for r in rows if r['config']['scale']==4]
        baseline=next(r['qoi']['x_over_h'] for r in fine if r['config']['upstream_h']==5 and r['config']['downstream_h']==30)
        offsets=[(r['qoi']['x_over_h']-baseline)/ref*1e6 for r in fine]
        iterations=[r['relative_change']*r['qoi']['x_over_h']/ref*1e6 for r in fine]
        dax.bar([f"{r['config']['upstream_h']}/{r['config']['downstream_h']}" for r in fine],offsets,color='#087b79',yerr=iterations,capsize=4)
        dax.axhline(0,color='#526976',lw=.8)
        dax.set(title='Domain change, magnified',ylabel='Difference from 5/30 domain (ppm of reference)',xlabel='Inlet / outlet length (h)')
        fig.savefig(root/f'{name}-gates.svg');plt.close(fig)
        fields=['id','grid','upstream_h','downstream_h','cells','iterations','seconds','x_over_h','relative_error_percent','mass_imbalance','qoi_change_percent','valid']
        records=[]
        for r in rows:
            records.append(dict(zip(fields,[r['id'],r['config']['scale'],r['config']['upstream_h'],r['config']['downstream_h'],r['mesh']['cells'],r['qoi']['iteration'],r.get('total_attempt_seconds',r['seconds']),r['qoi']['x_over_h'],100*r['relative_error'],r['mass']['relative_imbalance'],100*r['relative_change'],r['valid']])))
        with (root/f'{name}-results.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fields);w.writeheader();w.writerows(records)
        body=''
        for r in records:
            body+='<tr>'+''.join(f'<td>{html.escape(str(v))}</td>' for v in [f"G{[1,2,4].index(r['grid'])}",f"{r['upstream_h']} / {r['downstream_h']}",f"{r['cells']:,}",r['iterations'],f"{r['x_over_h']:.6f}",f"{r['relative_error_percent']:.3f}%",f"{r['mass_imbalance']:.2e}",f"{r['seconds']:.1f}s",'有效' if r['valid'] else '未过收敛门'])+f'<td><a href="{name}/{r["id"]}/result.json">数值</a> · <a href="{name}/{r["id"]}/evidence.json">原始证据</a> · <a href="{name}/{r["id"]}/log.simpleFoam">求解历史</a></td></tr>'
        gci=''
        for g in data['groups']:
            c=g['gci'];gci+=f'<tr><td>{g["upstream_h"]}h / {g["downstream_h"]}h</td>'
            gci+=(f'<td>{c["observed_order"]:.3f}</td><td>{c["extrapolated"]:.6f}</td><td>{100*c["fine_gci"]:.3f}%</td>' if c['applicable'] else '<td colspan="3">不适用：'+html.escape(c['reason'])+'</td>')+'</tr>'
        suggested=decision['suggested_tolerance'];label=f'{suggested*100:.1f}%' if suggested is not None else '尚不能给出'
        max_gci=max((g['gci']['fine_gci'] for g in data['groups'] if g['gci']['applicable']),default=None)
        gci_label=f'{100*max_gci:.3f}%' if max_gci is not None else '不适用'
        domain_pct=100*decision['fine_domain_effect']
        domain_label=f'{domain_pct:.6f}%' if domain_pct>=1e-6 else '&lt; 0.000001%'
        continuation_note='<p class="notice">含超时后的独立续跑身份；初次失败、检查点、原始日志和完整谱系均保留。<a href="re100/analysis.json">查看初次运行</a></p>' if name=='re100-resolved' else ''
        sections.append(f'''<section data-re="{re}"><h2>Re = {re} · {data['valid_count']} / {data['case_count']} 个有效原生算例</h2>{continuation_note}
<div class="cards"><article><small>细网格最大 GCI</small><b>{gci_label}</b><p>研究门槛 ≤ {100*decision['policy']['fine_gci_max']:.1f}%</p></article><article><small>本研究建议的筛选带</small><b>{label}</b><p>原 10% 参考带保持原版本</p></article><article><small>细网格最大域差</small><b>{domain_label}</b><p>研究门槛 ≤ {100*decision['policy']['fine_domain_effect_max']:.2f}%</p></article></div>
<p class="notice">{'研究门通过，可进入相邻工况验证。' if decision['gate_passed'] else '研究门未通过：不能用此结果收紧阈值或扩大工况。'} 建议带是观测偏差、GCI、域差、迭代变化和参考舍入的保守求和，不是统计置信区间。</p>
<img src="{name}-grid.svg" alt="Re {re} 四种域的三网格再附着长度，与文献参考比较"><p>重叠曲线意味着域效应很小；精确差值见表。<a href="{name}-grid.svg">导出 SVG</a> · <a href="{name}-grid.png">导出 PNG</a> · <a href="{name}-results.csv">下载 CSV</a></p>
<img src="{name}-gates.svg" alt="四种域的 GCI 与预声明门槛比较，以及放大后的域长度差值"><p>右图用百万分比放大域差；误差棒仅标示末两保存场的变化幅度，不是置信区间。低于该变化量的域差不能解释为已分辨的物理效应。</p>
<h3>每种域的三网格估计</h3><div class="scroll"><table><thead><tr><th>入口 / 出口</th><th>观察阶数 p</th><th>Richardson 外推 x/h</th><th>细网格 GCI</th></tr></thead><tbody>{gci}</tbody></table></div><p>外推值不是原生求解结果，不纳入模型得分。三点拟合的渐近比不作为独立收敛证明；GCI 反映离散估计，不包含所有建模误差。</p>
<details><summary>展开 {len(rows)} 个算例与原生证据</summary><div class="scroll"><table><thead><tr><th>网格</th><th>入口/出口 h</th><th>单元</th><th>迭代</th><th>x/h</th><th>参考偏差</th><th>质量误差</th><th>耗时</th><th>状态</th><th>证据</th></tr></thead><tbody>{body}</tbody></table></div></details>
<details><summary>查看预声明门槛与容差组成</summary><pre>{html.escape(json.dumps(decision,ensure_ascii=False,indent=2))}</pre></details><p><a href="{name}/analysis.json">分析 JSON</a> · <a href="{name}/protocol.json">实验身份与方案</a></p></section>''')
    output='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CFD 网格与域长度敏感性 · COMACBench</title><style>
:root{color-scheme:light;--ink:#16333d;--muted:#526976;--accent:#087b79}*{box-sizing:border-box}body{margin:0;color:var(--ink);background:#f4f7f8;font:16px/1.65 -apple-system,BlinkMacSystemFont,'PingFang SC',sans-serif}main{max-width:1100px;margin:auto;padding:42px 28px}h1{font-size:34px;line-height:1.3}h2{margin-top:0}h3{margin-bottom:8px}p{color:var(--muted)}header{border-bottom:1px solid #bacbd1;padding-bottom:26px}.brand{font-size:12px;letter-spacing:2px;color:var(--accent)}nav{display:flex;gap:10px;margin:22px 0}button{font:inherit;border:1px solid #bacbd1;padding:9px 18px;border-radius:7px;background:white;color:var(--ink);cursor:pointer}button.active{background:var(--accent);color:white}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.cards article{padding:20px;border:1px solid #d5e1e5;border-radius:9px;background:white}.cards b{display:block;font-size:32px}.cards p{margin-bottom:0;font-size:13px}.notice{padding:14px;border-left:4px solid #c88a24;background:#fff6e4}section{padding:25px 0}img{width:100%;border-radius:8px;background:white}a{color:var(--accent)}table{border-collapse:collapse;width:100%;white-space:nowrap;font-size:14px}td,th{padding:10px;text-align:left;border-bottom:1px solid #d3e0e5}th{font-weight:600}.scroll{overflow:auto}details{background:white;border:1px solid #d5e1e5;padding:15px;margin:16px 0;border-radius:8px}summary{cursor:pointer;font-weight:600}pre{overflow:auto;white-space:pre-wrap;font-size:12px}footer{border-top:1px solid #bacbd1;margin-top:26px;padding-top:20px}@media(max-width:650px){main{padding:24px 16px}h1{font-size:26px}.cards{grid-template-columns:1fr}}
</style><main><header><div class="brand">COMACBENCH / NATIVE CFD STUDY</div><h1>网格再细一档，边界再远一些，<br>结果会变多少？</h1><p>先核验数值敏感性与容差，再扩展工况。每个数字都能回到真实 OpenFOAM 场与日志。</p><p>三档网格 × 入口/出口四种组合；求解残差与末段指标使用更严格门槛。这里是求解研究，没有模型排名。</p></header><nav aria-label="选择工况">'''
    output+=''.join(f'<button data-target="{d["reynolds"]}">Re = {d["reynolds"]}</button>' for _,d in analyses)+'</nav>'+''.join(sections)
    output+='''<footer><p>范围：二维层流后向台阶，公开后向台阶基础问题；不代表飞机级接受或完整论文长域复现。入口中心值离散导致微小流量积分差，该效应随网格加密变化并包含在本研究结果中。耗时为两路同时运行的墙钟，仅供本机成本观察。</p><p><a href="README.md">研究记录</a> · <a href="verification.json">复核摘要</a> · <a href="https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html">NASA 网格收敛方法</a> · <a href="https://doi.org/10.1016/j.compfluid.2007.09.003">Erturk 2008 参考来源</a></p></footer></main><script>
function select(re){document.querySelectorAll('section[data-re]').forEach(s=>s.hidden=s.dataset.re!==re);document.querySelectorAll('button[data-target]').forEach(b=>b.classList.toggle('active',b.dataset.target===re))}document.querySelectorAll('button[data-target]').forEach(b=>b.onclick=()=>select(b.dataset.target));select(document.querySelector('button[data-target]').dataset.target);
</script></html>'''
    decisions=[data['tolerance_decision'] for _,data in analyses]
    if any(not d['gate_passed'] for d in decisions):
        grid_blocked=any(g['gci']['applicable'] and g['gci']['fine_gci']>data['tolerance_decision']['policy']['fine_gci_max'] for _,data in analyses for g in data['groups'])
        headline='网格误差尚未达标' if grid_blocked else '数值研究门尚未通过'
        output=output.replace('网格再细一档，边界再远一些，<br>结果会变多少？',headline+'，<br>暂不扩展仿真工况')
    output=output.replace('耗时为两路同时运行的墙钟，仅供本机成本观察。','耗时按算例累计，含其初次运行与续跑；两路并行的耗时仅用于本机成本观察。')
    diagnostic=root/'wall-gradient-diagnostic.json'
    if diagnostic.is_file():
        diag=json.loads(diagnostic.read_text())
        selected=sorted((r for r in diag['rows'] if r['config']['upstream_h']==5 and r['config']['downstream_h']==30),key=lambda r:r['config']['scale'])
        body=''.join(f'<tr><td>G{[1,2,4].index(r["config"]["scale"])}</td><td>{r["native_x_over_h"]:.6f}</td><td>{r["quadratic_x_over_h"]:.6f}</td></tr>' for r in selected)
        extra='<h2>误差来源诊断</h2><p>同一收敛速度场，单独比较壁面导数重构。下表为 5h / 30h 域；该诊断不替换正式剪切指标，也不改变研究门槛。</p><table><thead><tr><th>网格</th><th>原生剪切 x/h</th><th>二次导数重构 x/h</th></tr></thead><tbody>'+body+'</tbody></table><p>入口中心值离散的流量偏差为 0.125% / 0.03125% / 0.00781%，也是当前网格研究的一部分。<a href="wall-gradient-diagnostic.json">诊断数据</a> · <a href="reference-check.json">参考定义核验</a></p>'
        output=output.replace('<footer>','<footer>'+extra)
    (root/'index.html').write_text(output)


if __name__=='__main__':render(sys.argv[1])
