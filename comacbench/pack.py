"""Read-only, fail-closed contribution checks. Never import/execute contributed code."""
from __future__ import annotations

import ast
import hashlib
import json
import math
from pathlib import Path
import re

import yaml

PROTOCOL = 'comacbench.pack.v1'
FAMILIES = {'industrial_simulation', 'enterprise_data', 'knowledge_ontology'}
KINDS = {'simulation_agent': {'ccx_fea','cfd_step'}, 'code_exec': {'unit_tests_problem'}}
ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,100}$')


class UniqueSafeLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    pairs=loader.construct_pairs(node,deep=deep)
    result={}
    for key,value in pairs:
        if key in result:
            raise ValueError('duplicate YAML key')
        result[key]=value
    return result


UniqueSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,unique_mapping)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def safe_file(root, value):
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise ValueError('path_escape')
    root = Path(root).resolve()
    p = root / value
    # Symlinks are disallowed even if the final target is currently inside the pack.
    if not p.resolve().is_relative_to(root) or any(x.is_symlink() for x in [p, *p.parents] if x != root and x.is_relative_to(root)):
        raise ValueError('path_escape')
    if not p.is_file():
        raise ValueError('missing_file')
    return p


def fingerprint(root):
    root = Path(root).resolve()
    rows = {}
    for p in sorted(root.rglob('*')):
        if p.is_symlink():
            raise ValueError('pack contains symlink')
        if p.is_file() and '__pycache__' not in p.parts:
            rows[str(p.relative_to(root))] = digest(p)
    return hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()


def _validate_pack(root):
    root = Path(root).resolve()
    issues, tasks = [], []

    def issue(code, field, message, fix, severity='blocker', task_id=None):
        issues.append(dict(code=code, severity=severity, field=field, message=message,
                           suggested_fix=fix, task_id=task_id))

    def file(value, field, expected=None, tid=None):
        try:
            p = safe_file(root, value)
        except ValueError as e:
            issue(str(e), field, f'材料不可读取：{value}', '补齐包内文件；使用相对路径，不使用符号链接。', task_id=tid)
            return None
        if expected is not None and (not isinstance(expected, str) or digest(p) != expected.removeprefix('sha256:')):
            issue('digest_mismatch', field, '材料摘要与锁定值不一致。', '核对材料修订，确认后更新摘要并建立新版本。', task_id=tid)
        return p

    def mapping(p, field):
        try:
            data = yaml.load(p.read_text(encoding='utf-8'), Loader=UniqueSafeLoader)
            if not isinstance(data, dict):
                raise ValueError('expected mapping')
            return data
        except (OSError, ValueError, yaml.YAMLError, UnicodeError):
            issue('invalid_yaml', field, 'YAML 必须是可解析的对象。', '按 pack.yaml / TaskSpec 示例修复类型与缩进。')
            return {}

    pf = file('pack.yaml', 'pack.yaml')
    pack = mapping(pf, 'pack.yaml') if pf else {}
    for k in ('id', 'title', 'revision', 'description', 'license', 'source', 'suites'):
        if not pack.get(k):
            issue('missing_metadata', f'pack.{k}', '评测包元数据缺失。', f'补充 {k}。')
    if pack.get('protocol') != PROTOCOL:
        issue('unsupported_protocol', 'pack.protocol', '不支持该评测包协议。', f'使用 {PROTOCOL}。')
    if not isinstance(pack.get('id'), str) or not ID.fullmatch(pack.get('id', '')):
        issue('invalid_id', 'pack.id', 'ID 格式无效。', '使用字母、数字、点、下划线或短横线。')
    suites = pack.get('suites')
    if not isinstance(suites, list) or not suites:
        issue('empty_suite', 'pack.suites', '没有可评测任务族。', '提供非空 suites 列表。')
        suites = []
    seen, suite_ids = set(), set()
    for si, suite in enumerate(suites):
        sf = f'pack.suites[{si}]'
        if not isinstance(suite, dict):
            issue('invalid_suite', sf, '任务族必须是对象。', '填写 id、family、tasks。')
            continue
        sid = suite.get('id')
        if not isinstance(sid, str) or not ID.fullmatch(sid) or sid in suite_ids:
            issue('invalid_suite', sf+'.id', '任务族 ID 非法或重复。', '指定唯一 ID。')
            continue
        suite_ids.add(sid)
        if suite.get('family') not in FAMILIES:
            issue('invalid_family', sf+'.family', '未声明支持的能力族。', '选择 industrial_simulation、enterprise_data 或 knowledge_ontology。')
        paths = suite.get('tasks')
        if not isinstance(paths, list) or not paths:
            issue('empty_suite', sf+'.tasks', '任务族为空。', '至少提供一份任务 YAML。')
            continue
        declared = set()
        for ti, rel in enumerate(paths):
            tf = f'{sf}.tasks[{ti}]'
            tp = file(rel, tf)
            if not tp:
                continue
            # Existing runner derives assets_root from tasks/<suite>/; freeze this layout.
            if tp.parent != root/'tasks'/sid or tp.suffix != '.yaml':
                issue('task_layout', tf, '任务路径不符合运行器契约。', f'放入 tasks/{sid}/<task_id>.yaml。')
                continue
            declared.add(tp.name)
            t = mapping(tp, str(rel))
            tid = t.get('id')
            if not isinstance(tid, str) or not ID.fullmatch(tid) or tid != tp.stem or tid in seen:
                issue('invalid_id', str(rel)+'.id', '任务 ID 非法、重复或与文件名不符。', '修复唯一 task_id 与文件名。')
                continue
            seen.add(tid)
            tasks.append({'id': tid, 'suite': sid, 'family': suite.get('family'), 'path': rel,
                          'adapter': t.get('task_type'), 'evidence_level': 'solver_execution' if t.get('task_type') == 'simulation_agent' else 'executable_checks'})
            def problem(code, field, message, fix, severity='blocker'):
                issue(code, f'{rel}:{field}', message, fix, severity, tid)
            for key in ('domain', 'model_profile', 'assets_revision', 'allowed_tools', 'output_contract', 'input', 'reference', 'grader', 'scoring', 'limits', 'license_provenance'):
                if not t.get(key):
                    problem('missing_contract', key, '任务契约缺少必填内容。', f'补充 {key}。')
            if t.get('hidden'):
                problem('unsupported_hidden', 'hidden', 'v1 贡献入口只接收公开开发集。', '隐藏评测需独立隔离发布流程，不能混入此包。')
            if t.get('registry_id') != sid:
                problem('suite_mismatch', 'registry_id', '任务归属与任务族不一致。', '保持 registry_id 与 suite.id 相同。')
            objects = ('input', 'reference', 'grader', 'scoring', 'limits', 'license_provenance')
            if any(not isinstance(t.get(k), dict) for k in objects):
                problem('invalid_type', 'task', 'input/reference/grader/scoring/limits/license_provenance 必须为对象。', '按 TaskSpec 修正字段类型。')
                continue
            inp, ref, g = t['input'], t['reference'], t['grader']
            tasks[-1]['exec_kind']=g.get('exec_kind')
            prompt = file(inp.get('prompt_file'), 'input.prompt_file', inp.get('prompt_sha256', ''), tid)
            if prompt and not prompt.read_text(encoding='utf-8').strip():
                problem('empty_prompt', 'input.prompt_file', '题面为空。', '提供完整输入、单位、操作和交付要求。')
            for key in ('source', 'revision', 'uncertainty_note'):
                if not isinstance(ref.get(key), str) or not ref[key].strip():
                    problem('missing_reference', f'reference.{key}', '参考答案缺少来源、版本或不确定度说明。', f'补充 {key}，说明真值和容差依据。')
            for key in ('license', 'source', 'revision'):
                if not t['license_provenance'].get(key):
                    problem('missing_license', f'license_provenance.{key}', '贡献材料权属信息不完整。', f'补充 {key}；不自动发布。')
            private = set()
            oracle = file(g.get('oracle_source'), 'grader.oracle_source', tid=tid)
            if oracle:
                private.add(oracle.resolve())
            assets = inp.get('assets', [])
            if not isinstance(assets, list):
                problem('invalid_type', 'input.assets', '资产清单必须是列表。', '使用 path/digest 对象列表。')
                assets = []
            for ai, a in enumerate(assets):
                if not isinstance(a, dict):
                    problem('invalid_type', f'input.assets[{ai}]', '资产条目必须是对象。', '提供 path 与 digest。')
                    continue
                ap = file(a.get('path'), f'input.assets[{ai}]', a.get('digest', ''), tid)
                if ap and (ap.resolve() in private or any(x in {'private', 'held_out', 'gold', 'oracle', 'gold_scripts'} for x in ap.relative_to(root).parts)):
                    problem('reference_exposed', f'input.assets[{ai}]', '判分答案或参考实现被列入 agent 可见输入。', '从 input.assets 移除，留在 grader/reference。')
            if t.get('task_type') not in KINDS or g.get('exec_kind') not in KINDS.get(t.get('task_type'), set()):
                problem('unsupported_grader', 'grader.exec_kind', '该执行类型尚未通过贡献入口的契约校验。', '使用已支持类型或先补充对应验证规则；不能仅登记字符串。')
            from runners.solvers.backward_step import INPUTS as CFD_INPUTS
            supported_output={'ccx_fea':['model.inp'],'unit_tests_problem':['script'],
                              'cfd_step':['case/'+name for name in CFD_INPUTS]}.get(g.get('exec_kind'))
            if supported_output and t.get('output_contract') != supported_output:
                problem('unsupported_output', 'output_contract', '当前判分器未覆盖声明的全部交付物。', f'当前支持 {supported_output}；其他制品需先实现检查器。')
            if g.get('validity_gate') is not True:
                problem('missing_gate', 'grader.validity_gate', '工程有效性门不能关闭。', '启用 validity_gate。')
            weights = t['scoring'].get('weights', {})
            if not isinstance(weights, dict) or set(weights) != {'physics','requirements','objective','robustness'} or any(not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) or v < 0 for v in weights.values()) or abs(sum(weights.values())-1) > 1e-8:
                problem('invalid_weights', 'scoring.weights', '权重必须有限、非负且和为 1。', '显式声明四项权重；不适用项设 0。')
            if isinstance(weights,dict) and isinstance(weights.get('physics'),(int,float)) and weights['physics'] <= 0:
                problem('unscored_correctness', 'scoring.weights.physics', '实质正确性未计分，只交空壳可能得满分。', '为物理/断言正确性设置正权重。')
            if isinstance(weights,dict) and (weights.get('objective',0) != 0 or g.get('exec_kind') in {'ccx_fea','cfd_step'} and weights.get('robustness',0) != 0):
                problem('unimplemented_score', 'scoring.weights', '对未实现的目标/扰动检查设置了正权重。', '不适用项设 0；增加真实检查后再赋权。')
            for key in ('wall_clock_s','attempts','cpu','memory_gb'):
                n=t['limits'].get(key)
                if not isinstance(n,(float,int)) or isinstance(n,bool) or not math.isfinite(n) or n <= 0:
                    problem('invalid_limit', f'limits.{key}', '运行限额必须是有限正数。', '填写可执行的限额；墙钟限制与费用预算无关。')
            tests = g.get('tests', [])
            if g.get('exec_kind') == 'cfd_step':
                from runners.solvers.cfd_profile import PROFILE, THRESHOLDS, TEMPLATES
                if g.get('cfd_contract') != {'profile':PROFILE,'thresholds':THRESHOLDS}:
                    problem('invalid_cfd_contract','grader.cfd_contract','CFD 检查参数遗漏、未知或偏离已校准的受限算例。','使用公开 profile 与完整固定阈值；新物理问题需另行实现和校准。')
                if (ref.get('values') != {'reattachment_x_over_h':2.922} or ref.get('rel_tol') != .1
                    or g.get('numeric_rel_tol') != .1 or g.get('result_keys') != ['reattachment_x_over_h']
                    or t.get('evaluation',{}).get('units') != 'm, s, m^2/s, m^2/s^2, m^3/s'
                    or ref.get('doi') != '10.1016/j.compfluid.2007.09.003'):
                    problem('cfd_reference_mismatch','reference / evaluation.units','Re=100 后向台阶的真值、单位、来源或容差与已实现契约不一致。','核对论文表 5：2.922h；使用 10% 相对带及规定单位，并说明短域与离散误差限制。')
                if (g.get('solver_backend') != 'openfoam10-pinned-docker' or t['limits'] != {'cpu':2,'memory_gb':4,'wall_clock_s':600,'attempts':1}):
                    problem('cfd_runtime_mismatch','grader.solver_backend / limits','声明的执行后端或资源与固定运行环境不同。','使用 OpenFOAM 10、2 CPU、4 GiB、600 秒、1 次尝试。')
                available={a.get('path') for a in assets if isinstance(a,dict)}
                for name,content in TEMPLATES.items():
                    p=file('templates/'+name,'input.templates',tid=tid)
                    if p and (p.read_text()!=content or 'templates/'+name not in available):
                        problem('cfd_template_mismatch','input.templates/'+name,'公开方言模板缺失、被改写或没有交给受测 agent。','保留完整公开模板并列入带摘要的 input.assets；参考脚本留在 private。')
                required={'cfd:'+s for s in ('inputs','mesh','solver','convergence','conservation','qoi')}
                cfd_checks={r.get('check') for r in t.get('evaluation',{}).get('requirements',[]) if isinstance(r,dict)}
                if not required.issubset(cfd_checks):
                    problem('missing_cfd_check','evaluation.requirements','六阶段 CFD 工程检查未完整追踪。','补齐 inputs、mesh、solver、convergence、conservation、qoi。')
                fault_codes={'boundary_mismatch','fluid_mismatch','precomputed_output','mesh_below_minimum','not_converged','inlet_profile_mismatch'}
                declared_faults={n.get('expected_issue') for n in t.get('evaluation',{}).get('negative_controls',[]) if isinstance(n,dict)}
                if not fault_codes.issubset(declared_faults):
                    problem('missing_cfd_negative','evaluation.negative_controls','缺少本版要求的工程故障负例或预期诊断。','补齐缺边界、错误黏度、预制 QoI、粗网格、未收敛及错误入口；校准须命中各自 expected_issue。')
                problem('bounded_cfd_profile','grader.cfd_contract','二维 Re=100 短域后向台阶已接入原生证据检查；网格收敛与飞机级适用性仍待审查。','完成正负例校准、网格与域长度敏感性研究，再请工程专家审核。','review')
            if g.get('exec_kind') == 'unit_tests_problem':
                if not isinstance(tests,list) or not tests:
                    problem('empty_tests', 'grader.tests', '没有可执行的判分断言。', '添加正向、缺失、错误与边界输入的断言。')
                    tests=[]
                for j, src in enumerate(tests):
                    try:
                        tree=ast.parse(src)
                        assertions=[n for n in ast.walk(tree) if isinstance(n,ast.Assert)]
                        effective=[n for n in assertions if any(isinstance(x,ast.Call) for x in ast.walk(n.test)) and not isinstance(n.test,ast.Constant)]
                        if not effective:
                            raise ValueError('vacuous')
                    except (SyntaxError, ValueError, TypeError):
                        problem('vacuous_test', f'grader.tests[{j}]', '断言无法执行或没有检查候选函数。', '用候选函数的输出与独立预期结果比较。')
                if ref.get('n_test_cases') != len(tests):
                    problem('test_count_mismatch', 'reference.n_test_cases', '参考声明的测试数量与实际断言数不符。', '核对清单和遗漏的用例。')
            if g.get('exec_kind') == 'ccx_fea':
                keys=g.get('result_keys')
                vals=ref.get('values')
                if not isinstance(keys,list) or not keys or not isinstance(vals,dict) or set(keys) != set(vals) or set(keys) != set(g.get('extract',{})):
                    problem('metric_mismatch', 'grader.result_keys', '输出指标、抽取器和参考答案未一一对应。', '补齐同名指标和抽取规则。')
                elif any(not isinstance(v,(float,int)) or isinstance(v,bool) or not math.isfinite(v) for v in vals.values()):
                    problem('nonfinite_reference', 'reference.values', '参考答案包含非有限数或非数值。', '修复真值来源并重新校准。')
                tol=g.get('numeric_rel_tol')
                if not isinstance(tol,(int,float)) or isinstance(tol,bool) or not math.isfinite(tol) or tol <= 0 or tol >= 1:
                    problem('invalid_tolerance', 'grader.numeric_rel_tol', '相对容差无效或宽到不能判别。', '提供 0 到 1 之间、带依据的容差。')
                elif tol > .1:
                    problem('wide_tolerance', 'grader.numeric_rel_tol', '容差超过 10%，需检查是否掩盖错误。', '提供误差/不确定度推导与邻近错误负例。', 'review')
                quality=t.get('evaluation',{})
                if not isinstance(quality,dict) or not quality.get('units'):
                    problem('missing_units', 'evaluation.units', '结构任务未声明单位体系。', '明确长度、载荷、应力与密度单位。')
                if 'deck_contract' in g:
                    from runners.solvers.cantilever_contract import contract_errors
                    errors = contract_errors(g['deck_contract'])
                    for error in errors:
                        problem('invalid_deck_contract', 'grader.deck_contract.'+error['field'], error['message'], '补齐 profile 声明的完整参数，不得以空值或未知字段关闭检查。')
                    if not errors:
                        expected_extract = {'tip_defl_mm': {'type':'max_abs_udof','set':'NTIP','dof':2},
                                            'root_rf_sum_n': {'type':'sum_rf','set':'NROOT','dof':2}}
                        if (g.get('extract') != expected_extract or not isinstance(vals,dict)
                            or not isinstance(vals.get('root_rf_sum_n'), (float,int))
                            or not math.isclose(vals['root_rf_sum_n'], -g['deck_contract']['total_fy_n'], rel_tol=1e-6)
                            or quality.get('units') != 'mm, N, MPa, tonne/mm^3'):
                            problem('deck_reference_mismatch', 'grader.deck_contract / reference / extract / evaluation.units',
                                    '输入契约、根部平衡反力、输出集合或单位声明不一致。', '核对合载荷与正向反力、NTIP U2/NROOT RF2 抽取及固定单位体系。')
                    problem('bounded_engineering_profile', 'grader.deck_contract', '已接入结构化静力梁六项输入检查；仍需审查参考值、离散误差与题面语义。', '完成正负例校准及工程专家审查；此检查不代表复杂结构或飞机级接受。', 'review')
                else:
                    problem('partial_engineering_gate', 'grader', '当前核验实际求解与数值输出；网格、边界条件、材料与工况并未逐项独立审查。', '限制结论范围；增加对应检查器和故障负例后才能升级工程声明。', 'review')
            ev=t.get('evaluation', {})
            if not isinstance(ev,dict) or not ev.get('requirements') or not ev.get('negative_controls'):
                problem('missing_quality_plan', 'evaluation', '缺少需求到检查的追踪或负例。', '列出 requirements 及 negative_controls。')
                continue
            reqs=ev['requirements']
            if not isinstance(reqs,list):
                problem('invalid_type','evaluation.requirements','需求追踪必须是列表。','按示例填写 id/text/check。')
                continue
            for req in reqs:
                if not isinstance(req,dict) or not req.get('text') or not req.get('check'):
                    problem('uncovered_requirement','evaluation.requirements','存在没有判分检查的要求。','补充检查或明确标注 not_covered。')
                elif req['check']=='not_covered':
                    problem('uncovered_requirement','evaluation.requirements',req['text'],'补充检查器，当前不能据此宣称通过。','review')
                elif not isinstance(req['check'],str):
                    problem('invalid_type','evaluation.requirements.check','检查引用必须是字符串。','使用 test:1 等检查 ID。')
                elif req['check'].startswith('test:'):
                    try:
                        if not 1 <= int(req['check'].split(':')[1]) <= len(tests):
                            raise ValueError()
                    except ValueError:
                        problem('unknown_check','evaluation.requirements','需求引用了不存在的断言。','填写实际断言序号。')
                elif req['check'].startswith('deck:'):
                    from runners.solvers.cantilever_contract import CHECKS, contract_errors
                    if (g.get('exec_kind') != 'ccx_fea' or 'deck_contract' not in g
                        or contract_errors(g['deck_contract']) or req['check'][5:] not in CHECKS):
                        problem('unknown_check','evaluation.requirements','结构检查引用缺少可用契约或检查项不存在。','使用有效 deck_contract 及已实现的 deck: 检查 ID。')
                elif req['check'].startswith('cfd:'):
                    from runners.solvers.backward_step import STAGES
                    if g.get('exec_kind')!='cfd_step' or req['check'][4:] not in STAGES:
                        problem('unknown_check','evaluation.requirements','未知或未启用的 CFD 检查。','使用公开六阶段 cfd: 检查项。')
                elif req['check'] not in ({'solver_exit','reference_metrics','output_contract'} if g.get('exec_kind')=='ccx_fea' else {'output_contract'}):
                    problem('unknown_check','evaluation.requirements','未知的判分检查引用。','使用实际检查 ID。')
            negs=ev['negative_controls']
            if not isinstance(negs,list):
                problem('invalid_type','evaluation.negative_controls','负例必须为列表。','提供 script 与 max_score。')
            else:
                for n in negs:
                    if not isinstance(n,dict):
                        problem('invalid_type','evaluation.negative_controls','负例条目必须为对象。','提供 script 与 max_score。')
                        continue
                    np=file(n.get('script'),'evaluation.negative_controls.script',tid=tid)
                    if np and np.resolve() in {(root/a['path']).resolve() for a in assets if isinstance(a,dict) and isinstance(a.get('path'),str)}:
                        problem('reference_exposed','input.assets','负例代码不能作为公开输入。','将负例留在判分侧。')
                    if 'expected_issue' in n:
                        from runners.solvers.cantilever_contract import ISSUE_CODES
                        enabled=g.get('exec_kind')=='ccx_fea' and 'deck_contract' in g
                        if g.get('exec_kind')=='cfd_step':
                            from runners.solvers.backward_step import ISSUE_CODES
                            enabled=True
                        if not enabled or not isinstance(n['expected_issue'],str) or n['expected_issue'] not in ISSUE_CODES:
                            problem('unknown_expected_issue','evaluation.negative_controls.expected_issue','负例引用未知或未启用的工程诊断。','指定结构契约检查器的真实问题代码。')
                    mx=n.get('max_score')
                    if not isinstance(mx,(int,float)) or isinstance(mx,bool) or not math.isfinite(mx) or not 0 <= mx < 1:
                        problem('invalid_negative','evaluation.negative_controls.max_score','负例必须明确预期不满分。','声明 0 <= max_score < 1。')
        directory=root/'tasks'/sid
        if directory.is_dir() and {p.name for p in directory.glob('*.yaml')} != declared:
            issue('undeclared_task', sf+'.tasks', '目录中存在未列入清单的任务。', '对齐任务清单，防止运行器悄悄扩大样本。')
    issue('expert_review_required', 'pack', '静态检查不证明题意、工程真值与判分语义一致；当前包未完成发布审查。', '校准参考实现和错误负例，再进行工程专家审查。', 'review')
    for p in root.rglob('*'):
        if p.is_symlink():
            issue('path_escape',str(p.relative_to(root)),'评测包包含符号链接。','将许可范围内的材料实文件放入包中。')
    for sid in suite_ids:
        if len({t['adapter'] for t in tasks if t['suite']==sid}) > 1:
            issue('mixed_adapters',sid,'同一任务族不能混用运行器。','按 adapter 分成独立 suite。')
    return {'protocol': PROTOCOL, 'pack': {k:pack.get(k) for k in ('id','title','revision','description','source','license')},
            'runnable': not any(i['severity']=='blocker' for i in issues), 'publishable': False,
            'task_count':len(tasks), 'tasks':tasks, 'issues':issues,
            'summary':{s:sum(i['severity']==s for i in issues) for s in ('blocker','review','warning')}}


def validate_pack(root):
    try:
        return _validate_pack(root)
    except (ValueError, TypeError, KeyError, AttributeError, OSError, UnicodeError, RecursionError) as e:
        # Malformed contributed structures must still return user feedback, never launch code.
        return {'protocol':PROTOCOL,'pack':{},'runnable':False,'publishable':False,
                'task_count':0,'tasks':[], 'summary':{'blocker':1,'review':0,'warning':0},
                'issues':[{'code':'invalid_contract','severity':'blocker','task_id':None,
                           'field':'pack / task YAML','message':f'材料结构无法完整检查：{type(e).__name__}',
                           'suggested_fix':'按示例核对嵌套字段类型、编码和列表元素；此包未执行。'}]}
