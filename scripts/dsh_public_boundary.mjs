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
export const inject = ['tools', 'systemPrompt', 'agentDefaultModel'];
export const provide = ['comacbenchBoundary'];
const sha = value => createHash('sha256').update(value).digest('hex');
export const PUBLIC_SYSTEM = 'You are operating an already public fixed calibration work package. '
  + 'Use only the workbench tool. Begin with {"request":{"op":"observe"}} to obtain the complete public operation contract and current inputs. '
  + 'Determine conclusions from current observations and errors. Complete the work package within its fixed budgets. '
  + 'This is one public development repeat, not an unseen test or a generalization score. Report failures honestly.';

export function installBoundary(ctx, invoke, record, maxToolCalls = 96) {
  if (ctx.tools.get('workbench')) throw new Error('workbench_tool_name_collision');
  let calls = 0;
  ctx.tools.register(defineTool({
    name: 'workbench', description: 'Operate one host-bound public calibration session. observe returns the self-contained contract and current inputs. No filesystem paths, shell, code, arbitrary deck, or other sessions are accepted.',
    parameters: { request: { type: 'json', required: true, description: 'JSON object with selector op. Start with {"op":"observe"}.' } },
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
  const record = row => appendFileSync(join(auditDir, 'boundary.jsonl'), JSON.stringify({ seq: ++seq, ...row }) + '\n');
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
    child.on('error', reject);
    child.on('close', code => {
      // Host diagnostics remain in the protected audit; no path-bearing traceback
      // is forwarded to the model. Failed and interrupted calls remain recorded.
      record({ type: 'broker', call_id: callId, request, exit_code: code, stdout, stderr });
      if (code !== 0) return done({ result: { ok: false, code: 'broker_process_failed' } });
      try { done(JSON.parse(stdout)); } catch { reject(new Error('broker_invalid_json')); }
    });
    child.stdin.end(JSON.stringify(request));
  });
  installBoundary(ctx, invoke, record, 96);
  ctx.systemPrompt.suppressRuntimeContext();
  ctx.systemPrompt.section({ name: 'comacbench-public-system', order: 0, text: PUBLIC_SYSTEM,
    complete: true, interpolate: false });
  let assemblies = 0;
  ctx.on('system-prompt/assemble', async (_assembly, _context, next) => {
    const assembly = await next();
    const schemas = assembly.tools.map(s => s.name);
    const currentModel = ctx.agentDefaultModel.currentSelection();
    if (++assemblies > 64 || JSON.stringify(schemas) !== '["workbench"]'
        || assembly.contexts.some(c => c.text) || JSON.stringify(currentModel) !== JSON.stringify(model)) {
      record({ type: 'blocked', code: 'assembly_boundary_failed', schemas, assemblies });
      throw new Error('assembly_boundary_failed');
    }
    record({ type: 'assembly', schemas, contexts: assembly.contexts, model,
      public_system_sha256: sha(PUBLIC_SYSTEM), number: assemblies });
    return assembly;
  });
  const manifest = JSON.parse(readFileSync(join(config.session, 'session.json')));
  if (manifest.scenario.max_actions !== 32 || manifest.scenario.max_solver_calls !== 6
      || manifest.scenario.solve_timeout_s !== 120) throw new Error('budget_changed');
  const proof = { protocol: 'comacbench.public-boundary.v1', model,
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
    const completed = { ...proof, probe, agent_id: agent.id, creation_source: source,
      fresh_headless_session: true };
    writeFileSync(join(auditDir, 'control.json'), JSON.stringify(completed, null, 2) + '\n', { flag: 'wx' });
    record({ type: 'ready', agent_id: agent.id, session_manifest_sha256: manifest.manifest_sha256 });
    const assembled = await ctx.systemPrompt.assemble({ scope: agent, agent });
    if (assembled.sections.length !== 1 || assembled.sections[0].text !== PUBLIC_SYSTEM
        || assembled.contexts.some(c => c.text)) throw new Error('public_prompt_probe_failed');
    record({ type: 'prompt_probe', sections: assembled.sections, contexts: assembled.contexts,
      schemas: assembled.tools.map(s => s.name) });
    if (config.probeOnly) throw new Error('PREFLIGHT_COMPLETE_NO_MODEL');
  });
  // The headless runner must explicitly inject this service. It cannot start
  // before the execution guard and mandatory agent-created restriction hook.
  ctx.provide('comacbenchBoundary', Object.freeze(proof));
}
