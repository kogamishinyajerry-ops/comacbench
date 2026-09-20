"""Live local readout during the active native study; stops on final analysis."""
import html,json,os,re,sys,time
from pathlib import Path


def snapshot(root):
    protocol=json.loads((root/'protocol.json').read_text());reynolds=protocol['reynolds']
    scales=(1,2,4,8) if reynolds==200 else (8,)
    rows=[]
    for u,d,scale in [(u,d,s) for u,d in [(5,30),(10,30),(5,60),(10,60)] for s in scales]:
        work=root/f're{reynolds}-u{u}-d{d}-g{scale}';entry={'case':work.name,'cells':(5*u+2*(140+(33 if d==60 else 0)))*20*scale**2,'status':'网格与初场准备' if work.exists() else '等待求解槽位','iteration':None,'residuals':{}}
        log=work/'log.simpleFoam'
        if log.exists():
            chunks=re.split(r'Time = (\d+)s\n',log.read_text())
            if len(chunks)>2:
                index=-2 if 'ClockTime' in chunks[-1] else -4
                if abs(index)<=len(chunks):entry.update(status='原生求解中',iteration=int(chunks[index]),residuals={k:float(v) for k,v in re.findall(r'Solving for (Ux|Uy|p), Initial residual = ([^,]+)',chunks[index+1])})
        if (work/'result.json').exists():
            r=json.loads((work/'result.json').read_text());entry.update(status='已收敛且有效' if r['valid'] else '未通过 / 保留证据')
        rows.append(entry)
    return rows


def main():
    root=Path(sys.argv[1]).resolve();protocol=json.loads((root/'protocol.json').read_text());reynolds=protocol['reynolds']
    title='Re=100 第四档网格正在计算' if reynolds==100 else 'Re=200 四档网格敏感性研究正在计算'
    notice='Re=200 尚未启动。最终判断等待原生收敛、入口流量、近壁处理和网格 GCI 全部核验。' if reynolds==100 else 'Re=100 的完整证据已重新核验通过。当前扩展仍须独立完成原生收敛、入口、近壁和 GCI 检查。'
    evidence='<a href="prior-independent-checks.json">旧三档独立核验</a> · <a href="study-tests.log">专项目标测试</a>'
    if reynolds==200:
        parent=os.path.relpath(protocol['parent_verified']['path'],root)
        evidence=f'<a href="{parent}/index.html">Re=100 前置研究</a> · <a href="{parent}/analysis.json">放行依据</a> · <a href="frozen-source/docs/specs/cfd-re200-v1.md">Re=200 协议</a>'
    while not (root/'analysis.json').exists():
        rows=snapshot(root);table=''
        diagnostic=''
        if (root/'diagnostic-notice.json').exists():
            note=json.loads((root/'diagnostic-notice.json').read_text())
            diagnostic=f'<p class="notice">{html.escape(note["message"])} <a href="{html.escape(note["link"],quote=True)}">查看判据审计与局部放大图</a></p>'
        for r in rows:
            res=r['residuals'];p=f"{res['p']:.3e}" if 'p' in res else '—';u=f"{max(res.get('Ux',0),res.get('Uy',0)):.3e}" if res else '—'
            link=f"<a href='{r['case']}/log.simpleFoam'>原生日志</a>" if (root/r['case']/'log.simpleFoam').exists() else '待启动'
            match=re.fullmatch(r're\d+-u(\d+)-d(\d+)-g(\d+)',r['case']);up,down,scale=map(int,match.groups())
            label=f"G{(1,2,4,8).index(scale)} · {up}h / {down}h"
            table+=f"<tr><td title='{r['case']}'>{label}</td><td>{r['cells']:,}</td><td>{r['status']}</td><td>{r['iteration'] or '—'}</td><td>{p}</td><td>{u}</td><td>{link}</td></tr>"
        text=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="50"><title>{title}</title><style>body{{background:#f4f3ee;color:#26373a;font:16px/1.65 -apple-system,"PingFang SC",sans-serif;margin:0}}main{{max-width:1180px;margin:40px auto;padding:25px}}section{{background:white;padding:25px;border:1px solid #ddd;border-radius:12px;margin:25px 0}}h1{{font-size:32px}}.tag,a{{color:#14746c}}.scroll{{overflow:auto}}table{{border-collapse:collapse;width:100%;font-size:14px}}td,th{{padding:12px;text-align:left;border-bottom:1px solid #ddd;white-space:nowrap}}.notice{{border-left:5px solid #b47931;padding:12px 18px;background:#fff6df}}small{{color:#66777b}}</style><main><div class="tag">COMACBENCH / 原生 CFD 敏感性研究</div><h1>{title}</h1><p class="notice">{notice}</p>{diagnostic}<section><h2>当前原生求解状态</h2><p>保持 p=0.3、U=0.7 松弛与原空间格式，GAMG 使用已通过桥接的 DICGaussSeidel。压力残差门槛 1e-9，速度 1e-10；还需末两保存场零点稳定。</p><div class="scroll"><table><thead><tr><th>算例 / 域长度</th><th>单元数</th><th>状态</th><th>迭代</th><th>压力残差</th><th>最大速度残差</th><th>证据</th></tr></thead><tbody>{table}</tbody></table></div><small>每 50 秒读取本地原生日志。迭代数是收敛步骤，不是物理时间。</small></section><section><h2>已经确认的事项</h2><p>旧三档入口积分与原生通量一致，面中心采样存在可量化的二阶积分偏差；近壁为层流无滑移，独立二次重构差异随加密下降。</p><p>Re=100 中更激进的松弛候选因发散或桥接偏差超限被否决，未进入正式 GCI。保留中止尝试与初始化来源，按原数值设置执行。</p><p><a href="protocol.json">冻结协议</a> · {evidence}</p></section></main></html>'''
        if (root/'analysis.json').exists():break
        (root/'index.html').write_text(text)
        print(json.dumps({'final':False,'rows':rows},ensure_ascii=False),flush=True)
        time.sleep(50)

if __name__=='__main__':main()
