"""Offline engineering readout from verified fourth-grid study data."""
import csv
import html
import json
import math
import os
from pathlib import Path
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def gci_percent(value):
    if not value.get('applicable'):
        return math.nan
    number=value.get('fine_gci')
    return number*100 if isinstance(number,(int,float)) and math.isfinite(number) else math.nan


def percent_label(value,places=4):
    if not math.isfinite(value):return '不适用'
    if value and abs(value)<10**(-places):return f'{value:.3e}%'
    return f'{value:.{places}f}%'


def render(root):
    root=Path(root).resolve();data=json.loads((root/'analysis.json').read_text());rows=data['rows'];groups=data['groups']
    reynolds=data['reynolds'];reference={100:2.922,200:4.982}[reynolds]
    spec_name='cfd-re200-v1.md' if reynolds==200 else 'cfd-fourth-grid-v1.md'
    diagnostic='';has_zero_audit=(root/'zero-crossing-audit.json').exists()
    if has_zero_audit:
        audit=json.loads((root/'zero-crossing-audit.json').read_text())
        flagged=[r for r in audit['rows'] if r['ambiguous_for_first_upcrossing_rule']]
        if flagged:
            example=flagged[0];locations='、'.join(f"{r['x_h']:.6f}h" for r in example['crossings'] if r['direction']=='negative_to_positive')
            diagnostic=f'<section><h2>为何收敛了仍未通过</h2><p>已标注 {len(flagged)} 个算例的零点归属问题。示例包含 {locations} 等负→正剪切零点，冻结规则选中 {example["frozen_selected_x_h"]:.6f}h。首次符号翻转不能保证对应主再附着位置；角部小幅翻转的物理意义尚未核实。</p><img src="zero-crossing-audit.svg" alt="完整壁面剪切、角部微小符号翻转与下游零点的局部放大"><p>本轮 QoI 和未通过判定保留；诊断没有按参考值重新选点。<a href="zero-crossing-audit.html">查看全部零点和逐项反馈</a> · <a href="zero-crossing-audit.json">审计 JSON</a> · <a href="qoi-contract-finding.md">参考要求核验与修订建议</a></p></section>'
    curve_title='冻结零点规则在四档网格上的结果' if diagnostic else '四档加密后的再附着位置'
    evidence_root='' if reynolds==100 else os.path.relpath(Path(data['parent_verified']['path']),root)+'/'
    version=json.loads((root/'protocol.json').read_text()).get('execution_version',1)
    relax={1:'p=0.3、U=0.7',2:'p=0.7、U=0.95',3:'p=0.05、U=0.95'}[version]
    plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','font.size':10})
    colors=['#116e6a','#587ccc','#bd7b22','#9760a6']
    fig,ax=plt.subplots(figsize=(9,3.7),layout='constrained')
    for c,g in zip(colors,groups):
        rs=sorted([r for r in rows if r['config']['upstream_h']==g['upstream_h'] and r['config']['downstream_h']==g['downstream_h']],key=lambda r:r['config']['scale'])
        ax.plot([r['config']['scale'] for r in rs],[r['qoi']['x_over_h'] for r in rs],'-o',color=c,label=f"Lu={g['upstream_h']}h, Ld={g['downstream_h']}h",alpha=.8)
    ax.axhline(reference,ls='--',color='#b44a38',label=f'Published reference {reference}')
    ax.set(xscale='log',xlabel='Refinement scale (each step halves in-plane spacing)',ylabel='Frozen-rule first upcrossing x / h' if diagnostic else 'Reattachment x / h',xticks=[1,2,4,8],xticklabels=['G0 / 1','G1 / 2','G2 / 4','G3 / 8'])
    ax.minorticks_off()
    ax.grid(alpha=.15);ax.legend(fontsize=8,ncol=3,loc='lower left' if diagnostic else 'lower right');fig.savefig(root/'four-grids.svg');fig.savefig(root/'four-grids.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(11,3.2),layout='constrained')
    labels=[f"{g['upstream_h']} / {g['downstream_h']}" for g in groups]
    values=[gci_percent(g['gci']) for g in groups]
    axes[0].bar(labels,values,color=['#ba573f' if v>.5 else '#116e6a' for v in values]);axes[0].axhline(.5,ls='--',color='#222');axes[0].set(title='Finest-three GCI (%)',xlabel='Lu/h / Ld/h')
    axes[0].set_xlim(-.5,len(labels)-.5)
    axes[0].set_ylim(0,max(.55,max((v for v in values if math.isfinite(v)),default=0)*1.15))
    for i,value in enumerate(values):
        if not math.isfinite(value):axes[0].text(i,.025,'N/A',ha='center',color='#ba573f')
    first=sorted([r for r in rows if r['config']['upstream_h']==5 and r['config']['downstream_h']==30],key=lambda r:r['config']['scale'])
    axes[1].plot(range(4),[r['inlet']['relative_bias']*100 for r in first],'-o',color='#116e6a');axes[1].axhline(.01,ls='--',color='#222');axes[1].set(title='Inlet flux bias (%)',xticks=range(4),xticklabels=['G0','G1','G2','G3'],yscale='log')
    axes[2].plot(range(4),[r['wall']['relative_native_gap']*100 for r in first],'-o',color='#587ccc');axes[2].axhline(.1,ls='--',color='#222');axes[2].set(title='Independent wall gap (%)',xticks=range(4),xticklabels=['G0','G1','G2','G3'])
    for ax in axes:ax.grid(axis='y',alpha=.15)
    fig.savefig(root/'independent-checks.svg');fig.savefig(root/'independent-checks.png',dpi=180);plt.close(fig)
    fields=['case','Lu_h','Ld_h','grid','cells','x_h','inlet_bias_pct','effective_Re','wall_gap_pct','valid']
    with (root/'results.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(fields)
        for r in rows:
            c=r['config'];writer.writerow([r['id'],c['upstream_h'],c['downstream_h'],c['scale'],c['expected_cells'],r['qoi']['x_over_h'],r['inlet']['relative_bias']*100,r['inlet']['effective_reynolds'],r['wall']['relative_native_gap']*100,r['valid']])
    passed=data['gate_passed'];worst=max(values) if all(math.isfinite(v) for v in values) else math.nan;fine=[r for r in rows if r['config']['scale']==8]
    title='Re=100 已过门，可以开展 Re=200 研究' if passed else '第四档已核验，Re=200 仍受门槛约束'
    if reynolds==200:title='Re=200 敏感性研究已通过' if passed else 'Re=200 已完成计算，仍有未通过项'
    subtitle='四档网格、四组域长度；入口流量和近壁处理独立交叉核验。步高 h=10 mm，Re 按名义平均入口速度 1 m/s 和 2h 定义，实际积分偏差单独列出。'
    gate_labels={'native validity / completeness':'原生结果有效性或矩阵完整性','finest-three grid GCI > 0.5% or inapplicable':'最细三档 GCI 超过 0.5% 或不适用','domain sensitivity':'域长度敏感性','inlet / wall independent checks':'入口或近壁独立检查','linear solver bridge':'线性求解器桥接','face-average paired diagnostic invalid':'入口面平均配对诊断无效'}
    if all(not g['gci'].get('applicable') for g in groups):
        gate_labels['finest-three grid GCI > 0.5% or inapplicable']='最细三档 GCI 不适用'
    if all(r['inlet']['passed'] and r.get('geometric_inlet',{}).get('passed',False) for r in rows) and all(abs(r['inlet']['relative_bias'])<=data['policy']['fine_inlet_bias_max'] for r in fine):
        gate_labels['inlet / wall independent checks']='近壁零点差异超限或未随加密下降'
    reason='全部预声明门槛通过。' if passed else '未通过项：'+html.escape('；'.join(gate_labels.get(k,k) for k in data['failed_gates']))+'。'
    summary_rows=''
    for g in groups:
        value=gci_percent(g['gci']);order=g['gci'].get('observed_order')
        order_text=f'{order:.3f}' if isinstance(order,(int,float)) and math.isfinite(order) else '不适用'
        outcome='通过' if math.isfinite(value) and value<=.5 else '未通过'
        if not math.isfinite(value):outcome+='：'+html.escape(str(g['gci'].get('reason','GCI 不适用')))
        summary_rows+=f"<tr><td>{g['upstream_h']}h / {g['downstream_h']}h</td><td>{percent_label(gci_percent(g['old_gci']))}</td><td>{percent_label(value)}</td><td>{order_text}</td><td>{outcome}</td></tr>"
    detail=''
    for r in rows:
        c=r['config'];link=os.path.relpath(Path(r['artifact_path']),root)
        detail+=f"<tr><td>{c['upstream_h']} / {c['downstream_h']}</td><td>G{[1,2,4,8].index(c['scale'])}</td><td>{c['expected_cells']:,}</td><td>{r['qoi']['x_over_h']:.8f}</td><td>{r['inlet']['effective_reynolds']:.7f}</td><td>{r['wall']['relative_native_gap']*100:.5f}%</td><td>{'有效' if r['valid'] else '无效'}</td><td><a href='{link}/result.json'>结果</a> · <a href='{link}/evidence.json'>证据</a> · <a href='{link}/log.simpleFoam'>原生日志</a></td></tr>"
    inlet_fine=max(abs(r['inlet']['relative_bias']) for r in fine)*100;wall_fine=max(r['wall']['relative_native_gap'] for r in fine)*100
    if reynolds==100:
        pair=data['inlet_pair'];baseline=next(r for r in rows if r['config']['scale']==4 and r['config']['upstream_h']==5 and r['config']['downstream_h']==30)
        pair_delta=abs(pair['qoi']['x_over_h']-baseline['qoi']['x_over_h'])/baseline['qoi']['x_over_h']*100
        pair_text=f'配对算例将 G2 改为精确面平均入口，再附着位置相对原算例变化 {pair_delta:.6f}%。该算例仅用于诊断，没有混入原网格族。'
    else:
        pair_text='Re=100 的精确面平均配对诊断已在前置研究中核验。本组 Re=200 保持面中心入口定义，逐项重做实际面积、速度积分和原生通量检查。'
    followup=''
    if (root/'followup.json').exists():
        follow=json.loads((root/'followup.json').read_text());link=html.escape(os.path.relpath(Path(follow['path'])/'index.html',root),quote=True)
        followup=f'<p><a href="{link}">查看 Re=200 扩展研究</a>：{html.escape(follow["status"])}。Re=100 判定快照保持原样。</p>'
    candidate=data.get('screening_tolerance_candidate')
    tolerance_text=(f"本次筛查容差候选为 ±{candidate['relative_band']*100:g}%，采用预声明的保守误差项求和规则。它不是统计置信区间，尚未写入 benchmark 评分。" if passed and candidate else '当前证据尚不足以发布校准容差；保留既有评分，继续标注其 10% 容差未经本研究校准。')
    doc=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Re={reynolds} 四档网格独立核验</title>
<style>*{{box-sizing:border-box}}body{{margin:0;background:#f4f3ee;color:#253235;font:16px/1.6 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}}main{{max-width:1140px;margin:auto;padding:42px 28px 70px}}header p{{max-width:820px}}h1{{font-size:34px;line-height:1.3;margin:12px 0}}h2{{font-size:22px;margin-top:0}}.eyebrow{{color:#116e6a;font-size:13px;letter-spacing:2px}}.status{{border-left:5px solid {'#116e6a' if passed else '#ba573f'};padding:15px 20px;background:white;margin:22px 0}}.metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}.metric,section{{background:white;border:1px solid #dedfd6;border-radius:12px;padding:22px}}.metric strong{{display:block;font-size:26px;margin:5px 0}}.metric span,small{{color:#667476;font-size:13px}}section{{margin:20px 0}}img{{width:100%;height:auto}}.explain{{color:#59686b}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{text-align:left;padding:11px 9px;border-bottom:1px solid #e3e7e5;white-space:nowrap}}th{{background:#f3f7f5}}.table{{overflow:auto}}a{{color:#0c706c}}.steps{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}}.steps b{{display:block}}details summary{{cursor:pointer;font-weight:600}}footer{{font-size:13px;color:#667476}}@media(max-width:760px){{main{{padding:24px 16px}}h1{{font-size:27px}}.metrics{{grid-template-columns:repeat(2,1fr)}}.steps{{grid-template-columns:1fr}}section{{padding:16px}}}}</style>
<main><header><div class="eyebrow">COMACBENCH / 原生 CFD 证据 / 第四档研究</div><h1>{title}</h1><p>{subtitle}</p><div class="status">{reason}<br>入口、近壁检查与网格 GCI 各自判定；现有 benchmark 的 10% 容差尚未改动。{followup}</div></header>
<div class="metrics"><div class="metric"><span>最细三档网格误差估计</span><strong>{percent_label(worst)}</strong><small>最大 GCI，门槛 ≤ 0.5%</small></div><div class="metric"><span>第四档最大入口偏差</span><strong>{inlet_fine:.6f}%</strong><small>门槛 ≤ 0.01%</small></div><div class="metric"><span>第四档最大近壁差异</span><strong>{wall_fine:.5f}%</strong><small>门槛 ≤ 0.1%，随加密下降</small></div><div class="metric"><span>所选零点的域长度影响</span><strong>{percent_label(data['fine_domain_effect']*100,7)}</strong><small>门槛 ≤ 0.25%</small></div></div>
<section><h2>先读这个结果</h2><div class="steps"><div><b>① 网格是否够细</b>增加 G3 后，用 G1、G2、G3 重算离散不确定度；保留 G0、G1、G2 供比较。</div><div><b>② 输入是否一致</b>从实际网格面独立积分，并与原生通量比较。公开标出面中心采样带来的有效 Re 偏差。</div><div><b>③ 近壁是否可信</b>检查层流、无滑移、二维边界和实际壁距，再用二次速度梯度交叉核验零点。</div></div></section>
{diagnostic}<section><h2>{curve_title}</h2><p class="explain">四条域长度曲线非常接近。靠近论文参考线不等于通过网格误差门槛。</p><img src="four-grids.svg" alt="四档网格在四组域长度下的再附着位置，与论文参考值比较"><div class="table"><table><thead><tr><th>上游 / 下游域长</th><th>原三档 GCI</th><th>最细三档 GCI</th><th>新观察阶 p</th><th>网格门槛</th></tr></thead><tbody>{summary_rows}</tbody></table></div></section>
<section><h2>入口和近壁：独立检查什么</h2><img src="independent-checks.svg" alt="最细三档GCI、入口流量积分偏差与近壁独立重构差异及各自门槛"><p>入口面中心采样偏差依次为 0.125%、0.03125%、0.0078125%、0.001953125%。{pair_text}</p><p>壁面使用层流无滑移条件；二次重构采用实际不等壁距。它与原生张量剪切并非同一定义，差值予以保留；正式 QoI 始终采用原生壁面剪切零点。</p><p>Re=100 前置核验：<a href="{evidence_root}prior-independent-checks.json">原三档独立检查</a> · <a href="{evidence_root}inlet-face-average-u5-d30-g4/result.json">入口配对结果</a> · <a href="{evidence_root}bridge-u5-d30/result.json">短域桥接</a> · <a href="{evidence_root}bridge-u5-d60/result.json">长域桥接</a></p></section>
<section><details><summary>展开 16 个算例和原生证据</summary><div class="table"><table><thead><tr><th>Lu / Ld</th><th>网格</th><th>单元数</th><th>x/h</th><th>流量有效 Re</th><th>近壁差异</th><th>原生有效性</th><th>核验材料</th></tr></thead><tbody>{detail}</tbody></table></div></details></section>
<section><h2>复跑与使用边界</h2><p>新增算例从已保存的原生场映射初始化，GAMG 使用 DICGaussSeidel，最终松弛系数为 {relax}；来源、网格及两组桥接验证保留。新算例采用更严的绝对残差与末两场稳定性门槛。</p><p>第四档采用 4 个 MPI 分区，数值设置保持一致。Re=100 短域与长域均通过同网格桥接；本组结果逐项核对重构后的单元速度、压力和底壁剪切。<a href="{evidence_root}mpi-verification.json">MPI 桥接核验</a> · <a href="{evidence_root}mpi-reconstruction-check.json">桥接分区重构核验</a> · <a href="{evidence_root}mpi-speed-check.json">单次 100 步计时</a>（计时仅代表该次测量）。</p><p>发散、收敛但未通过桥接及中止的探索尝试均保留，未进入正式网格结果。入口面积另用多边形面积向量与高斯积分交叉验证。</p><p>{tolerance_text}</p><p>这里验证二维层流后向台阶及 benchmark 的证据链。结果不能直接代表飞机工业工况验收、商业求解器能力或模型排名。</p><p><a href="analysis.json">完整机器可读判定</a> · <a href="results.csv">下载数值 CSV</a> · <a href="protocol.json">冻结协议</a> · <a href="frozen-source/docs/specs/{spec_name}">事前门槛说明</a></p></section>
<footer>方法依据：<a href="https://doi.org/10.1016/j.compfluid.2007.09.003">Erturk 2008，Table 5</a> · <a href="https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html">NASA GCI</a> · <a href="https://doc.cfd.direct/openfoam/user-guide-v10/fvsolution">OpenFOAM 10 求解器控制</a> · <a href="https://cpp.openfoam.org/v10/wallShearStress_8C_source.html">原生壁面剪切实现</a><br>本页由本地真实求解结果生成，新增模型调用为 0；既有评分和历史证据保留。</footer></main></html>'''
    (root/'index.html').write_text(doc)
    print(root/'index.html')

if __name__=='__main__':render(sys.argv[1])
