"""Bounded, trusted-local CalculiX bridge for a fixed calibration model.

No candidate code or arbitrary INP is executed. Input generation follows the
existing aviation-structures-v2 C3D20 topology, at reduced loads. This is a
calibration bridge, NOT a general FEA/design benchmark or a sandbox.
"""
from __future__ import annotations

import hashlib
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time
from typing import Any

MAX_JOB_BYTES = 64 * 1024 * 1024
MAX_FILES = 40
VERSION = '2.23'
TEMPLATE = 'c3d20-cantilever-calibration-v1'
NUM = r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[eEdD][-+]?\d+)?'


def _api():
    from . import workbench
    return workbench


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _kill(p: subprocess.Popen) -> None:
    if os.name == 'nt':
        # Kill the process tree, not just the leader. Never interpolate a shell.
        killer = Path(os.environ.get('SYSTEMROOT', r'C:\Windows')) / 'System32' / 'taskkill.exe'
        try:
            subprocess.run([str(killer), '/PID', str(p.pid), '/T', '/F'],
                           capture_output=True, timeout=10, check=False)
        except (OSError, subprocess.TimeoutExpired):
            pass
        if p.poll() is None:
            p.kill()
    else:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired as exc:
        raise _api().WorkbenchError('process_termination_unconfirmed') from exc


def _process(command: list[str], root: Path, log: Path, timeout_s: float) -> dict[str, Any]:
    env = {k: v for k, v in os.environ.items() if k in
           {'PATH', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'TMPDIR',
            'LD_LIBRARY_PATH', 'DYLD_LIBRARY_PATH'}}
    # Deliberate single-thread profile; other limits are not OS-enforced.
    env.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
               NUMBER_OF_CPUS='1', CCX_NPROC_RESULTS='1', LANG='C', LC_ALL='C')
    started = time.monotonic()
    result = {'exit_code': None, 'timed_out': False, 'output_limit': False,
              'launch_error': None, 'duration_s': 0.0, 'process_started': False}
    with log.open('xb') as output:
        try:
            p = subprocess.Popen(command, cwd=root, stdout=output, stderr=subprocess.STDOUT,
                                 stdin=subprocess.DEVNULL, env=env,
                                 start_new_session=(os.name != 'nt'))
            result['process_started'] = True
        except OSError as exc:
            result['launch_error'] = type(exc).__name__
            result['duration_s'] = round(time.monotonic() - started, 6)
            return result
        try:
            while p.poll() is None:
                result['timed_out'] = time.monotonic() - started > timeout_s
                # A polling limit, not a hard filesystem quota.
                result['output_limit'] = sum(x.stat().st_size for x in root.iterdir()
                                             if x.is_file()) > MAX_JOB_BYTES
                if result['timed_out'] or result['output_limit']:
                    _kill(p)
                    break
                time.sleep(0.05)
            result['exit_code'] = p.returncode
        except BaseException:
            _kill(p)
            raise
    result['duration_s'] = round(time.monotonic() - started, 6)
    return result


def executor(path: str | None = None) -> dict[str, Any]:
    """An explicit invalid path is an error, never silently replaced from PATH."""
    import tempfile
    api = _api()
    declared = path or os.environ.get('CCX_BIN')
    chosen = declared or shutil.which('ccx') or (
        '/opt/homebrew/bin/ccx' if Path('/opt/homebrew/bin/ccx').is_file() else None)
    if not chosen:
        raise api.WorkbenchError('ccx_missing: set CCX_BIN to an existing authorized binary')
    binary = Path(chosen).expanduser().resolve(strict=True)
    api._ordinary(binary)
    if not os.access(binary, os.X_OK):
        raise api.WorkbenchError('ccx_not_executable')
    before = sha(binary)
    with tempfile.TemporaryDirectory(prefix='comacbench-ccx-probe-') as tmp:
        root = Path(tmp)
        result = _process([str(binary), '-v'], root, root / 'version.log', 5)
        text = (root / 'version.log').read_bytes()[:8192].decode('utf-8', errors='replace')
    versions = re.findall(r'\bVersion\s+(\d+\.\d+)\b', text, re.I)
    # Upstream CalculiX.c handles -v through stop.f, which calls exit(201).
    # Permit that status only for the exact version banner, never for a solve.
    # https://github.com/Dhondtguido/CalculiX/blob/master/src/stop.f
    if (result['exit_code'] not in (0, 201) or result['timed_out']
            or result['output_limit'] or result['launch_error'] is not None
            or not result['process_started']
            or not re.fullmatch(r'\s*This is Version 2\.23\s*', text)):
        raise api.WorkbenchError(f"ccx_version_unverified: expected {VERSION}; observed {versions}; exit={result['exit_code']}")
    if sha(binary) != before:
        raise api.WorkbenchError('ccx_changed_during_probe')
    return {'path': str(binary), 'sha256': before, 'version': VERSION,
            'version_output': text, 'version_exit_code': result['exit_code'], 'os': os.name,
            'trust_scope': 'operator_supplied_local_binary_not_attestation',
            'library_env_sha256': api.digest({k: os.environ.get(k) for k in
                                            ('LD_LIBRARY_PATH', 'DYLD_LIBRARY_PATH')})}


def validate_executor(value: Any) -> None:
    api = _api()
    keys = {'path', 'sha256', 'version', 'version_output', 'version_exit_code', 'os', 'trust_scope', 'library_env_sha256'}
    if (not isinstance(value, dict) or set(value) != keys
            or not isinstance(value['path'], str) or not Path(value['path']).is_absolute()
            or not isinstance(value['sha256'], str) or not api.SHA.fullmatch(value['sha256'])
            or not isinstance(value['library_env_sha256'], str)
            or not api.SHA.fullmatch(value['library_env_sha256'])
            or value['version'] != VERSION or value['os'] not in ('posix', 'nt')
            or type(value['version_exit_code']) is not int or value['version_exit_code'] not in (0, 201)
            or value['trust_scope'] != 'operator_supplied_local_binary_not_attestation'
            or not isinstance(value['version_output'], str) or len(value['version_output']) > 8192):
        raise api.WorkbenchError('native_executor_contract')


def mesh() -> tuple[list, list, list[int], list[int]]:
    nodes, elements, index = [], [], {}
    offsets = ((0,0,0),(2,0,0),(2,2,0),(0,2,0),(0,0,2),(2,0,2),(2,2,2),(0,2,2),
               (1,0,0),(2,1,0),(1,2,0),(0,1,0),(1,0,2),(2,1,2),(1,2,2),(0,1,2),
               (0,0,1),(2,0,1),(2,2,1),(0,2,1))
    for k in range(2):
        for j in range(4):
            for i in range(20):
                conn = []
                for dx, dy, dz in offsets:
                    key = (2*i+dx, 2*j+dy, 2*k+dz)
                    if key not in index:
                        index[key] = len(nodes) + 1
                        nodes.append((index[key], key[0]*2.5, -5+key[1]*1.25, -2.5+key[2]*1.25))
                    conn.append(index[key])
                elements.append((len(elements)+1, conn))
    root = [n[0] for n in nodes if n[1] == 0]
    tip = [n[0] for n in nodes if n[1] == 100]
    return nodes, elements, root, tip


def deck(force_y_n: float) -> bytes:
    if type(force_y_n) not in (int, float) or not -200 <= force_y_n <= -10:
        raise _api().WorkbenchError('force_outside_calibration_domain')
    nodes, elements, root, tip = mesh()
    lines = ['** COMACBench fixed calibration template; mm N MPa', '*NODE']
    lines += [f'{n}, {x:.6f}, {y:.6f}, {z:.6f}' for n, x, y, z in nodes]
    lines.append('*ELEMENT, TYPE=C3D20, ELSET=EALL')
    for num, conn in elements:
        values = [num] + conn
        lines += [', '.join(map(str, values[i:i+16])) for i in range(0, 21, 16)]
    for name, ids in (('NROOT', root), ('NTIP', tip)):
        lines.append(f'*NSET, NSET={name}')
        lines += [', '.join(map(str, ids[i:i+16])) for i in range(0, len(ids), 16)]
    lines += ['*MATERIAL, NAME=STEEL', '*ELASTIC', '210000.0, 0.3', '*DENSITY', '7.85e-9',
              '*SOLID SECTION, ELSET=EALL, MATERIAL=STEEL', '*BOUNDARY', 'NROOT, 1, 3, 0.0',
              '*STEP', '*STATIC']
    for node in tip:
        lines += ['*CLOAD', f'{node}, 2, {force_y_n/len(tip):.12f}']
    lines += ['*NODE PRINT, NSET=NTIP', 'U', '*NODE PRINT, NSET=NROOT', 'RF',
              '*NODE FILE', 'U, RF', '*END STEP']
    return ('\n'.join(lines) + '\n').encode('ascii')


def _inventory(root: Path) -> dict[str, str]:
    api = _api()
    api._ordinary(root, directory=True)
    files = list(root.iterdir())
    if len(files) > MAX_FILES:
        raise api.WorkbenchError('native_file_count_limit')
    result, size = {}, 0
    for f in files:
        api._ordinary(f)
        if not re.fullmatch(r'[A-Za-z0-9_.-]{1,80}', f.name):
            raise api.WorkbenchError('native_file_name')
        size += f.stat().st_size
        if size > MAX_JOB_BYTES:
            raise api.WorkbenchError('native_archive_size_limit')
        if f.name != 'receipt.json':
            result[f.name] = sha(f)
    return result


def run_job(root: Path, request: dict, bound: dict) -> None:
    """Reserve evidence directory before launch; interrupted jobs are never retried silently."""
    api = _api()
    validate_executor(bound)
    root.mkdir(exist_ok=False)
    api._write_new(root / 'request.json', request)
    (root / 'model.inp').write_bytes(deck(request['force_y_n']))
    command = [bound['path'], '-i', 'model']
    binary = Path(bound['path'])
    try:
        compatible = (binary.is_file() and sha(binary) == bound['sha256']
                      and os.name == bound['os'] and api.digest({k: os.environ.get(k) for k in
                         ('LD_LIBRARY_PATH', 'DYLD_LIBRARY_PATH')}) == bound['library_env_sha256'])
    except OSError:
        compatible = False
    if compatible:
        status = _process(command, root, root / 'model.solver.log', request['timeout_s'])
        # Identity is checked again after execution, not only at start.
        status['identity_unchanged'] = binary.is_file() and sha(binary) == bound['sha256']
    else:
        (root / 'model.solver.log').write_text('Bound executor unavailable or changed.\n', encoding='utf-8')
        status = {'exit_code': None, 'timed_out': False, 'output_limit': False,
                  'launch_error': 'executor_changed', 'duration_s': 0.0,
                  'process_started': False, 'identity_unchanged': False}
    status.update(command=command, executor_sha256=bound['sha256'])
    api._write_new(root / 'status.json', status)
    api._write_new(root / 'receipt.json', {'protocol': 'comacbench.native-job.v1',
                                         'files': _inventory(root)})


def parse_dat(text: str) -> dict[str, float]:
    """Require exact output sets, complete unique node rosters, finite signed data and final time."""
    api = _api()
    _, _, root, tip = mesh()
    headers = {'uy_mm': r'displacements \(vx,vy,vz\) for set NTIP and time\s+(' + NUM + ')',
               'rfy_n': r'forces \(fx,fy,fz\) for set NROOT and time\s+(' + NUM + ')'}
    lines, values = text.splitlines(), {}
    for key, pattern in headers.items():
        found = [(i, re.search(pattern, line, re.I)) for i, line in enumerate(lines)]
        found = [(i, m) for i, m in found if m]
        if len(found) != 1:
            raise api.WorkbenchError('native_output_block_count')
        i, match = found[0]
        number = lambda s: float(s.replace('D', 'E').replace('d', 'e'))
        if not math.isclose(number(match[1]), 1.0, rel_tol=0, abs_tol=1e-10):
            raise api.WorkbenchError('native_output_not_final')
        rows = {}
        for line in lines[i+1:]:
            if not line.strip() and not rows:
                continue
            m = re.fullmatch(r'\s*(\d+)\s+(' + NUM + r')\s+(' + NUM + r')\s+(' + NUM + r')\s*', line)
            if not m:
                break
            node = int(m[1])
            row = [number(m[g]) for g in (2,3,4)]
            if node in rows or not all(math.isfinite(v) for v in row):
                raise api.WorkbenchError('native_duplicate_or_nonfinite_node')
            rows[node] = row
        expected = set(tip if key == 'uy_mm' else root)
        if set(rows) != expected:
            raise api.WorkbenchError('native_node_roster_mismatch')
        y = [v[1] for v in rows.values()]
        values[key] = max(y, key=abs) if key == 'uy_mm' else math.fsum(y)
    return values


def review_job(root: Path, request: dict, bound: dict) -> dict:
    api = _api()
    receipt = api.read_json(root / 'receipt.json')
    if (not isinstance(receipt, dict) or set(receipt) != {'protocol','files'}
            or receipt['protocol'] != 'comacbench.native-job.v1'
            or receipt['files'] != _inventory(root)):
        raise api.WorkbenchError('native_archive_changed')
    if api.read_json(root / 'request.json') != request:
        raise api.WorkbenchError('native_request_mismatch')
    if (root / 'model.inp').read_bytes() != deck(request['force_y_n']):
        raise api.WorkbenchError('native_input_mismatch')
    status = api.read_json(root / 'status.json')
    keys = {'exit_code','timed_out','output_limit','launch_error','duration_s','process_started',
            'identity_unchanged','command','executor_sha256'}
    if (not isinstance(status, dict) or set(status) != keys
            or status['command'] != [bound['path'], '-i', 'model']
            or status['executor_sha256'] != bound['sha256']
            or any(type(status[k]) is not bool for k in ('timed_out','output_limit','process_started','identity_unchanged'))
            or (status['exit_code'] is not None and type(status['exit_code']) is not int)
            or type(status['duration_s']) not in (int,float) or not math.isfinite(status['duration_s'])
            or status['duration_s'] < 0):
        raise api.WorkbenchError('native_status_contract')
    payload = {'job_id': root.name, 'receipt_sha256': sha(root / 'receipt.json'),
               'process_started': status['process_started'], 'duration_s': status['duration_s'],
               'valid': False, 'qoi': {}, 'checks': []}
    log = (root / 'model.solver.log').read_text(encoding='utf-8', errors='replace')
    process_ok = (type(status['exit_code']) is int and status['exit_code'] == 0
                  and status['process_started'] and status['identity_unchanged']
                  and not status['timed_out'] and not status['output_limit'] and status['launch_error'] is None)
    checks = [{'check': 'process_completed', 'passed': process_ok},
              {'check': 'termination_log', 'passed': bool(re.search(r'\bJob finished\b', log))
               and not bool(re.search(r'\*ERROR|\bsegmentation fault\b', log, re.I))}]
    try:
        qoi = parse_dat((root / 'model.dat').read_text(encoding='ascii', errors='strict'))
        force = request['force_y_n']
        # Independent beam-theory cross-check; NOT a surrogate used instead of native solve.
        reference_u = force * 100**3 / (3 * 210000 * (5 * 10**3 / 12))
        checks += [{'check': 'signed_displacement_crosscheck', 'passed': math.isclose(qoi['uy_mm'], reference_u, rel_tol=0.03, abs_tol=1e-6)},
                   {'check': 'support_force_balance', 'passed': math.isclose(qoi['rfy_n'], -force, rel_tol=1e-5, abs_tol=1e-6)}]
        payload['qoi'] = qoi
    except (OSError, UnicodeError, api.WorkbenchError) as exc:
        checks.append({'check': 'native_data_readable', 'passed': False, 'reason': str(exc)[:300]})
    payload['checks'] = checks
    payload['valid'] = all(c['passed'] for c in checks)
    return payload
