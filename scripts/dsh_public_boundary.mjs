// Trusted DSH host plugin. This file is never supplied to the subject Agent.
import { createRequire } from 'node:module';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { appendFileSync, writeFileSync, readFileSync, mkdirSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { createHash } from 'node:crypto';
import { spawn } from 'node:child_process';

const requireDSH = createRequire(join(process.env.COMACBENCH_DSH_ROOT, 'package.json'));
const { defineTool } = await import(pathToFileURL(requireDSH.resolve('@deepseek-ai/dsh-tools')));
export const name = 'comacbench-public-boundary';
export const inject = ['tools', 'systemPrompt', 'agentDefaultModel', 'llm'];
export const provide = ['comacbenchBoundary'];
const sha = value => createHash('sha256').update(value).digest('hex');
export const CONTRACT_SHA256 = 'd6b1d694ed9c92093b9b022b1dcc208b5bf046b2608cdbaee0319052008b9271';
// Git's CRLF transport conversion is not a change to JSON string content.
const contractBytes = Buffer.from(readFileSync(new URL('../comacbench/public_input_v2.json', import.meta.url), 'utf8').replace(/\r\n/g, '\n'));
if (sha(contractBytes) !== CONTRACT_SHA256) throw new Error('public_contract_version_mismatch');
export const CONTRACT = JSON.parse(contractBytes);
export const PUBLIC_SYSTEM = CONTRACT.sections[0].text;
export const canonical = value => JSON.stringify(value, function (_key, v) {
  return v && !Array.isArray(v) && typeof v === 'object'
    ? Object.fromEntries(Object.keys(v).sort().map(k => [k, v[k]])) : v;
});
const same = (a, b) => canonical(a) === canonical(b);
const freeze = value => {
  if (value && typeof value === 'object') { Object.values(value).forEach(freeze); Object.freeze(value); }
  return value;
};
freeze(CONTRACT);

// These instance wrappers cover the post-waterfall assembly and dispatch paths of
// the pinned installed DSH. They are local host controls, not hostile-host isolation.
export function installPromptBoundary(ctx, record, model, hostResults, noModel = false) {
  for (const [pkg, digest] of Object.entries(CONTRACT.runtime)) {
    if (sha(readFileSync(requireDSH.resolve(pkg))) !== digest) throw new Error('unsupported_dsh_runtime:' + pkg);
  }
  const fail = (code, actual) => {
    record({ type: 'blocked', code, actual });
    throw new Error(code);
  };
  const validate = a => same(a.sections, CONTRACT.sections) && same(a.contexts, []) && same(a.tools, CONTRACT.tools);
  // DSH restores the complete section AFTER this cooperative waterfall. Check
  // transforms too, so a later mutation is rejected, even if DSH would discard it.
  ctx.on('system-prompt/assemble', async (input, _context, next) => {
    const before = canonical(input.sections);
    const publicSection = input.sections.filter(s => s.name === CONTRACT.sections[0].name);
    if (!same(publicSection, CONTRACT.sections)) fail('assembly_section_source_changed', input);
    const value = await next();
    if (canonical(value.sections) !== before || !same(value.contexts, []) || !same(value.tools, CONTRACT.tools))
      fail('assembly_boundary_failed', value);
    return value;
  }, { prepend: true });
  let assemblies = 0, dispatches = 0, latest;
  const assemble = ctx.systemPrompt.assemble;
  ctx.systemPrompt.assemble = async function (...args) {
    const value = await assemble.apply(this, args);
    if (!validate(value) || !same(ctx.agentDefaultModel.currentSelection(), model) || ++assemblies > 64)
      fail('final_assembly_boundary_failed', value);
    latest = structuredClone({ sections: value.sections, contexts: value.contexts, tools: value.tools });
    record({ type: 'assembly', contract_version: CONTRACT.version, contract_sha256: CONTRACT_SHA256,
      ...latest, schemas: value.tools.map(s => s.name), model, number: assemblies,
      public_system_sha256: sha(value.sections.map(s => s.text).join('\n\n')),
      input_sha256: sha(canonical(latest)) });
    return freeze(value);
  };
  // Both preparedCall.stream and ordinary stream pass through adapterStream,
  // after every llm/stream middleware. No adapter/provider is replaced.
  // A preflight traverses the real Agent loop and LLM waterfall without even
  // asking the provider for model capabilities. This stub is preflight-only.
  if (noModel) ctx.llm.prepareCall = async config => ({ config,
    stream: options => ctx.llm.stream(options) });
  const dispatch = ctx.llm.adapterStream;
  if (typeof dispatch !== 'function') throw new Error('unsupported_dsh_dispatch');
  ctx.llm.adapterStream = function (options, prepared) {
    const actual = structuredClone({ messages: options.messages, tools: options.tools });
    if (!latest || ++dispatches > 64 || !same(actual.tools, CONTRACT.tools)
        || options.provider !== model.provider || options.model !== model.model) fail('dispatch_boundary_failed', actual);
    const systems = actual.messages.filter(m => m.role === 'system');
    const users = actual.messages.filter(m => m.role === 'user');
    if (systems.length !== 1 || !same(systems[0].content, [{type:'text', text: PUBLIC_SYSTEM}])
        || users.length !== 1 || !same(users[0].content, [{type:'text', text: CONTRACT.user_entry}]))
      fail('public_entry_changed', actual);
    for (const m of actual.messages) {
      if (!['system', 'user', 'assistant', 'tool'].includes(m.role)) fail('unexpected_message_source', actual);
      if (m.role === 'tool') {
        const host = hostResults.get(m.toolCallId);
        if (!host || !same(m.content, host.content) || m.isError !== host.is_error) fail('tool_message_changed', actual);
      }
      if (m.role === 'assistant' && (m.source?.kind !== 'model' || m.source.provider !== model.provider || m.source.model !== model.model))
        fail('assistant_source_changed', actual);
    }
    record({ type: 'model_input', contract_version: CONTRACT.version, contract_sha256: CONTRACT_SHA256,
      assembly_number: assemblies, number: dispatches, model, ...actual, input_sha256: sha(canonical(actual)) });
    if (noModel) throw new Error('PREFLIGHT_COMPLETE_NO_MODEL');
    // Seal the checked envelope, including histories, before DSH's adapter projection.
    freeze(options.messages); freeze(options.tools);
    return dispatch.call(this, Object.freeze({ ...options }), prepared);
  };
}

export function installBoundary(ctx, invoke, record, maxToolCalls = 96) {
  if (ctx.tools.get('workbench')) throw new Error('workbench_tool_name_collision');
  let calls = 0;
  ctx.tools.register(defineTool({
    name: 'workbench', description: 'Operate one host-bound public calibration session. observe returns the self-contained contract and current inputs. No filesystem paths, shell, code, arbitrary deck, or other sessions are accepted.',
    parameters: { request: { type: 'object', required: true, additionalProperties: false,
      description: 'An object, not a JSON-encoded string. Start with {"op":"observe"}.',
      properties: {
        op: { type: 'string', required: true, enum: ['observe', 'solve', 'check', 'put', 'advance', 'submit', 'read_native'] },
        target: { type: 'string' }, name: { type: 'string' },
        claim: { type: 'string', enum: ['requirements_met', 'needs_review'] },
        basis: { type: 'object', additionalProperties: true, properties: {} },
        payload: { type: 'object', additionalProperties: false, properties: {
          requirement_revision: { type: 'string', required: true },
          claim: { type: 'string', required: true, enum: ['requirements_met', 'needs_review'] },
          cases: { type: 'array', required: true, items: { type: 'object', additionalProperties: false, properties: {
            point: { type: 'string', required: true }, uy_mm: { type: 'number', required: true },
            rfy_n: { type: 'number', required: true }, meets_requirement: { type: 'boolean', required: true },
          } } },
        } },
      } } },
    output: { schema: { type: 'json' }, render: (_args, value) => [{ type: 'text', text: JSON.stringify(value) }] },
    async execute(args, exec) {
      return await invoke(args.request, exec.signal, exec.callId);
    },
  }));
  ctx.tools.guard(exec => {
    if (exec.name !== 'workbench') return 'COMACBench public capability boundary: tool denied';
    if (++calls > maxToolCalls) return 'COMACBench fixed tool-call budget exhausted';
    return undefined;
  });
  ctx.on('tools/result', (exec, result) => {
    record({ type: 'tool_result', call_id: exec.callId, name: exec.name,
      arguments: exec.arguments, is_error: result.isError,
      content: result.content, error: result.error ?? null });
  });
}

export function restrictAgent(agent) {
  agent.ctx.tools.presentAs('native');
  agent.ctx.tools.restrict({ allow: ['workbench'] });
}

export async function probeBoundary(ctx, agent) {
  const probes = [];
  for (const [name, args] of [
    ['read', { path: 'session/session.json' }],
    ['read', { path: '../tests/test_workbench_native.py' }],
    ['read', { path: '../scripts/reference.py' }],
    ['read', { path: '../docs/native-calibration-handoff.md' }],
    ['read', { path: '../neighbor/report/report.json' }],
    ['bash', { command: 'cat session/session.json' }],
    ['run_code', { code: 'require("node:fs").readFileSync("session/session.json")' }],
    ['glob', { pattern: '**/*' }], ['web_fetch', { url: 'file:///session/session.json' }],
  ]) {
    const result = await ctx.tools.execute({ callId: `boundary-probe-${probes.length + 1}`,
      name, arguments: args, agent, signal: new AbortController().signal });
    probes.push({ name, arguments: args, is_error: result.isError, error: result.error ?? null });
    if (!result.isError) throw new Error('forbidden_tool_executed');
  }
  const schemas = ctx.tools.schemas(agent).map(s => s.name);
  if (JSON.stringify(schemas) !== '["workbench"]') throw new Error('unexpected_tools_visible');
  return { probes, schemas, all_denied: true };
}

export async function apply(ctx, config) {
  const auditDir = resolve(config.auditDir);
  mkdirSync(auditDir, { recursive: false });
  let seq = 0;
  const hostResults = new Map();
  const record = row => {
    if (row.type === 'tool_result') {
      if (hostResults.has(row.call_id)) throw new Error('duplicate_host_call_id');
      hostResults.set(row.call_id, structuredClone(row));
    }
    appendFileSync(join(auditDir, 'boundary.jsonl'), JSON.stringify({ seq: ++seq, ...row }) + '\n');
  };
  const model = ctx.agentDefaultModel.currentSelection();
  if (model.provider !== 'zai-coding-cn' || model.model !== 'glm-4.7') {
    record({ type: 'blocked', code: 'existing_model_changed', model });
    throw new Error('existing_model_changed; no model call authorized');
  }
  const invoke = (request, signal, callId) => new Promise((done, reject) => {
    const child = spawn(config.python, ['-m', 'comacbench.workbench_public', '--session', config.session],
      { cwd: config.source, shell: false, stdio: ['pipe', 'pipe', 'pipe'], signal });
    let stdout = '', stderr = '';
    child.stdout.on('data', data => { stdout += data; });
    child.stderr.on('data', data => { stderr += data; });
    let processError = null;
    child.on('error', error => { processError = error.code ?? 'spawn_error'; });
    child.on('close', code => {
      // Host diagnostics remain in the protected audit; no path-bearing traceback
      // is forwarded to the model. Failed and interrupted calls remain recorded.
      record({ type: 'broker', call_id: callId, request, exit_code: code, stdout, stderr, process_error: processError });
      if (code !== 0 || processError) return done({ result: { ok: false, code: 'broker_process_failed' } });
      try { done(JSON.parse(stdout)); } catch { done({ result: { ok: false, code: 'broker_invalid_json' } }); }
    });
    child.stdin.end(JSON.stringify(request));
  });
  installBoundary(ctx, invoke, record, 96);
  ctx.systemPrompt.suppressRuntimeContext();
  ctx.systemPrompt.section({ name: 'comacbench-public-system', order: 0, text: PUBLIC_SYSTEM,
    complete: true, interpolate: false });
  installPromptBoundary(ctx, record, model, hostResults, config.noModel === true);
  const manifest = JSON.parse(readFileSync(join(config.session, 'session.json')));
  if (manifest.scenario.max_actions !== 32 || manifest.scenario.max_solver_calls !== 6
      || manifest.scenario.solve_timeout_s !== 120) throw new Error('budget_changed');
  const proof = { protocol: 'comacbench.public-boundary.v2', model,
    contract_version: CONTRACT.version, contract_sha256: CONTRACT_SHA256, runtime: CONTRACT.runtime,
    public_user_entry: CONTRACT.user_entry,
    session_manifest_sha256: manifest.manifest_sha256,
    engine_sha256: manifest.engine_sha256,
    plugin_sha256: sha(readFileSync(fileURLToPath(import.meta.url))),
    gateway_sha256: sha(readFileSync(join(config.source, 'comacbench/workbench_public.py'))),
    complete_public_system: PUBLIC_SYSTEM, runtime_context_suppressed: true,
    mode: 'native', os_process_isolation: false,
    boundary_scope: 'trusted DSH host capability restriction; not hostile-host or OS isolation',
    budget: { actions: 32, solver_calls: 6, solve_timeout_s: 120, tool_calls: 96, model_assemblies: 64 },
    task_scope: 'same_public_task_development_repeat', prior_public_task_exposure: true };
  let agentSeen = false;
  ctx.on('agent/created', async ({ agent, source }) => {
    if (agentSeen || source !== 'startup') throw new Error('one_fresh_agent_only');
    agentSeen = true;
    restrictAgent(agent);
    const probe = await probeBoundary(ctx, agent);
    const observationProbe = await ctx.tools.execute({ callId: 'boundary-probe-observe', name: 'workbench',
      arguments: { request: { op: 'observe' } }, agent, signal: new AbortController().signal });
    if (observationProbe.isError || observationProbe.value?.result?.code !== 'observed'
        || observationProbe.value?.observation?.actions_used !== 0) throw new Error('public_observe_probe_failed');
    const completed = { ...proof, probe, agent_id: agent.id, creation_source: source,
      fresh_headless_session: true, public_observe_success: true };
    writeFileSync(join(auditDir, 'control.json'), JSON.stringify(completed, null, 2) + '\n', { flag: 'wx' });
    record({ type: 'ready', agent_id: agent.id, session_manifest_sha256: manifest.manifest_sha256 });
    const assembled = await ctx.systemPrompt.assemble({ scope: agent, agent });
    if (assembled.sections.length !== 1 || assembled.sections[0].text !== PUBLIC_SYSTEM
        || assembled.contexts.some(c => c.text)) throw new Error('public_prompt_probe_failed');
    record({ type: 'prompt_probe', sections: assembled.sections, contexts: assembled.contexts,
      schemas: assembled.tools.map(s => s.name), tools: assembled.tools });
    if (config.probeOnly) throw new Error('PREFLIGHT_COMPLETE_NO_MODEL');
  });
  // The headless runner must explicitly inject this service. It cannot start
  // before the execution guard and mandatory agent-created restriction hook.
  ctx.provide('comacbenchBoundary', Object.freeze(proof));
}
