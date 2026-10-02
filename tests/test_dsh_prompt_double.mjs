// Adaptation of reviewer probe_prompt_hook.mjs for version 2; service doubles ONLY.
import assert from 'node:assert/strict';
import {installPromptBoundary, CONTRACT} from '../scripts/dsh_public_boundary.mjs';
const rows=[], hooks={}; const model={provider:'zai-coding-cn',model:'glm-4.7'};
const assembly=()=>structuredClone({sections:CONTRACT.sections,contexts:[],tools:CONTRACT.tools});
const ctx={on:(name,fn)=>{hooks[name]=fn;},agentDefaultModel:{currentSelection:()=>model},
 systemPrompt:{assemble:async()=>assembly()},llm:{adapterStream:()=>{throw Error('must not call adapter');}}};
installPromptBoundary(ctx,row=>rows.push(row),model,new Map());
const probes=[];
for(const kind of ['unchanged','changed_section','extra_section','unexpected_context','unexpected_tool']){
 const input=assembly(), output=assembly();
 if(kind==='changed_section')output.sections[0].text='SYNTHETIC REFERENCE: needs_review; 15 actions / 3 solves';
 if(kind==='extra_section')output.sections.push({text:'SYNTHETIC PRIVATE REFERENCE: future limit 0.45'});
 if(kind==='unexpected_context')output.contexts.push({text:'SYNTHETIC PRIVATE REFERENCE'});
 if(kind==='unexpected_tool')output.tools.push({name:'read'});
 let accepted=true,error;
 try{await hooks['system-prompt/assemble'](input,null,async()=>output);}catch(e){accepted=false;error=e.message;}
 probes.push({kind,accepted,error});assert.equal(accepted,kind==='unchanged',kind);
}
console.log(JSON.stringify({status:'PASS',scope:'DSH service doubles; not installed DSH runtime evidence',probes,records:rows},null,2));
