"""Evidence-aware entry point around the frozen v1 pack and execution contracts."""
from pathlib import Path
import yaml

from . import pack as base
from .evidence import catalog, verify_study, CATALOG_SHA256


def validate_pack(root):
    result = base.validate_pack(root)
    result['validation_evidence'] = []
    def issue(code, message, fix, severity='blocker'):
        result['issues'].append({'code': code, 'severity': severity, 'field': 'pack.validation_evidence',
                                'task_id': None, 'message': message, 'suggested_fix': fix})
    try:
        pack = yaml.load(base.safe_file(root, 'pack.yaml').read_text(), Loader=base.UniqueSafeLoader)
        links = pack.get('validation_evidence') if isinstance(pack, dict) else None
        cfd = any(t.get('exec_kind') == 'cfd_step' for t in result['tasks'])
        if cfd or links is not None:
            if (not isinstance(links, dict) or set(links) != {'protocol','purpose','studies'}
                or links.get('protocol') != 'comacbench.research-links.v1'
                or links.get('purpose') != 'research_support'
                or not isinstance(links.get('studies'), list) or not links['studies']
                or any(not isinstance(s, str) for s in links['studies'])
                or len(links['studies']) != len(set(links['studies']))):
                issue('invalid_research_links', '研究依据缺失或用途不合理；不能把研究容差声明成评分授权。',
                      '填写 research_support 和已接受的研究 ID；新研究需单独建立版本、材料与审核依据。')
            else:
                known = {s['id']: s for s in catalog()}
                for sid in links['studies']:
                    if sid not in known:
                        issue('unknown_research_evidence', f'未接受的研究证据：{sid}', '使用目录中的已接受版本；失败或未完成的历史尝试不能作为准入依据。')
                        continue
                    try:
                        result['validation_evidence'].append(verify_study(known[sid]))
                    except (ValueError, OSError, KeyError, TypeError) as e:
                        issue('research_evidence_integrity', f'{sid} 证据不完整或摘要不符：{e}', '恢复原始冻结证据及目录结构；不得修改摘要绕过校验。')
                if cfd and 'bfs-re100-validated-v1' not in links['studies']:
                    issue('research_scope_mismatch', '现有评分任务为 Re=100，未提供对应研究依据。', '补充 Re=100 研究；Re=200/300 的研究不能替代任务工况。')
            if result['validation_evidence']:
                result['issues'] = [i for i in result['issues'] if i['code'] != 'bounded_cfd_profile']
                issue('research_not_scoring_calibration', '敏感性研究已接入；候选带 2.5%/2%/2% 尚未成为评分容差。',
                      '公开 Re=100 仍使用 10%；Re=200/300 需先扩展运行契约、正负例校准及工程审核。快速预检只校验分析与回执摘要；完整复核还要求原始场存在；清理状态见下方反馈。', 'review')
            if any(not e.get('native_evidence_available', True) for e in result['validation_evidence']):
                issue('native_evidence_deleted', '原始 CFD 场与过程文件已按用户要求清理；这里只保留历史分析和回执。',
                      '可继续按现有契约评测新的 agent；历史研究无法从保存场完整复核。需要重新验证物理结果时重新求解，不能用历史通过标记代替。', 'review')
            result['evidence_catalog_sha256'] = CATALOG_SHA256
    except (ValueError, OSError, KeyError, TypeError, yaml.YAMLError) as e:
        issue('research_evidence_integrity', f'研究证据入口无法读取：{e}', '恢复材料、目录及合法 YAML 后重试。')
    result['summary'] = {s: sum(i['severity'] == s for i in result['issues']) for s in ('blocker','review','warning')}
    result['runnable'] = result['summary']['blocker'] == 0
    return result


def write_report(path, data):
    from .report import write_report as original
    import html
    import os
    from urllib.parse import quote
    from .evidence import ROOT
    original(path, data)
    rows = data.get('validation', {}).get('validation_evidence', [])
    if not rows:
        return
    retention_note = '<p><strong>原始场已清理：下列研究通过状态是历史记录，当前只能核验保留摘要。</strong></p>' if any(not r.get('native_evidence_available', True) for r in rows) else ''
    table = retention_note + '<section><h2>已接入的 CFD 研究证据</h2><p>摘要核验通过；不代表本次复算或 agent 成绩。公开评分仍为 Re=100 / 10%。</p><table><tr><th>工况</th><th>研究矩阵</th><th>候选带（非评分）</th><th>证据位置</th></tr>'
    for r in rows:
        url = quote(os.path.relpath(ROOT/r['report'], Path(path).resolve().parent))
        table += f'<tr><td>Re={r["reynolds"]}</td><td>{r["matrix_cases"]}/16 通过</td><td>{r["candidate_relative_tolerance"]:.1%}</td><td><a href="{html.escape(url)}">打开研究图表</a><br>{html.escape(r["analysis"])}</td></tr>'
    table += '</table></section>'
    p = Path(path)
    p.write_text(p.read_text().replace('<section id="coverage">', table+'<section id="coverage">'))


def main():
    # Explicit process-local dependency binding; the frozen files remain byte-identical.
    from . import __main__ as legacy
    original_save = legacy.save
    def save(path, data):
        if isinstance(data, dict) and isinstance(data.get('rerun'), str):
            data['rerun'] = data['rerun'].replace('-m comacbench ', '-m comacbench.admission ', 1)
        original_save(path, data)
    legacy.save = save
    legacy.validate_pack = validate_pack
    legacy.write_report = write_report
    return legacy.main()


if __name__ == '__main__':
    raise SystemExit(main())
