"""Deterministic policy, not a model score. Requires a genuine local CalculiX 2.23.

No evaluator expected answers or beam-theory values are used by this policy.
All reported measurements come from observed native job evidence.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from comacbench import workbench as wb
from comacbench.workbench_report import export_report


def perform(out: Path, *, ccx: str | None = None, negative: str | None = None,
            scenario: dict | None = None) -> dict:
    scenario = scenario or wb.read_json(ROOT / 'examples/workbench/structures-change-v1.json')
    out.mkdir(parents=True, exist_ok=False)
    session = out / 'session'
    # Preflight may fail; do not produce a fake solver success.
    obs = wb.start(session, scenario, {'name': 'native-reference-policy', 'revision': '1',
                                      'kind': 'negative_control' if negative else 'reference'}, ccx_path=ccx)
    while True:
        for target in sorted(obs['statuses']):
            if target == 'review' or obs['statuses'][target] == 'verified':
                continue
            response = wb.act(session, {'op': 'solve', 'target': target})
            if not response['result']['ok']:
                raise wb.WorkbenchError('native_reference_solve_failed: ' + str(response['result']))
            response = wb.act(session, {'op': 'check', 'target': target})
            if not response['result']['ok']:
                raise wb.WorkbenchError('native_reference_check_failed')
            obs = response['observation']
        cases = []
        for point in sorted(scenario['loads']):
            measured = obs['artifacts']['solution_' + point]['payload']['qoi']
            cases.append({'point': point, **measured,
                          'meets_requirement': abs(measured['uy_mm']) <= obs['sources']['requirement']['max_tip_mm']})
        payload = {'cases': cases, 'claim': 'requirements_met' if all(r['meets_requirement'] for r in cases) else 'needs_review',
                   'requirement_revision': obs['sources']['requirement']['revision']}
        wb.act(session, {'op':'put', 'target':'review', 'basis':obs['dependencies']['review'], 'payload':payload})
        response = wb.act(session, {'op':'check', 'target':'review'})
        if not response['result']['ok']:
            raise wb.WorkbenchError('native_reference_review_failed')
        obs = response['observation']
        if obs['remaining_phases']:
            obs = wb.act(session, {'op':'advance'})['observation']
            if negative == 'stale':
                response = wb.act(session, {'op':'submit', 'claim':'requirements_met'})
                if response['result']['code'] != 'unverified_targets':
                    raise wb.WorkbenchError('stale_negative_not_detected')
                break
        else:
            claim = 'requirements_met' if negative == 'false-ready' else payload['claim']
            response = wb.act(session, {'op':'submit','claim':claim})
            expected = 'false_completion_claim' if negative else 'work_package_complete'
            if response['result']['code'] != expected:
                raise wb.WorkbenchError('unexpected_terminal_result: ' + str(response['result']))
            break
    return export_report(session, out / 'report')


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--ccx')
    p.add_argument('--negative', choices=('stale','false-ready'))
    a = p.parse_args()
    try:
        result = perform(a.out, ccx=a.ccx, negative=a.negative)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, wb.WorkbenchError) as exc:
        error = {'status':'BLOCKED', 'error':str(exc), 'model_called':False, 'native_acceptance_passed':False}
        # Keep the unfinished session/failed raw jobs, rather than cleaning them up.
        if a.out.is_dir() and not (a.out/'blocked.json').exists():
            (a.out/'blocked.json').write_bytes(wb.canonical(error))
        print(json.dumps(error, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
