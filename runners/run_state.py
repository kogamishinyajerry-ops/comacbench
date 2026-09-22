"""Versioned resume identity and atomic output publication for the five CLIs.

Metadata extends manifest.extra / result.artifacts; it is not an authenticity proof.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import shlex
import sys

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback
    import msvcrt

    def _msvcrt_flock(fd, _flags):
        fd.seek(0)
        msvcrt.locking(fd.fileno(), msvcrt.LK_NBLCK, 1)

    class fcntl:  # minimal shim of the POSIX module surface we use
        LOCK_EX = 1
        LOCK_NB = 2
        flock = staticmethod(_msvcrt_flock)

from . import common
from .providers import PROVIDER_PRESETS


def provider_identity(provider: str, model: str | None) -> dict:
    if provider == 'external':
        from comacbench.agent import identity
        return identity()
    preset = PROVIDER_PRESETS.get(provider, {})
    resolved = model or preset.get('model_default') or (
        os.environ.get('BM_MODEL') if provider == 'openai_compat' else None) or 'n/a'
    base = (os.environ.get(preset['base_env']) if preset.get('base_env') else None) or preset.get('base_default')
    if provider == 'openai_compat':
        base = os.environ.get('BM_API_BASE')
    return {'name': provider, 'model': resolved,
            'endpoint_sha256': common.sha256_bytes((base or '').encode()),
            'extra_body': preset.get('extra_body'), 'escalate': preset.get('escalate')}


def rerun_command(module: str, args, model: str) -> str:
    command = [sys.executable, '-m', module, '--tasks', str(Path(args.tasks).absolute()),
               '--out', str(Path(args.out).absolute()), '--provider', args.provider,
               '--seed', str(args.seed), '--resume']
    if model != 'n/a':
        command += ['--model', model]
    for name in ('hidden', 'iterate', 'limit', 'scaffold', 'allow_partial_oracle'):
        value = getattr(args, name, None)
        if value:
            command += ['--' + name.replace('_', '-')]
            if not isinstance(value, bool):
                command += [str(value)]
    if args.provider == 'external':
        command = ['env'] + [f'{k}={os.environ[k]}' for k in (
            'COMAC_AGENT_CONFIG', 'COMAC_AGENT_PACK_ROOT', 'COMAC_AGENT_AUDIT')] + command
    return 'cd ' + shlex.quote(str(common.BENCH_ROOT)) + ' && ' + shlex.join(command)


def referenced_files(tasks, tasks_dir, options) -> dict:
    """Hash declared files that are read outside input.assets (gold/QoI/scaffold)."""
    root = Path(tasks_dir).resolve().parent.parent
    paths = set()

    def visit(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in ('path', 'oracle_source', 'golden_workbook', 'h5_path',
                           'test_file', 'solution_file') and isinstance(item, str):
                    paths.add(root / item)
                else:
                    visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    for task in tasks:
        visit(task.spec)
        grader = task['grader']
        if grader.get('case_ref') and grader.get('qoi_script'):
            paths.add(root / grader['case_ref'] / grader['qoi_script'])
    if (options or {}).get('scaffold'):
        paths.add(common.BENCH_ROOT / options['scaffold'])
    return {str(p): common.sha256_file(p) if p.is_file() else 'MISSING'
            for p in sorted(paths)}


class RunState:
    """One locked CLI execution; preflight all cache entries before publishing."""

    def __init__(self, *, out_dir, tasks, prompts, adapter, provider, model, seed,
                 env_digest, assets, tasks_dir, rerun, resume, options=None,
                 extra=None, runtime_inputs=None):
        self.out = Path(out_dir)
        self.tasks = {t.id: t for t in tasks}
        if not self.tasks or len(self.tasks) != len(tasks):
            raise SystemExit('[resume] execution set must be nonempty with unique IDs')
        identity = {
            'version': 1, 'adapter': adapter, 'provider': provider_identity(provider, model),
            'seed': seed, 'environment_digest': env_digest, 'assets': assets,
            'python': sys.executable, 'options': options or {},
            'runtime_inputs': runtime_inputs or {},
            'referenced_files': referenced_files(tasks, tasks_dir, options),
            'tasks': {t.id: common.sha256_bytes(json.dumps(
                {'spec': t.spec, 'prompt': prompts[t.id]}, sort_keys=True,
                ensure_ascii=False, default=str).encode()) for t in tasks},
        }
        self.identity = identity
        self.token = common.sha256_bytes(json.dumps(identity, sort_keys=True, ensure_ascii=False).encode())
        self.manifest_args = dict(registry_id=tasks[0]['registry_id'], adapter=adapter,
            provider=provider, seed=seed, tasks_dir=tasks_dir, env_digest=env_digest,
            assets=assets, rerun_command=rerun, task_ids=list(self.tasks))
        self.extra = {**(extra or {}), 'resume_identity': identity,
                      'selected_task_ids': list(self.tasks)}
        self.resume = resume
        self.cached = {}
        self.lock = None

    def _reject(self, reason):
        raise SystemExit(f'[resume] {reason}; use a new --out directory (existing results preserved)')

    def __enter__(self):
        self.out.mkdir(parents=True, exist_ok=True)
        self.lock = (self.out / '.run.lock').open('a')
        try:
            try:
                fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:  # POSIX: BlockingIOError; Windows: PermissionError from msvcrt
                self._reject('another writer owns this output directory')
            files = sorted(self.out.glob('result_*.json'))
            manifest = self.out / 'run_manifest.json'
            if files or manifest.exists():
                if not self.resume:
                    self._reject('output already contains a run; matching runs require --resume')
                try:
                    saved = json.loads(manifest.read_text(encoding='utf-8'))
                except (OSError, ValueError):
                    self._reject('missing or unreadable run_manifest.json')
                if not isinstance(saved, dict) or not isinstance(saved.get('extra'), dict) or saved['extra'].get('resume_identity') != self.identity:
                    self._reject('run identity mismatch or legacy manifest without identity')
                expected_manifest = {
                    'registry_id': self.manifest_args['registry_id'],
                    'adapter': self.identity['adapter'],
                    'provider': self.identity['provider']['name'],
                    'seed': self.identity['seed'],
                    'environment_digest': self.identity['environment_digest'],
                    'assets': self.identity['assets'], 'n_tasks': len(self.tasks),
                }
                if (any(saved.get(k) != v for k, v in expected_manifest.items())
                        or any(saved['extra'].get(k) != v for k, v in self.extra.items())):
                    self._reject('manifest metadata disagrees with run identity')
                for file in files:
                    tid = file.stem.removeprefix('result_')
                    if tid not in self.tasks:
                        self._reject(f'unexpected cached task: {file.name}')
                    try:
                        row = json.loads(file.read_text(encoding='utf-8'))
                    except (OSError, ValueError):
                        self._reject(f'unreadable cached result: {file.name}')
                    task = self.tasks[tid]
                    expected = {'task_id': tid, 'registry_id': task['registry_id'],
                                'adapter': self.identity['adapter'],
                                'environment_digest': self.identity['environment_digest'],
                                'assets_revision': task['assets_revision']}
                    if not isinstance(row, dict) or any(row.get(k) != v for k, v in expected.items()):
                        self._reject(f'cached task identity mismatch: {file.name}')
                    artifacts = row.get('artifacts')
                    if not isinstance(artifacts, dict) or artifacts.get('resume_identity') != self.token:
                        self._reject(f'cached experiment identity mismatch: {file.name}')
                    score, gate = row.get('score'), row.get('validity_gate')
                    if type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 1 or gate not in (0, 1) or (gate == 0 and score != 0):
                        self._reject(f'invalid cached score/gate: {file.name}')
                    self._validate_result_fields(row, file)
                    self._verify_evidence(row, file)
                    self.cached[tid] = row
            self.finish()
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def _verify_evidence(self, row, file):
        """复用前核验归档证据字节——证据是 result 的一部分，不是可选附件。

        fail-closed：归档不可核验就拒绝复用并要求新目录，绝不因 result.json
        里曾有过满分就继续授予可复核状态。同时核对两处索引（result 内联索引
        与证据目录自描述清单）一致，以便发现只改了证据目录的改动。
        未声明 ``deliverable_files_dir`` 的 adapter 不受影响（向后兼容）。
        """
        artifacts = row.get('artifacts')
        if not isinstance(artifacts, dict):
            self._reject(f'missing artifacts: {file.name}')
        rel_dir = artifacts.get('deliverable_files_dir')
        if rel_dir is None:
            return  # 该 adapter 未归档原件
        if not isinstance(rel_dir, str) or not rel_dir.strip():
            self._reject(f'invalid evidence dir declaration: {file.name}')
        root = self.out.resolve()
        ev_dir = (self.out / rel_dir).resolve()
        if ev_dir != root and root not in ev_dir.parents:
            self._reject(f'evidence dir escapes the run directory: {rel_dir!r}')
        index = artifacts.get('deliverable_files')
        try:
            declared = json.loads(index) if isinstance(index, str) else index
        except ValueError:
            self._reject(f'unreadable cached evidence index: {file.name}')
        manifest_path = ev_dir / common.EVIDENCE_MANIFEST
        try:
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            self._reject(f'evidence manifest missing or unreadable: '
                         f'{rel_dir}/{common.EVIDENCE_MANIFEST}')
        if (not isinstance(manifest, dict)
                or manifest.get('protocol') != common.EVIDENCE_PROTOCOL
                or manifest.get('task_id') != row.get('task_id')
                or not isinstance(manifest.get('files'), list)):
            self._reject(f'evidence manifest malformed: {rel_dir}')
        if manifest.get('complete') is not True:
            self._reject(f'evidence marked incomplete at capture time: {rel_dir}')
        if not isinstance(declared, list) or declared != manifest['files']:
            self._reject(f'evidence index disagrees with manifest: {rel_dir}')
        for entry in manifest['files']:
            if not isinstance(entry, dict) or not isinstance(entry.get('path'), str):
                self._reject(f'evidence manifest malformed: {rel_dir}')
            rel = entry['path']
            target = (ev_dir / rel).resolve()
            if ev_dir not in target.parents:
                self._reject(f'evidence entry escapes its directory: {rel!r}')
            if not target.is_file() or target.is_symlink():
                self._reject(f'archived evidence file missing: {rel_dir}/{rel}')
            sha, size = common.sha256_file(target), target.stat().st_size
            if sha != entry.get('sha256') or size != entry.get('bytes'):
                self._reject(f'archived evidence bytes do not match the '
                             f'recorded digest: {rel_dir}/{rel}')

    def _validate_result_fields(self, row, file):
        def number(value):
            return type(value) in (int, float) and math.isfinite(value)

        subs = row.get('subscores')
        timings = row.get('timings')
        if (not isinstance(subs, dict)
                or not set(common.DEFAULT_SUBSCORES) <= subs.keys()
                or any(v is not None and (not number(v) or not 0 <= v <= 1)
                       for v in subs.values())
                or not isinstance(timings, dict)
                or not {'agent_s', 'setup_s', 'grade_s'} <= timings.keys()
                or any(not number(v) or v < 0 for v in timings.values())
                or not isinstance(row.get('subscore_applicability'), dict)
                or 'failure_mode' not in row
                or (row['failure_mode'] is not None and not isinstance(row['failure_mode'], str))):
            self._reject(f'incomplete or invalid cached result: {file.name}')
        for key in ('gate_failures', 'logs'):
            value = row.get(key)
            if not isinstance(value, list) or any(not isinstance(v, str) for v in value):
                self._reject(f'invalid cached {key}: {file.name}')

    def write_result(self, task, result):
        result['artifacts']['resume_identity'] = self.token
        common.write_json_atomic(self.out / f'result_{task.id}.json', result)

    def finish(self, **extra):
        return common.write_run_manifest(self.out, **self.manifest_args,
                                        extra={**self.extra, **extra})

    def __exit__(self, *exc):
        if self.lock:
            self.lock.close()
            self.lock = None
