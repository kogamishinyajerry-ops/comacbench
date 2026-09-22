"""Pinned research attachments. Fast admission checks receipts; --full hashes native files.

Neither mode reruns the solver or promotes a research tolerance into public scoring.
"""
from pathlib import Path
import hashlib
import itertools
import json

from .pack import safe_file

ROOT = Path(__file__).resolve().parents[1]
CATALOG = 'evidence/cfd-validation-v1.json'
CATALOG_SHA256 = '0e62a890865804e9418b4a71a25ccc0516a3d4771ea8a46cc69cc8bbddadb823'


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def checked(root, rel, expected):
    p = safe_file(root, rel)
    if sha(p) != expected:
        raise ValueError(f'digest_mismatch: {rel}')
    return p


def catalog(root=ROOT):
    return json.loads(checked(root, CATALOG, CATALOG_SHA256).read_text(encoding="utf-8"))['studies']


def verify_study(study, root=ROOT, full=False):
    retained_only = study.get('native_evidence_state') == 'deleted_by_user'
    if full and retained_only:
        raise ValueError('native_evidence_deleted: 原始场已按用户要求清理；仅保留历史分析与回执，不能完整复核。')
    for rel, expected in study['anchors'].items():
        checked(root, rel, expected)
    analysis = json.loads(safe_file(root, study['analysis']).read_text(encoding="utf-8"))
    rows = analysis['rows']
    expected = set(itertools.product([1, 2, 4, 8], [5, 10], [30, 60]))
    actual = {(r['config']['scale'], r['config']['upstream_h'], r['config']['downstream_h']) for r in rows}
    if (analysis['reynolds'] != study['reynolds'] or analysis['gate_passed'] is not True
        or analysis['failed_gates'] or len(rows) != 16 or actual != expected
        or any(r['valid'] is not True or r['config']['reynolds'] != study['reynolds'] for r in rows)
        or analysis['calibrated_tolerance'] is not None or analysis['current_benchmark_tolerance'] != .1
        or analysis['screening_tolerance_candidate']['relative_band'] != study['candidate_relative_tolerance']):
        raise ValueError('research_contract_mismatch: matrix / gates / tolerance')
    native_count = 0
    if full:
        for rel in study['native_manifests']:
            manifest = safe_file(root, rel)
            for name, record in json.loads(manifest.read_text(encoding="utf-8"))['files'].items():
                checked(manifest.parent, name, record['sha256'])
                native_count += 1
    return {k: study[k] for k in ('id','reynolds','report','analysis','reference')} | {
        'integrity_passed': True, 'verification_level': 'retained_analysis_and_receipts' if retained_only else 'native_file_hashes' if full else 'analysis_and_receipt_hashes',
        'native_evidence_available': not retained_only,
        'anchor_count': len(study['anchors']), 'native_files_hashed': native_count,
        'scientific_gate_passed': True, 'matrix_cases': len(rows), 'grid_levels': 4, 'domains': 4,
        'candidate_relative_tolerance': study['candidate_relative_tolerance'],
        'public_scoring_tolerance': .1, 'calibrated_tolerance': None,
        'scorable_reynolds': [100], 'publishable': False,
        'native_execution_counts': analysis.get('native_execution_counts'),
        'analysis_sha256': study['anchors'][study['analysis']],
        'scope': '二维稳态层流后向台阶；研究证据，非 agent 成绩。Re=200/300 尚未接入评分运行器。',
        'cases': [{'id': r['id'], 'scale': r['config']['scale'],
                   'upstream_h': r['config']['upstream_h'], 'downstream_h': r['config']['downstream_h'],
                   'x_over_h': r['qoi']['x_over_h']} for r in rows]}


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--full', action='store_true')
    args = ap.parse_args()
    try:
        results = [verify_study(s, full=args.full) for s in catalog()]
        print(json.dumps({'passed': True, 'studies': results, 'solver_calls': 0, 'model_calls': 0}, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as e:
        print(json.dumps({'passed': False, 'error': str(e)}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
