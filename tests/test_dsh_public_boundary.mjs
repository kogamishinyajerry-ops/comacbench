// Run with the user's existing DSH installation. No provider/model calls.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';
import { installBoundary, restrictAgent, probeBoundary } from '../scripts/dsh_public_boundary.mjs';
const req = createRequire(join(process.env.COMACBENCH_DSH_ROOT, 'package.json'));
const imp = async name => import(pathToFileURL(req.resolve(name)));
const { Context } = await imp('@deepseek-ai/cordis');
const { default: SystemPrompt } = await imp('@deepseek-ai/dsh-system-prompt');
const { ToolRuntime, defineTool } = await imp('@deepseek-ai/dsh-tools');
const { createScope } = await imp('@deepseek-ai/dsh-scope');
const ctx = new Context();
new SystemPrompt(ctx, {});
new ToolRuntime(ctx, { mode: 'native' });
let forbiddenExecutions = 0;
const register = name => ctx.tools.register(defineTool({ name, description: 'test sentinel', parameters: {},
  output: { schema: { type: 'json' }, render: () => [] },
  execute: async () => { forbiddenExecutions++; return {}; } }));
for (const name of ['read', 'bash', 'glob', 'web_fetch']) register(name);
const records = [];
installBoundary(ctx, async request => ({ request }), row => records.push(row), 3);
const agent = {};
agent.ctx = createScope(ctx, agent).ctx;
restrictAgent(agent);
// A later permissive policy cannot override the monotonic guard/visibility.
ctx.on('tools/pre-execute', async () => ({ kind: 'allow' }));
const proof = await probeBoundary(ctx, agent);
assert.equal(forbiddenExecutions, 0);
const schema = ctx.tools.schemas(agent)[0];
assert.equal(schema.parameters.properties.request.type, 'object');
assert.equal(schema.parameters.properties.request.properties.op.type, 'string');
const stringInput = await ctx.tools.execute({ callId: 'string-input', name: 'workbench',
  arguments: { request: '{"op":"observe"}' }, agent, signal: new AbortController().signal });
assert.equal(stringInput.isError, true);
const call = n => ctx.tools.execute({ callId: `allowed-${n}`, name: 'workbench',
  arguments: { request: { op: 'observe' } }, agent, signal: new AbortController().signal });
assert.equal((await call(1)).isError, false);
assert.equal((await call(2)).isError, false);
assert.equal((await call(3)).isError, true);
assert.equal(records.length, proof.probes.length + 4);
// The explicit guard also rejects scoped tool overrides that bypass visibility.
// Test it independently of the allowlist with a separate registry.
const other = new Context();
new SystemPrompt(other, {});
new ToolRuntime(other, { mode: 'native' });
other.tools.register(defineTool({ name: 'read', description: 'sentinel', parameters: {},
  output: { schema: { type: 'json' }, render: () => [] }, execute: async () => { forbiddenExecutions++; return {}; } }));
other.tools.guard(exec => exec.name !== 'workbench' ? 'boundary denial' : undefined);
other.on('tools/pre-execute', async () => ({ kind: 'allow' }));
assert.equal((await other.tools.execute({ callId: 'guard', name: 'read', arguments: {},
  signal: new AbortController().signal })).isError, true);
assert.equal(forbiddenExecutions, 0);
console.log(JSON.stringify({ status: 'PASS', proof, forbidden_body_executions: forbiddenExecutions,
  tool_budget_denied: true, late_allow_cannot_override_guard: true, model_calls: 0 }, null, 2));
