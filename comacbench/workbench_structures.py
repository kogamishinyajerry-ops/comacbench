"""One controlled native family; no arbitrary plugins, solver code or custom tolerances."""
from __future__ import annotations
from copy import deepcopy
import math
from typing import Any
from . import workbench_ccx as ccx

FAMILY = 'comacbench.structures-change.v1'


def _api():
    from . import workbench
    return workbench


def is_native(scenario: Any) -> bool:
    return isinstance(scenario, dict) and scenario.get('protocol') == FAMILY


def sources(scenario: dict) -> dict:
    return {'model': {'template': ccx.TEMPLATE}, 'requirement': deepcopy(scenario['requirement']),
            'note': deepcopy(scenario['note']),
            **{f'load_{key}': deepcopy(v) for key, v in scenario['loads'].items()}}


def graph(scenario: dict) -> dict:
    nodes = {f'solution_{key}': ['model', f'load_{key}'] for key in sorted(scenario['loads'])}
    nodes['review'] = list(nodes) + ['requirement']
    return nodes


def source_valid(key: str, value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    if key.startswith('load_'):
        return (set(value) == {'force_y_n','revision'} and _api()._text(value['revision'])
                and type(value['force_y_n']) in (int, float) and -200 <= value['force_y_n'] <= -10)
    if key == 'requirement':
        return (set(value) == {'max_tip_mm','revision'} and _api()._text(value['revision'])
                and type(value['max_tip_mm']) in (int,float) and 0.1 <= value['max_tip_mm'] <= 1)
    if key == 'note':
        return set(value) == {'text'} and _api()._text(value['text'])
    return key == 'model' and value == {'template': ccx.TEMPLATE}


def validate(scenario: dict) -> dict:
    api = _api()
    fields = {'protocol','id','revision','title','description','license','max_actions',
              'max_solver_calls','solve_timeout_s','loads','requirement','note','phases'}
    if set(scenario) != fields:
        raise api.WorkbenchError('native_scenario_fields')
    if not isinstance(scenario['id'], str) or not api.ID.fullmatch(scenario['id']):
        raise api.WorkbenchError('native_scenario_id')
    if not all(api._text(scenario[k]) for k in ('revision','title','description','license')):
        raise api.WorkbenchError('native_metadata')
    if type(scenario['max_actions']) is not int or not 1 <= scenario['max_actions'] <= 128:
        raise api.WorkbenchError('native_action_budget')
    if type(scenario['max_solver_calls']) is not int or not 1 <= scenario['max_solver_calls'] <= 12:
        raise api.WorkbenchError('native_solver_budget')
    if type(scenario['solve_timeout_s']) is not int or not 1 <= scenario['solve_timeout_s'] <= 300:
        raise api.WorkbenchError('native_timeout')
    loads = scenario['loads']
    if not isinstance(loads, dict) or set(loads) != {'service','limit'}:
        raise api.WorkbenchError('native_load_ids')
    initial = sources(scenario)
    if any(not source_valid(k, v) for k, v in initial.items()):
        raise api.WorkbenchError('native_source')
    phases, ids = scenario['phases'], set()
    if not isinstance(phases, list) or not 1 <= len(phases) <= 8:
        raise api.WorkbenchError('native_phases')
    for i, phase in enumerate(phases):
        if (not isinstance(phase, dict) or set(phase) != {'id','instruction','changes'}
                or not isinstance(phase['id'], str) or not api.ID.fullmatch(phase['id'])
                or phase['id'] in ids or not api._text(phase['instruction'])
                or not isinstance(phase['changes'], dict)):
            raise api.WorkbenchError('native_phase_schema')
        ids.add(phase['id'])
        if (i == 0 and phase['changes']) or (i > 0 and not phase['changes']):
            raise api.WorkbenchError('native_phase_changes')
        for k, v in phase['changes'].items():
            if k == 'model' or k not in initial or not source_valid(k, v):
                raise api.WorkbenchError('native_source_change')
    if len(api.canonical(scenario)) > api.MAX_BYTES // 2:
        raise api.WorkbenchError('native_scenario_too_large')
    return deepcopy(scenario)


def request(scenario: dict, state: dict, action: Any) -> dict | None:
    """Return a broker-owned launch request only for a valid and budgeted solve action."""
    if (not isinstance(action, dict) or set(action) != {'op','target'}
            or action['op'] != 'solve' or not isinstance(action['target'], str)
            or action['target'] not in graph(scenario) or action['target'] == 'review'
            or state['complete'] or state['actions_used'] >= scenario['max_actions']
            or state['counts'].get('solver_calls', 0) >= scenario['max_solver_calls']):
        return None
    target = action['target']
    return {'template': ccx.TEMPLATE, 'target': target,
            'force_y_n': state['sources']['load_' + target.removeprefix('solution_')]['force_y_n'],
            'timeout_s': scenario['solve_timeout_s']}


def review(scenario: dict, state: dict, target: str, payload: Any) -> list[dict]:
    if target != 'review':
        # These payloads are broker-owned and reconstructed from sealed raw job files
        # on every replay. A user put to these nodes is rejected by the environment.
        return deepcopy(payload['checks'])
    expected_cases = []
    for point in sorted(scenario['loads']):
        result = state['artifacts']['solution_' + point]['payload']
        qoi = result['qoi']
        passed = abs(qoi['uy_mm']) <= state['sources']['requirement']['max_tip_mm']
        expected_cases.append({'point': point, 'uy_mm': qoi['uy_mm'], 'rfy_n': qoi['rfy_n'],
                               'meets_requirement': passed})
    expected = {'cases': expected_cases,
                'claim': 'requirements_met' if all(x['meets_requirement'] for x in expected_cases) else 'needs_review',
                'requirement_revision': state['sources']['requirement']['revision']}
    from .workbench_review import _equal
    return [{'check': 'native_review_content', 'passed': _equal(payload, expected)}]


def public_contract(scenario: dict) -> dict:
    return {'family': FAMILY, 'graph': graph(scenario),
            'actions': 'solve(target) creates a broker-owned solution; check; put review; advance; submit',
            'action_format': {
                'selector': 'op',
                'required_fields': {'solve': ['op','target'], 'check': ['op','target'],
                                    'put': ['op','target','basis','payload'],
                                    'advance': ['op'], 'submit': ['op','claim']},
                'solve_example': {'op': 'solve', 'target': 'solution_limit'},
                'put_target': 'review',
                'put_basis': 'Copy the current observe.dependencies.review object unchanged.',
                'put_payload': 'Build review_fields and case_fields from observed native measurements and the current requirement.',
                'submit_claim': 'Use the claim in the verified review payload.',
                'cli_session_argument': 'Pass the session directory path, not the session_id.'},
            'review_fields': ['cases','claim','requirement_revision'],
            'case_fields': ['point','uy_mm','rfy_n','meets_requirement'],
            'claim': 'requirements_met if all abs(uy_mm) <= current max_tip_mm; else needs_review',
            'validity_checks': {'beam_displacement_relative_tolerance': 0.03,
                                'force_balance_relative_tolerance': 1e-5,
                                'absolute_tolerance': 1e-6},
            'native_budget': {'max_solver_calls': scenario['max_solver_calls'],
                              'per_call_timeout_s': scenario['solve_timeout_s']},
            'scope': 'Fixed calibration beam only; no stress, fatigue, joints, geometric design, or engineering approval. '
                     'Preliminary numerical tolerances require target-machine and expert validation. '
                     'No arbitrary deck/code is accepted. Raw files are re-read, not re-solved, during observation.'}


def limitations(state: dict) -> dict:
    calls = state['counts'].get('solver_calls', 0)
    started = state['counts'].get('native_processes_started', 0)
    return {'public_regression_only': True, 'publishable': False,
            'isolated_transfer_verified': False,
            'solver_execution': 'local_process_attempted' if started else 'not_performed',
            'native_requests': calls, 'native_processes_started': started,
            'identity_scope': 'declared_subject_and_local_executable_hash', 'sandboxed': False,
            'budget_scope': 'brokered_actions_and_solver_attempts; single-thread request, no OS memory quota',
            'engineering_approval': False}
