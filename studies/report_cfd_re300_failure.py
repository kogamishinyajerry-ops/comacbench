"""Independently reproduce and report the stopped Re=300 v1 pilot.

This does not change the frozen solver, root selection, or failed case results.
"""
import argparse
import csv
import html
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
from studies.run_cfd_re300 import identity,verify_case
from studies.cfd_re300 import reduce
from studies.cfd_step_sensitivity import save,sha,inspect_mesh
from studies.cfd_fourth_grid import field_dictionary,native_qoi,inlet_check,wall_check,POLICY
from studies.reprocess_cfd_primary import geometry,read_flux,read_velocity
from studies.cfd_primary_recirculation import primary_region,match_root
from studies.cfd_zero_crossing_audit import crossings
from runners.solvers.backward_step import residuals
from runners.solvers.foam_text import field_values

SELF='studies/report_cfd_re300_failure.py'
IDS=('retention-control-u5-d30-g1','re300-u5-d30-g1')
ERROR='primary wall root not unique: 0'


def reproduce(out):
    protocol=identity(out);rows=[];visual=None;records=0
    for cid in IDS:
        work=out/cid;row,n=verify_case(out,work);records+=n
        if row['status']!='failed' or row['valid'] or row.get('error')!=ERROR:raise ValueError('unexpected pilot outcome')
        try:reduce(work,row['config'])
        except ValueError as exc:
            if str(exc)!=ERROR:raise
        else:raise ValueError('frozen reducer no longer reproduces the failure')
        case=work/'case';log=(work/'log.simpleFoam').read_text();conv=residuals(log)
        mesh,info=inspect_mesh(case,row['config'],(work/'log.checkMesh').read_text());plan=geometry(mesh)
        times=sorted(int(p.name) for p in case.iterdir() if p.is_dir() and p.name.isdecimal() and int(p.name)>0 and all((p/f).is_file() for f in ('U','p','phi','wallShearStress')))
        if len(times)<2 or times[-1]!=conv['iteration']:raise ValueError('missing convergence field pair')
        snapshots=[]
        for t in times[-2:]:
            psi,flux=read_flux(case,mesh,plan,t);labels,region=primary_region(plan['x'],plan['y'],psi)
            velocity,psi_u,first,quad=read_velocity(case,mesh,plan,t);labels_u,region_u=primary_region(plan['xc'],plan['yc'],psi_u)
            native=native_qoi(case,mesh,t);a=match_root(native['curve'],plan['x'],labels,region['label'])
            au=match_root(native['curve'],plan['xc'],labels_u,region_u['label']);fa=match_root(first,plan['xc'],labels_u,region_u['label'])
            if a['selected']['bracket_indices']!=au['selected']['bracket_indices']:raise ValueError('primary native U/phi disagreement')
            audit=crossings(quad);up=[dict(r,first_layer_component=int(labels_u[0,r['bracket_indices'][0]])) for r in audit['crossings'] if r['direction']=='negative_to_positive']
            try:match_root(quad,plan['xc'],labels_u,region_u['label'])
            except ValueError as exc:
                if str(exc)!=ERROR:raise
            else:raise ValueError('quadratic association failure not reproduced')
            if len(up)!=1 or up[0]['first_layer_component']!=0:raise ValueError('unexpected quadratic topology')
            i=up[0]['bracket_indices'][0]
            points=[{'index':k,'x_h':float(plan['xc'][k]),'first_layer_component':int(labels_u[0,k]),
                     'first_layer_u':float(velocity[0,k,0]),'quadratic_shear':float(quad[k][1])}
                    for k in range(max(0,i-2),min(len(plan['xc']),i+3))]
            q=a['selected']['x_h'];q2=up[0]['x_h']
            snapshots.append({'iteration':t,'native_primary':a,'native_U':au,'first_layer':fa,
                              'primary_region':region,'velocity_region':region_u,'flux':flux,
                              'quadratic_audit':audit,'quadratic_upcrossings':up,'nearby_samples':points,
                              'candidate_relative_gap':abs(q2-q)/q,
                              'candidate_is_validated_by_frozen_contract':False})
            visual={'x':plan['x'],'y':plan['y'],'psi':psi,'U':velocity[:,:,0],
                    'native_curve':np.asarray(native['curve']),'quadratic_curve':np.asarray(quad),'first_curve':np.asarray(first),'snapshot':snapshots[-1]}
        inlet=inlet_check(case,mesh,times[-1]);wall=wall_check(case,mesh,times[-1]);final=conv['final']
        data=field_dictionary(case/str(times[-1])/'phi')
        fluxes={p:sum(field_values(data['boundaryField'][p]['value'],len(ids))) for p,ids in mesh['ranges'].items() if p!='frontAndBack'}
        mass=abs(sum(fluxes.values()))/abs(fluxes['inlet'])
        leak=(abs(fluxes['lowerWall'])+abs(fluxes['upperWall']))/abs(fluxes['inlet'])
        change=abs(snapshots[-1]['native_primary']['selected']['x_h']-snapshots[-2]['native_primary']['selected']['x_h'])/snapshots[-1]['native_primary']['selected']['x_h']
        checks={'native_converged':f"SIMPLE solution converged in {conv['iteration']} iterations" in log and '\nEnd\n' in log,
                'residuals':final['p']<=POLICY['p_residual_max'] and max(final['Ux'],final['Uy'])<=POLICY['U_residual_max'],
                'native_steps':[(s['stage'],s['exit']) for s in row['steps']]==[(s,0) for s in ('blockMesh','checkMesh','mapFields','simpleFoam')],
                'primary_interval_stable':snapshots[-1]['native_primary']['selected']['bracket_indices']==snapshots[-2]['native_primary']['selected']['bracket_indices'],
                'primary_qoi_stable':change<=POLICY['qoi_change_max'],'mass':mass<=POLICY['mass_imbalance_max'] and leak<1e-8,
                'inlet':inlet['passed'],'wall_boundary':wall['passed']}
        if not all(checks.values()):raise ValueError('additional native/identity failure: '+str(checks))
        rows.append({'id':cid,'result_sha256':sha(work/'result.json'),'native_checks':checks,'convergence':conv['final'],
                     'saved_times':times,'snapshots':snapshots,'relative_primary_change':change,'mesh':info,
                     'inlet':inlet,'wall_boundary_passed':wall['passed'],'mass_relative_imbalance':mass,'wall_leak':leak,
                     'frozen_reduction_reproduced':ERROR})
    a,b=rows
    if a['saved_times'][-2:]!=b['saved_times']:raise ValueError('rolling retained pair differs')
    pair=[]
    for t in b['saved_times']:
        for f in ('U','p','phi','wallShearStress'):
            left=out/IDS[0]/'case'/str(t)/f;right=out/IDS[1]/'case'/str(t)/f
            if field_dictionary(left)!=field_dictionary(right):raise ValueError('native retention field changed')
            pair.append({'iteration':t,'field':f,'control_sha256':sha(left),'rolling_sha256':sha(right),'parsed_fields_equal':True})
    started=[cid for cid in protocol['matrix'] if (out/cid).exists()]
    if started!=[IDS[1]]:raise ValueError('matrix continued past the pilot stop gate')
    return {'study_gate_passed':False,'status':'stopped_at_frozen_quadratic_wall_association','identity_sha256':sha(out/'protocol.json'),
            'failure_verifier_sha256':sha(ROOT/SELF),'native_records_verified':records,'source_files_verified':len(protocol['source_hashes']),
            'parent_manifest_counts':[len(json.loads(Path(r['path']).read_text())['files']) for r in protocol['parent_manifests']],
            'native_runs_completed':2,'matrix_runs_started':1,'matrix_runs_valid':0,'matrix_runs_not_started':15,
            'retention_fields_equal':True,'retention_gate_passed':False,'paired_fields':pair,'cases':rows,
            'current_benchmark_tolerance':.1,'screening_tolerance_candidate':None,'expanded_re400':False,
            'feedback':[{'code':'QUADRATIC_ROOT_LABEL_MISMATCH','stage':'near-wall diagnostic association',
                         'evidence':'native bracket [65,66]; quadratic bracket [66,67]; U is positive but quadratic wall shear is negative at index 66',
                         'action':'Define diagnostic-branch correspondence separately from primary-eddy identity under a new protocol; replay both saved pilots and the Re=200 fields before restarting the remaining matrix.'}]},visual


def figures(out,v):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
    s=v['snapshot'];q=s['native_primary']['selected']['x_h'];q2=s['quadratic_upcrossings'][0]['x_h']
    fig,ax=plt.subplots(1,2,figsize=(12,4),layout='constrained')
    z=ax[0].pcolormesh(v['x'],v['y'],v['U'],cmap='RdBu_r',vmin=-.2,vmax=1.4,rasterized=True)
    ax[0].contour(v['x'],v['y'],v['psi'],levels=[0],colors='#23383c',linewidths=.8)
    for c in s['primary_region']['contours']:
        line=np.asarray(c['xy_h']);ax[0].plot(line[:,0],line[:,1],'w-',lw=1)
    ax[0].plot(*s['primary_region']['centre_xy_h'],'wo',ms=4);ax[0].plot(q,0,'o',color='#bf732a',clip_on=False)
    ax[0].set(xlim=(0,8.5),ylim=(0,2),xlabel='x / h',ylabel='y / h',title='Primary eddy identified by native phi and U')
    fig.colorbar(z,ax=ax[0],label='u / Umean',shrink=.7)
    for key,label,color in [('native_curve','Native shear','#166e70'),('quadratic_curve','Quadratic gradient','#bf732a')]:
        c=v[key];ax[1].plot(c[:,0],c[:,1],label=label,color=color)
    ax[1].axhline(0,color='#888',lw=.7);ax[1].set(xlabel='x / h',ylabel='Kinematic wall shear (m2/s2)',title='Complete downstream wall');ax[1].legend()
    fig.suptitle('Re=300 | G0 | Lu=5h, Ld=30h | native iteration 1855')
    fig.savefig(out/'pilot-primary.png',dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4),layout='constrained')
    for key,label,color in [('native_curve','Native shear','#166e70'),('first_curve','First-cell gradient','#555'),('quadratic_curve','Quadratic gradient','#bf732a')]:
        c=v[key];ax.plot(c[:,0],c[:,1],'.-',label=label,color=color)
    ax.axvspan(6.5,6.6,alpha=.08,color='#166e70',label='Last first-layer reverse-flow cell')
    ax.axhline(0,color='#888',lw=.7);ax.plot([q,q2],[0,0],'o',color='#bf732a')
    ax.annotate(f'Native {q:.6f}',(q,0),xytext=(6.40,.00125),arrowprops={'arrowstyle':'->','color':'#555'})
    ax.annotate(f'Quadratic candidate {q2:.6f}',(q2,0),xytext=(6.69,-.00125),arrowprops={'arrowstyle':'->','color':'#555'})
    ax.set(xlim=(6.35,6.93),ylim=(-.0026,.0022),xlabel='x / h',ylabel='Kinematic wall shear (m2/s2)',title='Different gradient estimates straddle different sampling intervals')
    ax.legend(fontsize=8,loc='upper left');ax.grid(alpha=.12);fig.savefig(out/'wall-association.svg');plt.close(fig)


def report(out,analysis,v):
    s=analysis['cases'][-1]['snapshots'][-1];q=s['native_primary']['selected']['x_h'];q2=s['quadratic_upcrossings'][0]['x_h']
    protocol=json.loads((out/'protocol.json').read_text())
    with (out/'results.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['case','matrix_member','status','native_iteration','diagnostic_native_x1_h','quadratic_candidate_x1_h','benchmark_valid','feedback'])
        for cid in [IDS[0]]+protocol['matrix']:
            started=cid in IDS
            w.writerow([cid,cid!=IDS[0],'stopped_diagnostic' if started else 'not_started',1855 if started else '',q if started else '',q2 if started else '',False,ERROR if started else 'pilot gate not passed'])
    figures(out,v)
    rows=''.join(f"<tr><td>{html.escape(cid)}</td><td>{'原生收敛；诊断契约失败' if cid==IDS[1] else '未开始：前置门槛未通过'}</td></tr>" for cid in protocol['matrix'])
    doc=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Re=300 验证暂停 · COMACBench</title><style>*{{box-sizing:border-box}}body{{margin:0;background:#f3f4ef;color:#24383d;font:16px/1.7 -apple-system,"PingFang SC",sans-serif}}main{{max-width:1150px;margin:auto;padding:32px}}section,.card{{padding:22px;background:white;border:1px solid #dbe2db;border-radius:10px;margin:18px 0}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}.card strong{{display:block;color:#a3642b;font-size:28px}}.notice{{border-left:5px solid #b67231}}a{{color:#166e70}}h1{{line-height:1.3}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{text-align:left;border-bottom:1px solid #ddd;padding:9px}}img{{width:100%;height:auto}}code{{overflow-wrap:anywhere}}@media(max-width:700px){{main{{padding:16px}}.cards{{grid-template-columns:1fr 1fr}}}}</style><main><p>COMACBENCH / CFD / Re=300 v1</p><h1>验证已暂停：粗网格近壁诊断契约不适用</h1><p>四档网格 × 四种域已冻结；首组对照试验触发停止条件，后续 15 组尚未运行。本页展示真实保存场的失败复核，不能作为 Re=300 评分通过或容差标定结果。</p><div class="cards"><div class="card"><strong>2</strong>原生求解收敛（含对照）</div><div class="card"><strong>0/16</strong>矩阵有效</div><div class="card"><strong>8/8</strong>配对字段完全一致</div><div class="card"><strong>15</strong>未启动算例</div></div><section class="notice"><h2>问题在哪里</h2><p>主涡可由两条独立路径识别，原生壁面再附着点为 <b>{q:.6f}h</b>。二次近壁梯度的唯一上穿零点候选为 <b>{q2:.6f}h</b>，相差 <b>{s['candidate_relative_gap']*100:.4f}%</b>。</p><p>原生零点位于 [6.55,6.65]h；二次估计位于 [6.65,6.75]h。在 6.65h 处，第一层速度为正，而二次壁面梯度为负。旧规则要求二次零点负侧采样点仍具有第一层主负流区标签，因此产生 <code>{ERROR}</code>。它把近壁估计之间的离散差异与主涡归属失败绑定了。</p><p>这是粗网格诊断的契约问题。此处 0.4629% 是估计差异，尚未通过冻结规则的归属校验；不能用它直接宣布近壁验证通过。</p></section><section><h2>保存的场证明了什么</h2><img src="pilot-primary.png" alt="真实 Re=300 粗网格场的主涡闭合流线及完整壁面剪切曲线"><p>主涡身份在第 1800、1855 步均唯一且稳定；原生 phi 和独立 U 积分对应同一壁面区间，三条内部流线闭合。白线为内部闭合流线，黑线为零流函数。</p><img src="wall-association.svg" alt="原生再附着点和二次梯度零点跨越相邻采样区间的证据"><p>两次求解都在 1855 步收敛；残差、守恒、入口和壁面边界检查通过。purgeWrite 0 与 2 的末两次 U、p、phi、wallShearStress 共 8 项逐项相同，保存策略没有造成该差异。</p></section><section><h2>本阶段决策</h2><p>保持冻结 v1 失败状态，候选容差为空，公开评分容差仍为 10%。不启动其余矩阵，也未扩展 Re=400。</p><p>下一步应以新身份单独修正近壁诊断对应关系：保持基于 phi/U、台阶连通和闭合流线的主涡识别；为二次梯度定义可检验的负剪切分支对应规则，显式处理跨采样区间、多个分支及零平台。先复核这两组场和 Re=200 已保存场，再重新放行矩阵。</p><p><a href="failure-analysis.json">独立失败复核 JSON</a> · <a href="results.csv">矩阵与对照 CSV</a> · <a href="README.md">复核命令与完整边界</a> · <a href="execution.log">原执行日志</a></p></section><section><h2>16 组矩阵的真实状态</h2><table><thead><tr><th>算例</th><th>状态</th></tr></thead><tbody>{rows}</tbody></table></section><section><h2>协议和证据</h2><p>二维稳态层流，扩张比 2，Re=Umean·2h/nu=300。四域为上游 5/10h × 下游 30/60h。参考论文 Table 5 的 6.751 仅用于研究设计，本次未形成全矩阵误差或容差结论。</p><p><a href="protocol.json">冻结协议</a> · <a href="parent-verification.json">父阶段复核</a> · <a href="retention-control-u5-d30-g1/result.json">对照结果</a> · <a href="re300-u5-d30-g1/result.json">矩阵首例结果</a> · <a href="https://doi.org/10.1016/j.compfluid.2007.09.003">参考论文</a></p></section></main></html>'''
    (out/'index.html').write_text(doc)
    (out/'README.md').write_text(f'''# Re=300 v1：已按协议停止

四网格四域矩阵未完成：运行了首个矩阵算例和保存策略对照，共 2 次原生 SIMPLE；均在 1855 步收敛，但冻结的二次近壁梯度归属检查均失败。0/16 矩阵有效，15 组未启动。没有新模型调用。

## 复核结论

- 原生主涡 X1/h={q:.12f}；二次梯度唯一上穿候选={q2:.12f}，两者跨一个采样区间，差异 {s['candidate_relative_gap']*100:.6f}%。候选未通过冻结归属规则。
- 原生及第一层零点区间 [65,66]；二次梯度区间 [66,67]。x/h=6.65 时第一层 U 为正、二次梯度为负，因此旧标签匹配返回 0 个匹配。
- 两个末次时刻 1800/1855 的主涡均由独立 phi/U 路径识别，闭合流线、残差、入口、壁面边界、守恒检查通过。
- 两次保存策略配对的 8 个字段解析值完全相同，0 策略保留 19 个正时刻，2 策略保留 2 个。保存策略字段对照通过；整体冻结前置门槛仍失败，不能用字段一致替代近壁检查。
- 当前来源检查覆盖 {analysis['native_records_verified']} 个新原生文件、{analysis['source_files_verified']} 个冻结源文件，以及旧两份交付清单（340 / 105 项）。
- 全矩阵 GCI、域敏感性、候选容差均未形成；公开评分 10% 未改，未扩展 Re=400。数据仅为二维稳态层流诊断，不能代表三维非定常工业工况验收。

## 可复核命令

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python studies/report_cfd_re300_failure.py verify --out report/2026-09-08-cfd-re300
```

第一项本轮 123 项通过；第二项应 exit 0，含源码和原生 hash、两次原生/主涡检查、8 项保存场一致、冻结失败重现与“未启动后续矩阵”检查。exit 0 表示失败证据可复现，**不表示 Re=300 研究通过**。

原执行命令 `studies/run_cfd_re300.py run --out report/2026-09-08-cfd-re300` 已 exit 1；保留完整 `execution.log`。本轮原 `verify` 也会拒绝冻结前置门槛，不应在同一身份下覆盖失败结果重跑。

## 后续小步修复的边界

保持主涡、原生壁面指标、参考值、求解参数与数值阈值。以新协议身份定义二次近壁诊断的分支对应关系，不能直接用第一层 U 的符号标签代替二次梯度符号。

新增验收应包含：原生/二次零点跨采样区间的本次反例；角区与多个上穿零点；零平台、无闭合主涡、缺失字段；跨两次保存时刻的分支稳定性。先对两组 Re=300 保存场及原 Re=200 16 组/32 场独立复核，确认主涡和原生 QoI 均不改变，再重启未运行矩阵。不得按距参考值最近、全壁面首个零点或放宽误差阈值选择候选。

## 文件

- `protocol.json` / `frozen-source/`：原运行身份，保持不变。
- 两个算例的 `result.json` / `evidence.json` / `case/`：原失败及原生证据，保持不变。
- `failure-analysis.json`：独立失败核验，候选与原评分有效性分离。
- `failure-source.json` / `failure-frozen-source/`：报告复核器的独立身份。
- `results.csv`：16 个矩阵位置与 1 个对照；未运行位置明确为空。
- `pilot-primary.png` / `wall-association.svg`：由保存场生成的主涡与差异图。
''')


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['build','verify']);p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve()
    source={'identity':'comacbench.cfd-re300-failure-audit.v1','files':{SELF:sha(ROOT/SELF)}}
    if a.command=='build':
        if (out/'failure-source.json').exists():raise ValueError('failure delivery already exists')
        analysis,v=reproduce(out);analysis=json.loads(json.dumps(analysis))
        frozen=out/'failure-frozen-source'/SELF;frozen.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/SELF,frozen)
        save(out/'failure-source.json',source);save(out/'failure-analysis.json',analysis);report(out,analysis,v)
    else:
        if json.loads((out/'failure-source.json').read_text())!=source or sha(out/'failure-frozen-source'/SELF)!=source['files'][SELF]:raise ValueError('failure verifier drift')
        analysis,_=reproduce(out)
        if json.loads((out/'failure-analysis.json').read_text())!=json.loads(json.dumps(analysis)):raise ValueError('failure analysis drift')
    print(json.dumps({'failure_reproduced':True,'study_gate_passed':False,'native_runs':2,'matrix_valid':0,'matrix_not_started':15,'native_records_verified':analysis['native_records_verified']}),flush=True)


if __name__=='__main__':main()
