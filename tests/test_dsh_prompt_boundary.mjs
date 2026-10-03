// Existing installed DSH services, real waterfalls/complete-section/dispatch.
// Terminal adapter is a no-network sentinel, never a subject Agent/model score.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';
import { installBoundary, installPromptBoundary, restrictAgent, CONTRACT } from '../scripts/dsh_public_boundary.mjs';
const req = createRequire(join(process.env.COMACBENCH_DSH_ROOT, 'package.json'));
const imp = async name => import(pathToFileURL(req.resolve(name)));
const { Context } = await imp('@deepseek-ai/cordis');
const { default: SystemPrompt, renderPrompt } = await imp('@deepseek-ai/dsh-system-prompt');
const { ToolRuntime } = await imp('@deepseek-ai/dsh-tools');
const { LlmRuntime } = await imp('@deepseek-ai/dsh-llm');
const { createScope } = await imp('@deepseek-ai/dsh-scope');
const model = {provider:'zai-coding-cn', model:'glm-4.7'};
const summary = [];
for (const kind of ['normal', 'replace_section', 'extra_section', 'context', 'schema_description', 'schema_parameters', 'dispatch_system', 'dispatch_user', 'dispatch_context', 'dispatch_schema', 'dispatch_tool_response']) {
  const ctx = new Context(); new SystemPrompt(ctx, {}); new ToolRuntime(ctx,{mode:'native'}); new LlmRuntime(ctx);
  ctx.provide('agentDefaultModel', {currentSelection:()=>structuredClone(model)});
  const rows = [], host = new Map(); let executed = 0, adapterCalls = 0;
  const record = row => { rows.push(row); if(row.type==='tool_result') host.set(row.call_id,row); };
  installBoundary(ctx, async request => {executed++; return {result:{ok:true,code:request.op==='observe'?'observed':'synthetic_task_action'}};}, record);
  ctx.systemPrompt.suppressRuntimeContext();
  ctx.systemPrompt.section({...CONTRACT.sections[0], order:0, complete:true});
  installPromptBoundary(ctx, record, model, host);
  const agent = {}; agent.ctx=createScope(ctx,agent).ctx; restrictAgent(agent);
  // Startup success, then mutate a SUBSEQUENT assembly via a later hook.
  await ctx.systemPrompt.assemble({scope:agent,agent});
  ctx.on('system-prompt/assemble', async (input,_context,next)=>{
    const a=structuredClone(await next());
    if(kind==='replace_section') a.sections.find(s=>s.name==='comacbench-public-system').text='private reference';
    if(kind==='extra_section') a.sections.push({name:'extra',text:'private reference'});
    if(kind==='context') a.contexts.push({name:'extra',text:'private reference'});
    if(kind==='schema_description') a.tools[0].description='private reference';
    if(kind==='schema_parameters') a.tools[0].parameters.properties.request.description='private reference';
    return a;
  });
  ctx.on('llm/stream',(options,next)=>{
    if(kind==='dispatch_system') options.messages[0].content[0].text='private reference';
    if(kind==='dispatch_user') options.messages[1].content[0].text='different task';
    if(kind==='dispatch_context') options.messages.push({role:'developer',content:[{type:'text',text:'private reference'}]});
    if(kind==='dispatch_schema') options.tools[0].description='changed';
    if(kind==='dispatch_tool_response') options.messages.push({role:'tool',toolCallId:'unlogged',isError:false,content:[{type:'text',text:'private reference'}]});
    return next();
  });
  let error;
  try {
    const a=await ctx.systemPrompt.assemble({scope:agent,agent});
    const options={...model, tools:structuredClone(a.tools), messages:[
      {role:'system',content:[{type:'text',text:renderPrompt(a)}]},
      {role:'user',content:[{type:'text',text:CONTRACT.user_entry}]}]};
    // The real LLM runtime's common prepared/unprepared dispatch path.
    const prepared={config:model,modelInfo:{},registration:{adapter:{}},dispatch:async function* (actual){
      adapterCalls++; assert.equal(actual.messages[0].content[0].text,CONTRACT.sections[0].text);
    }};
    for await(const _chunk of ctx.llm.streamWithRegistration(options,prepared)) {}
    assert.equal(adapterCalls,1);
  } catch(e) {error=e.message;}
  if(kind==='normal') {
    assert.equal(error,undefined);
    for(const [i,op] of ['observe','check'].entries()) {
      const result=await ctx.tools.execute({callId:'normal-'+i,name:'workbench',arguments:{request:{op,...(op==='check'?{target:'review'}:{})}},agent,signal:new AbortController().signal});
      assert.equal(result.isError,false);
    }
    assert.equal(executed,2);
    assert.equal(rows.filter(r=>r.type==='assembly').length,2);
    assert.equal(rows.filter(r=>r.type==='model_input').length,1);
  } else {assert.ok(error,kind);assert.equal(adapterCalls,0,kind);}
  summary.push({kind,error:error??null,adapter_sentinel_calls:adapterCalls,tool_bodies:executed,records:rows});
}
console.log(JSON.stringify({status:'PASS',scope:'installed DSH services; synthetic terminal adapter and task body; no model/network/solver',runtime:CONTRACT.runtime,cases:summary},null,2));
