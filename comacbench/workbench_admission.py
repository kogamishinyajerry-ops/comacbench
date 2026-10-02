"""Maintainer-only audit of a public trial's host controls and lossless tool records.

Not an authentication or hostile-administrator boundary. Agent prose is never evidence
of protocol conformance. Historical reports are not modified by this module.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def unknown_admission(kind: str = "user_agent", reason: str = "No complete, verified host-control and tool-call record supplied.") -> dict:
    return {"protocol_conformance": "unknown" if kind == "user_agent" else "not_applicable",
            "reference_exposure": "unknown" if kind == "user_agent" else "reference_or_control",
            "score_admissible": False, "deviation_reasons": [reason] if kind == "user_agent" else ["Reference and negative controls are not model scores."],
            "evaluation_scope": "same_public_task_development_repeat",
            "unseen_generalization_score_admissible": False,
            "admission_evidence": {}, "trust_scope": "trusted local maintainer audit; not endpoint or OS attestation"}


CONTRACT_SHA256 = 'd6b1d694ed9c92093b9b022b1dcc208b5bf046b2608cdbaee0319052008b9271'
MAX_RECORD = 8_000_000  # raw native text <= 1 MB plus JSON escaping/envelope
MAX_LOG = 128_000_000


def _loads(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key: ' + key)
            result[key] = value
        return result
    if not isinstance(text, str) or len(text.encode('utf-8')) > MAX_RECORD:
        raise ValueError('record too large or not text')
    value = json.loads(text, object_pairs_hook=pairs,
                       parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON: ' + x)))
    json.dumps(value, allow_nan=False)  # also rejects overflow such as 1e999
    return value


def _read(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError('not an ordinary evidence file: ' + path.name)
    with path.open('rb') as f:
        raw = f.read(MAX_RECORD + 1)
    value = _loads(raw.decode('utf-8'))
    if type(value) is not dict:
        raise ValueError('expected JSON object: ' + path.name)
    return value


def _lines(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_LOG:
        raise ValueError('invalid/oversized log: ' + path.name)
    rows = []
    with path.open('rb') as f:
        while raw := f.readline(MAX_RECORD + 1):
            if not raw.endswith(b'\n'):
                raise ValueError('truncated/oversized JSONL record: ' + path.name)
            row = _loads(raw.decode('utf-8'))
            if type(row) is not dict or not isinstance(row.get('type'), str):
                raise ValueError('invalid record type: ' + path.name)
            rows.append(row)
            if len(rows) > 10000:
                raise ValueError('too many audit records')
    return rows


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _contract_sha(path):
    # Git for Windows may export CRLF. Freeze UTF-8 contract content with LF
    # transport newlines; JSON string escapes and every other byte remain locked.
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _index(rows, field, label):
    result = {}
    for r in rows:
        key = r[field]
        if not isinstance(key, str) or not key or key in result:
            raise ValueError('duplicate/invalid ' + label + ' callId: ' + str(key))
        result[key] = r
    return result


def _schema_accepts(value, schema):
    """Validate the frozen JSON tool schema at the broker-entry boundary."""
    kind = schema.get('type')
    types = {'object': (dict,), 'array': (list,), 'string': (str,),
             'boolean': (bool,), 'number': (int, float)}
    if kind in types and type(value) not in types[kind]:
        return False
    if 'enum' in schema and value not in schema['enum']:
        return False
    if kind == 'object':
        properties = schema.get('properties', {})
        return (set(schema.get('required', [])) <= value.keys()
                and (schema.get('additionalProperties') is not False or value.keys() <= properties.keys())
                and all(_schema_accepts(v, properties[k]) for k, v in value.items() if k in properties))
    return kind != 'array' or all(_schema_accepts(v, schema['items']) for v in value)


def _text_result(row):
    content = row['content']
    if (type(row['is_error']) is not bool or type(content) is not list or len(content) != 1
            or set(content[0]) != {'type', 'text'} or content[0]['type'] != 'text'
            or not isinstance(content[0]['text'], str)):
        raise ValueError('unexpected host response content')
    return content[0]['text']


def _native_payload(value):
    if type(value) is not dict or set(value) != {'job_id', 'receipt_sha256', 'process_started', 'duration_s', 'valid', 'qoi', 'checks'}:
        raise ValueError('native payload fields')
    if (type(value['process_started']) is not bool or type(value['valid']) is not bool
            or type(value['duration_s']) not in (float, int) or value['duration_s'] < 0
            or type(value['qoi']) is not dict or set(value['qoi']) not in (set(), {'uy_mm', 'rfy_n'})
            or any(type(x) not in (int, float) for x in value['qoi'].values())):
        raise ValueError('native payload types')
    for c in value['checks']:
        if (set(c) not in ({'check', 'passed'}, {'check', 'passed', 'reason'})
                or not isinstance(c['check'], str) or type(c['passed']) is not bool
                or ('reason' in c and not isinstance(c['reason'], str))):
            raise ValueError('native check fields')


class ResponseAudit:
    """Positive per-operation projection against replayed CURRENT state.

    Uses only recorded native payloads, never executes a solver. The caller's
    snapshot has already re-read the physical archive under its original engine.
    """
    def __init__(self, data, session=None):
        from . import workbench as wb
        self.wb, self.data, self.session = wb, data, session
        self.manifest = data['manifest']
        self.scenario = self.manifest['scenario']
        self.state = wb._initial(self.scenario)
        self.index = 0

    def check(self, request, value):
        from .workbench_public import public_observation, NATIVE_FILES
        if type(value) is not dict or set(value) not in ({'result'}, {'result', 'observation'}):
            raise ValueError('public response fields')
        result = value['result']
        if type(result) is not dict or type(result.get('ok')) is not bool or type(result.get('code')) is not str:
            raise ValueError('result types')
        op = request.get('op') if isinstance(request, dict) else None
        if 'observation' in value:
            if op == 'observe':
                expected = {'ok': True, 'code': 'observed'}
            elif op in {'solve', 'check', 'put', 'advance', 'submit'}:
                event = self.data['events'][self.index]
                if event['action'] != request:
                    raise ValueError('action does not match environment event')
                evidence = None
                if op == 'solve' and result['code'] in {'native_evidence_recorded', 'native_solve_failed'}:
                    evidence = value['observation']['artifacts'][request['target']]['payload']
                    _native_payload(evidence)
                    if evidence['job_id'] != f'{self.index + 1:06d}' or evidence['receipt_sha256'] != self.wb.digest(self.data['native_receipts'][evidence['job_id']]):
                        raise ValueError('native receipt binding')
                expected = self.wb._transition(self.scenario, self.state, request, evidence)
                if expected != event['result']:
                    raise ValueError('replayed result mismatch')
                self.index += 1
            else:
                raise ValueError('observation not allowed for operation')
            if _digest(result) != _digest(expected) or _digest(value['observation']) != _digest(public_observation(self.wb._observation(self.manifest, self.state))):
                raise ValueError('response differs from positive current projection')
        elif result['code'] == 'native_text':
            if (op != 'read_native' or set(result) != {'ok', 'code', 'target', 'name', 'text'}
                    or result['ok'] is not True or result['target'] != request['target']
                    or result['name'] != request['name'] or result['name'] not in NATIVE_FILES
                    or type(result['text']) is not str or len(result['text'].encode()) > 3_000_000):
                raise ValueError('native text contract')
            job = self.state['artifacts'][result['target']]['payload']['job_id']
            if self.session is None:
                raise ValueError('native text audit requires the original session path')
            root = self.session / 'native' / job
            for directory in (self.session, self.session / 'native', root):
                self.wb._ordinary(directory, directory=True)
            path = root / result['name']
            self.wb._ordinary(path)
            if (path.stat().st_size > 1_000_000 or _sha(path) != self.data['native_receipts'][job]['files'][result['name']]
                    or path.read_text(encoding='utf-8', errors='replace') != result['text']):
                raise ValueError('native text archive mismatch')

        else:
            common = {'public_request_denied', 'public_target_denied', 'public_json_denied', 'host_io_error',
                      'broker_process_failed', 'broker_invalid_json'}
            allowed = common | ({'public_file_denied', 'native_file_unavailable', 'native_file_too_large'} if op == 'read_native' else set())
            if result['code'] == 'workbench_error':
                import re
                if set(result) != {'ok', 'code', 'detail'} or not isinstance(result['detail'], str) or not re.fullmatch(r'[a-z0-9_]{1,80}', result['detail']):
                    raise ValueError('workbench error contract')
            elif result['code'] not in allowed or set(result) != {'ok', 'code'}:
                raise ValueError('operation result fields/code')
            if result['ok'] is not False:
                raise ValueError('error result marked successful')


def _prompt_checks(control, rows, host, source):
    contract_path = source / 'comacbench/public_input_v2.json'
    if _contract_sha(contract_path) != CONTRACT_SHA256:
        raise ValueError('audit public contract source changed')
    contract = _read(contract_path)
    if (control.get('protocol') != 'comacbench.public-boundary.v2'
            or control.get('contract_version') != contract['version'] or control.get('contract_sha256') != CONTRACT_SHA256):
        raise ValueError('unsupported admission contract; old records lack actual per-round input evidence')
    checks = {'frozen_contract': control['complete_public_system'] == contract['sections'][0]['text']
              and control['public_user_entry'] == contract['user_entry'] and control['runtime'] == contract['runtime']}
    assemblies = [r for r in rows if r['type'] == 'assembly']
    inputs = [r for r in rows if r['type'] == 'model_input']
    checks['controlled_assemblies'] = all(type(r['number']) is int for r in assemblies) and bool(assemblies) and len(assemblies) <= 64 and [r['number'] for r in assemblies] == list(range(1, len(assemblies)+1))
    for r in assemblies:
        actual = {k:r[k] for k in ('sections','contexts','tools')}
        checks['controlled_assemblies'] &= (actual == {k:contract[k] for k in actual}
            and r['contract_version'] == contract['version'] and r['contract_sha256'] == CONTRACT_SHA256
            and r['model'] == control['model'] and r['input_sha256'] == _digest(actual)
            and r['public_system_sha256'] == hashlib.sha256('\n\n'.join(s['text'] for s in r['sections']).encode()).hexdigest())
    checks['actual_model_inputs'] = all(type(r['number']) is int and type(r['assembly_number']) is int for r in inputs) and bool(inputs) and len(inputs) <= 64 and [r['number'] for r in inputs] == list(range(1,len(inputs)+1))
    for r in inputs:
        if not 1 <= r['assembly_number'] <= len(assemblies) or assemblies[r['assembly_number']-1]['seq'] >= r['seq']:
            raise ValueError('model input assembly association')
        actual = {k:r[k] for k in ('messages','tools')}
        valid = (r['contract_version'] == contract['version'] and r['contract_sha256'] == CONTRACT_SHA256
                 and r['model'] == control['model'] and r['tools'] == contract['tools'] and r['input_sha256'] == _digest(actual))
        systems = [m for m in r['messages'] if m['role'] == 'system']
        users = [m for m in r['messages'] if m['role'] == 'user']
        valid &= len(systems) == 1 and systems[0]['content'] == [{'type':'text','text':contract['sections'][0]['text']}]
        valid &= len(users) == 1 and users[0]['content'] == [{'type':'text','text':contract['user_entry']}]
        for m in r['messages']:
            valid &= m['role'] in {'system','user','assistant','tool'}
            if m['role'] == 'tool':
                h = host[m['toolCallId']]
                valid &= h['content'] == m['content'] and h['is_error'] == m['isError'] and h['seq'] < r['seq']
            if m['role'] == 'assistant':
                valid &= m['source']['kind'] == 'model' and all(m['source'][k] == control['model'][k] for k in ('provider','model'))
        checks['actual_model_inputs'] &= valid
    return checks


def audit_trial(data: dict, directory: Path, *, session: Path | None = None) -> dict:
    admission = unknown_admission(data["manifest"]["subject"]["kind"])
    if data["manifest"]["subject"]["kind"] != "user_agent":
        return admission
    issues = []
    try:
        control = _read(directory / "control.json")
        rows = _lines(directory / "boundary.jsonl")
        stream = _lines(directory / "dsh-events.jsonl")
        end = _read(directory / "execution.json")
        for name in ("control.json", "boundary.jsonl", "dsh-events.jsonl", "execution.json"):
            admission["admission_evidence"][name] = _sha(directory / name)
        manifest = data["manifest"]
        source = Path(__file__).resolve().parents[1]
        checks = {
            "control_protocol": control["protocol"] == "comacbench.public-boundary.v2",
            "session_binding": control["session_manifest_sha256"] == manifest["manifest_sha256"],
            "engine_binding": control["engine_sha256"] == manifest["engine_sha256"],
            "plugin_binding": control["plugin_sha256"] == _sha(source / "scripts/dsh_public_boundary.mjs"),
            "gateway_binding": control["gateway_sha256"] == _sha(source / "comacbench/workbench_public.py"),
            "fixed_budget": control["budget"] == {"actions": 32, "solver_calls": 6, "solve_timeout_s": 120, "tool_calls": 96, "model_assemblies": 64},
            "existing_model": control["model"]["provider"] == "zai-coding-cn" and control["model"]["model"] == "glm-4.7",
            "fresh_context": control["fresh_headless_session"] is True and control["creation_source"] == "startup",
            "context_boundary": control["runtime_context_suppressed"] is True and control["mode"] == "native",
            "entry_contract_probed": control.get("public_observe_success") is True,
            "scope": control["task_scope"] == "same_public_task_development_repeat" and control["prior_public_task_exposure"] is True,
            "live_denials": control["probe"]["all_denied"] is True and control["probe"]["schemas"] == ["workbench"]
                            and len(control["probe"]["probes"]) == 9 and all(p["is_error"] is True for p in control["probe"]["probes"]),
            "audit_sequence": all(type(r["seq"]) is int for r in rows) and [r["seq"] for r in rows] == list(range(1, len(rows) + 1)),
            "execution_closed": type(end["exit_code"]) is int and end["exit_code"] == 0 and type(end["attempt_count"]) is int and end["attempt_count"] == 1 and end["model_or_tool_overrides"] == "boundary_only",
            "fresh_session_stream": len([r for r in stream if r["type"] == "session"]) == 1
                and next(r for r in stream if r["type"] == "session")["sessionId"] == control["agent_id"],
            "completed_stream": any(r["type"] == "status" and r.get("phase") == "turn_end"
                                    and r.get("reason", {}).get("kind") == "completed" for r in stream)
                                and stream[-1]["type"] == "final",
        }
        admission["audit_checks"] = checks
        ready = [r for r in rows if r["type"] == "ready"]
        assemblies = [r for r in rows if r["type"] == "assembly"]
        prompts = [r for r in rows if r["type"] == "prompt_probe"]
        checks["public_prompt_probed"] = (len(prompts) == 1 and len(prompts[0]["sections"]) == 1
            and prompts[0]["sections"][0]["text"] == control["complete_public_system"]
            and not any(c["text"] for c in prompts[0]["contexts"]) and prompts[0]["schemas"] == ["workbench"])
        checks["startup_boundary"] = (len(ready) == 1 and bool(assemblies)
            and len(assemblies) <= 64 and ready[0]["seq"] < assemblies[0]["seq"]
            and all(r["schemas"] == ["workbench"] and not any(c["text"] for c in r["contexts"])
                    and r["model"] == control["model"] for r in assemblies)
            and not any(r["type"] == "blocked" for r in rows))
        calls = [r for r in stream if r['type'] == 'tool_call']
        results = [r for r in stream if r['type'] == 'tool_result']
        host_results = [r for r in rows if r['type'] == 'tool_result' and not r['call_id'].startswith('boundary-probe-')]
        brokers = [r for r in rows if r['type'] == 'broker' and not r['call_id'].startswith('boundary-probe-')]
        # Validate uniqueness BEFORE building lookups, including extra broker IDs.
        cm = _index(calls, 'callId', 'model call')
        rm = _index(results, 'callId', 'model result')
        hm = _index(host_results, 'call_id', 'host result')
        bm = _index(brokers, 'call_id', 'broker receipt')
        checks['all_calls_captured'] = 0 < len(cm) <= 96 and cm.keys() == rm.keys() == hm.keys() and bm.keys() <= cm.keys()
        if not checks['all_calls_captured']:
            raise ValueError('missing/extra model, host or broker callId')
        checks['only_public_tool'] = all(c['tool'] == 'workbench' for c in calls)
        checks['call_arguments_match'] = all(c['tool'] == hm[c['callId']]['name'] and c['input'] == hm[c['callId']]['arguments'] for c in calls)
        positions = {id(r): i for i,r in enumerate(stream)}
        request_schema = _read(source / 'comacbench/public_input_v2.json')['tools'][0]['parameters']
        responses = ResponseAudit(data, session)
        paths = []
        checks["broker_payload_parseable"] = True
        # Host order binds environment actions, including legal rejected actions.
        for h in host_results:
            key = h['call_id']; c = cm[key]; r = rm[key]
            if positions[id(c)] >= positions[id(r)]:
                raise ValueError('result before model call: ' + key)
            text = _text_result(h)
            if r['result'] != text:
                raise ValueError('model/host result mismatch: ' + key)
            broker = bm.get(key)
            if broker is None:
                # DSH validation/guard denial BEFORE broker. No receipt is invented.
                err = h.get('error') or {}
                msg = err.get('message', '')
                if (not h['is_error'] or set(err) - {'message','info'} or not isinstance(msg,str)
                        or text != 'Error: ' + msg or not (msg in {'invalid arguments: \"request\" must be an object', 'invalid arguments: \"request\" is required'}
                        or msg in {'COMACBench public capability boundary: tool denied', 'COMACBench fixed tool-call budget exhausted'})):
                    raise ValueError('missing broker without a recognized pre-gateway denial: ' + key)
                paths.append({'call_id':key, 'path':'pre_gateway_denial'})
                continue
            if not _schema_accepts(c['input'], request_schema):
                raise ValueError('broker reached with schema-rejected arguments: ' + key)
            if broker['seq'] >= h['seq'] or broker['request'] != c['input']['request'] or h['is_error']:
                raise ValueError('broker association/order/outcome: ' + key)
            exit_code = broker['exit_code']
            if exit_code is not None and type(exit_code) is not int:
                raise ValueError('broker exit code type')
            value = _loads(text)  # EACH actual model-visible response, not just receipts
            if exit_code != 0 or broker.get('process_error'):
                expected = {'result': {'ok':False, 'code':'broker_process_failed'}}
                path = 'broker_failure'
            else:
                try:
                    expected = _loads(broker['stdout'])
                    path = 'gateway_response'
                except (ValueError, UnicodeError, RecursionError):
                    checks['broker_payload_parseable'] = False
                    expected = {'result': {'ok':False, 'code':'broker_invalid_json'}}
                    path = 'broker_failure'
            if _digest(value) != _digest(expected):
                raise ValueError('broker/model response mismatch: ' + key)
            responses.check(c['input']['request'], value)
            if 'observation' in value and c['input']['request']['op'] != 'observe':
                path = 'task_action' if value['result']['ok'] else 'task_action_rejected'
            paths.append({'call_id':key, 'path':path})
        checks['actions_match_environment'] = responses.index == len(data['events'])
        checks['per_call_receipts_and_projection'] = True
        admission['call_paths'] = paths
        checks.update(_prompt_checks(control, rows, hm, source))
        issues = [key for key, passed in checks.items() if not passed]
        admission["audit_checks"] = checks
        admission["tool_calls"] = len(calls)
        admission["prior_public_task_exposure"] = True
        if not issues:
            admission.update(protocol_conformance="conformant", reference_exposure="not_observed_in_recorded_run",
                             score_admissible=True, deviation_reasons=[])
        else:
            admission["deviation_reasons"] = ["Host audit did not establish conformance: " + ", ".join(issues)]
    except (OSError, ValueError, KeyError, TypeError, AttributeError, StopIteration, IndexError, RecursionError) as exc:
        admission["deviation_reasons"] = ["Incomplete or inconsistent host audit: " + type(exc).__name__ + ": " + str(exc)[:300]]
    return admission


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True, type=Path)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    from .workbench_report import export_report
    print(json.dumps(export_report(args.session, args.out, admission_evidence=args.audit)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
