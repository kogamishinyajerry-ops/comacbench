"""probe v2: 验收重写后的 workload evaluator（fix/ 副本，artifacts.v2）。

与原 probe_workload.py 的差异：
  - PACK 指向 fix/（assets/ 与 private/ 均取自修复副本，原始包不动）
  - 保留原 18 个场景（5 正例 + 13 反例）
  - 新增 8 个独立审查反例/成对用例（a-h，不与原 13 重叠）：
      a) all_valid_rows_rejected      有效行全部被拒（空 normalized + 全进 exceptions）
      b) legal_duplicate_input        同 point 同值两行（运行时构造 case；oracle 冻结规则
                                      下第二行同样触发 seen 拒收 → 按冲突处理，期望
                                      evaluator 与 oracle 一致 = 正例）
      c) stale_version_reuse          输入版本已更新的旧版本结果复用（运行时构造 case，
                                      交付 source_version/version 改回旧值）
      d) missing_run_manifest_deliverable  从 manifest.json 删 run_manifest kind 并删文件
      e) duplicate_kind_declaration   manifest.json 中 normalized 声明两次
      f) mass_flow_off_by_10x         mass_flow 与输入差 10 倍（数值级错误）
      g) unparseable_manifest_csv     run_manifest.csv 写成二进制乱码
      h) wrong_case_identity          rows 数值全对但 case_id 换成另一合法格式串

输出与原探针一致：每场景一行控制台输出 + 末尾汇总表 + JSON summary。
exit 0 = 全部场景符合预期（正例全过、反例全拦、无 evaluator 异常）。
"""
from pathlib import Path
from types import SimpleNamespace
import importlib.util, subprocess, sys, json, os, shutil, csv

ROOT = Path(__file__).resolve().parents[1]        # 仓库根
PACK = ROOT / 'packs/aviation-workload-starter-v1'  # assets/ private/ 在 pack 下
EVALUATOR = PACK / 'private/workload_evaluator.py'
ORACLE = PACK / 'private/workload_oracle.py'
EVIDENCE = ROOT / 'probes/evidence/workload'
RUNTIME = ROOT / 'probes/.probe_runtime'           # 运行时构造 case 的伪 pack 根
EVIDENCE.mkdir(parents=True, exist_ok=True)
spec = importlib.util.spec_from_file_location('fixed_workload_evaluator', EVALUATOR)
ev = importlib.util.module_from_spec(spec); spec.loader.exec_module(ev)

def readj(ws): return json.loads((ws / 'outputs/normalized.json').read_text())
def writej(ws, d): (ws / 'outputs/normalized.json').write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
def readc(ws, name):
    with (ws / 'outputs' / name).open(newline='') as f: return list(csv.DictReader(f))
def writec(ws, name, rows, fields=None):
    fields = fields or {'run_manifest.csv': ['point', 'case_id', 'version'],
                        'exceptions.csv': ['point', 'reason', 'detail']}[name]
    with (ws / 'outputs' / name).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)

# ---- 原探针的 13 个反例构造 + legal_reorder（保持原样语义） ----
def values(ws, value):
    d = readj(ws)
    for r in d['rows']: r['altitude_m'] = value; r['mass_flow_kg_s'] = value
    writej(ws, d)
def lineage(ws):
    d = readj(ws); d['case_id'] = 'OTHER-CASE'
    for r in d['rows']: r.pop('source_version', None)
    writej(ws, d)
    rs = readc(ws, 'run_manifest.csv')
    for r in rs: r['case_id'] = 'OTHER-CASE'; r['version'] = '1999-01-01'
    writec(ws, 'run_manifest.csv', rs)
def extra(ws):
    rs = readc(ws, 'run_manifest.csv'); rs.append(dict(point='P99', case_id='OTHER', version='old')); writec(ws, 'run_manifest.csv', rs)
def dup(ws):
    rs = readc(ws, 'run_manifest.csv'); rs.append(dict(rs[0])); writec(ws, 'run_manifest.csv', rs)
def missing_exceptions(ws):
    (ws / 'outputs/exceptions.csv').unlink()
    p = ws / 'manifest.json'; m = json.loads(p.read_text())
    m['deliverables'] = [d for d in m['deliverables'] if d['kind'] != 'exceptions']
    p.write_text(json.dumps(m))
def bad_header(ws): (ws / 'outputs/exceptions.csv').write_text('wrong,header\n')
def drop_valid(ws):
    d = readj(ws); d['rows'] = [r for r in d['rows'] if r['point'] != 'P3']; writej(ws, d)
    writec(ws, 'run_manifest.csv', [r for r in readc(ws, 'run_manifest.csv') if r['point'] != 'P3'])
def keep_conflict(ws):
    d = readj(ws); d['rows'].append(dict(point='P1', altitude_m=0, mass_flow_kg_s=1.2, source_version='2026-09-12')); writej(ws, d)
    rs = readc(ws, 'run_manifest.csv'); rs.append(dict(point='P1', case_id='BLEED-CHK-C', version='2026-09-12')); writec(ws, 'run_manifest.csv', rs)
def stale(ws):
    rs = readc(ws, 'run_manifest.csv'); rs.append(dict(point='P0', case_id='BLEED-CHK-D', version='old')); writec(ws, 'run_manifest.csv', rs)
def nonsense_reason(ws):
    rs = readc(ws, 'exceptions.csv')
    for r in rs: r['reason'] = 'looks good'; r['detail'] = ''
    writec(ws, 'exceptions.csv', rs)
def malformed_rows(ws):
    d = readj(ws); d['rows'] = 42; writej(ws, d)
def reordered(ws):
    rs = readc(ws, 'run_manifest.csv'); writec(ws, 'run_manifest.csv', rs[::-1], ['version', 'point', 'case_id'])
    d = readj(ws); d['rows'] = d['rows'][::-1]; writej(ws, d)

# ---- 新增 8 个独立反例/成对用例构造 ----
def reject_all(ws):
    d = readj(ws); d['rows'] = []; writej(ws, d)
    writec(ws, 'run_manifest.csv', [])
    writec(ws, 'exceptions.csv', [dict(point=p, reason='missing_unit:altitude', detail='全部拒收') for p in ('P1', 'P2', 'P3')])
def old_version_reuse(ws):
    d = readj(ws)
    for r in d['rows']: r['source_version'] = '2026-09-12'
    writej(ws, d)
    rs = readc(ws, 'run_manifest.csv')
    for r in rs: r['version'] = '2026-09-12'
    writec(ws, 'run_manifest.csv', rs)
def missing_manifest(ws):
    (ws / 'outputs/run_manifest.csv').unlink()
    p = ws / 'manifest.json'; m = json.loads(p.read_text())
    m['deliverables'] = [d for d in m['deliverables'] if d['kind'] != 'run_manifest']
    p.write_text(json.dumps(m))
def double_kind(ws):
    p = ws / 'manifest.json'; m = json.loads(p.read_text())
    m['deliverables'].append({'path': 'outputs/normalized.json', 'kind': 'normalized'})
    p.write_text(json.dumps(m))
def tenx(ws):
    d = readj(ws)
    for r in d['rows']: r['mass_flow_kg_s'] = r['mass_flow_kg_s'] * 10
    writej(ws, d)
def garbage(ws):
    (ws / 'outputs/run_manifest.csv').write_bytes(bytes(range(256)))
def wrong_identity(ws):
    d = readj(ws); d['case_id'] = 'BLEED-CHK-Z'; writej(ws, d)
    rs = readc(ws, 'run_manifest.csv')
    for r in rs: r['case_id'] = 'BLEED-CHK-Z'
    writec(ws, 'run_manifest.csv', rs)

# ---- 运行时构造 case（b/c 两个场景无现成 case 文件） ----
def make_runtime_case(tid, case_dict):
    tdir = RUNTIME / 'tasks/enterprise.workload'; tdir.mkdir(parents=True, exist_ok=True)
    (tdir / f'{tid}.yaml').touch()
    adir = RUNTIME / 'assets'; adir.mkdir(parents=True, exist_ok=True)
    (adir / f'{tid}_case.json').write_text(json.dumps(case_dict, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')

runtime_cases = {
    # b) 同 point 同值两行：oracle seen 规则同样拒收 → 期望按冲突处理（P1 两条都拒）
    'workload_legal_dup_05': {
        'case_id': 'BLEED-CHK-E', 'version': '2026-09-12',
        'rows': [
            {'point': 'P1', 'altitude_m': 0, 'mass_flow_kg_s': 1.2},
            {'point': 'P1', 'altitude_m': 0, 'mass_flow_kg_s': 1.2},
            {'point': 'P2', 'altitude_m': 6000, 'mass_flow_kg_s': 0.95},
        ]},
    # c) 输入版本已更新（2026-09-20）；反例交付复用旧版本 2026-09-12 的结果
    'workload_stale_refresh_06': {
        'case_id': 'BLEED-CHK-F', 'version': '2026-09-20',
        'rows': [
            {'point': 'P1', 'altitude_m': 0, 'mass_flow_kg_s': 1.2},
            {'point': 'P2', 'altitude_m': 6000, 'mass_flow_kg_s': 0.95},
        ],
        'stale_results': [{'point': 'P0', 'note': 'older revision output present'}]},
}
for tid, cd in runtime_cases.items():
    make_runtime_case(tid, cd)

cases = ['workload_baseline_01', 'workload_missing_unit_02', 'workload_conflict_dup_03', 'workload_stale_output_04']
base = cases[0]
probes = [(f'oracle_{tid}', tid, None, True) for tid in cases] + [
    ('legal_reorder', base, reordered, True),
    # ---- 原 13 反例 ----
    ('wrong_physical_values', base, lambda ws: values(ws, -999999), False),
    ('booleans_as_measurements', base, lambda ws: values(ws, True), False),
    ('nonfinite_measurements', base, lambda ws: values(ws, float('nan')), False),
    ('wrong_case_and_missing_lineage', base, lineage, False),
    ('extra_job', base, extra, False),
    ('duplicate_job', base, dup, False),
    ('missing_required_exceptions_file', base, missing_exceptions, False),
    ('bad_exceptions_header', base, bad_header, False),
    ('drop_legitimate_P3', cases[1], drop_valid, False),
    ('accept_conflicting_P1', cases[2], keep_conflict, False),
    ('stale_P0_in_run_manifest', cases[3], stale, False),
    ('wrong_rejection_reason', cases[1], nonsense_reason, False),
    ('malformed_rows_type', base, malformed_rows, False),
    # ---- 新增 8 个独立反例/成对用例 ----
    ('all_valid_rows_rejected', base, reject_all, False),                      # a
    ('legal_duplicate_input', 'workload_legal_dup_05', None, True),            # b
    ('stale_version_reuse', 'workload_stale_refresh_06', old_version_reuse, False),  # c
    ('missing_run_manifest_deliverable', base, missing_manifest, False),       # d
    ('duplicate_kind_declaration', base, double_kind, False),                  # e
    ('mass_flow_off_by_10x', base, tenx, False),                               # f
    ('unparseable_manifest_csv', base, garbage, False),                        # g
    ('wrong_case_identity', base, wrong_identity, False),                      # h
]

report = []
for name, tid, mutate, expected in probes:
    constructed = tid in runtime_cases
    pack_root = RUNTIME if constructed else PACK
    ws = EVIDENCE / name
    if ws.exists(): shutil.rmtree(ws)
    (ws / 'inputs/assets').mkdir(parents=True)
    shutil.copyfile(pack_root / 'assets' / f'{tid}_case.json',
                    ws / 'inputs/assets' / f'{tid}_case.json')
    env = dict(os.environ); env.pop('WORKLOAD_CASE', None)
    proc = subprocess.run([sys.executable, str(ORACLE)], cwd=ws, env=env,
                          text=True, capture_output=True, timeout=10)
    assert proc.returncode == 0, (name, proc.stderr)
    if mutate: mutate(ws)
    manifest = json.loads((ws / 'manifest.json').read_text())
    task = SimpleNamespace(id=tid,
                           yaml_path=pack_root / 'tasks/enterprise.workload' / f'{tid}.yaml')
    try:
        result = ev.evaluate(task, ws, manifest['deliverables'])
        accepted = bool(result.get('checks')) and all(c['passed'] for c in result['checks'])
        error = None
    except Exception as e:
        result = {}; accepted = False; error = type(e).__name__ + ': ' + str(e)
    row = dict(name=name, task_id=tid, expected_accept=expected, actual_accept=accepted,
               defect=(accepted != expected) or error is not None, error=error,
               failed_checks=result.get('failed', []), checks=result.get('checks', []),
               workspace=str(ws.relative_to(ROOT)))
    report.append(row)
    (ROOT / 'evidence' / f'{name}.json').write_text(json.dumps(row, ensure_ascii=False, indent=2) + '\n')
    print(f'{name:40} expected={expected!s:<5} actual={accepted!s:<5} error={error}')

# 汇总表（控制台）
w = max(len(r['name']) for r in report) + 2
print('\n' + 'scenario'.ljust(w) + 'expect  actual  verdict')
for r in report:
    verdict = 'pass' if not r['defect'] else 'FAIL'
    print(r['name'].ljust(w) + f"{r['expected_accept']!s:<7}{r['actual_accept']!s:<7}{verdict}")

summary = dict(commit='5543fa5e4a5f5db716a782a5c1bfb5b4585ac8cd', python=sys.version,
               scope='fixed workload evaluator (fix/private) on local files, not full CLI',
               scenarios=len(report),
               positive=sum(r['expected_accept'] for r in report),
               positive_passed=sum(r['actual_accept'] and r['expected_accept'] for r in report),
               negative=sum(not r['expected_accept'] for r in report),
               false_accepts=sum(r['actual_accept'] and not r['expected_accept'] for r in report),
               false_rejects=sum(not r['actual_accept'] and r['expected_accept'] for r in report),
               evaluator_crashes=sum(r['error'] is not None for r in report),
               results=report)
(ROOT / 'evidence/workload-probes-v2.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in summary.items() if k != 'results'}, ensure_ascii=False, indent=2))
sys.exit(int(any(r['defect'] for r in report)))
