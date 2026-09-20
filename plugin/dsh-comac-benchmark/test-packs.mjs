import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, writeFileSync, cpSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { apply } from "./index.js";

const repo = fileURLToPath(new URL("../../", import.meta.url));
const tools = [], routes = [];
const ctx = { tools: { register: t => tools.push(t) }, effect: f => f(),
  webServer: { register: r => routes.push(r) } };
apply(ctx);
const byName = Object.fromEntries(tools.map(t => [t.name, t]));
assert.equal(tools.length, 10);
const catalog = await byName.comac_pack_catalog.execute({});
assert.equal(catalog.ok, true);
const core = catalog.packs.find(p => p.pack.id === "aviation-core-v1");
assert.equal(core?.task_count, 3);
const cfd = catalog.packs.find(p => p.pack.id === "aviation-cfd-step-v1");
assert.equal(cfd?.runnable, true);
assert.equal(cfd.task_count, 1);
assert.deepEqual(cfd.validation_evidence.map(e => e.reynolds), [100, 200, 300]);
assert.equal(cfd.validation_evidence.reduce((n,e) => n+e.matrix_cases, 0), 48);
assert.equal(cfd.publishable, false);
assert.ok(cfd.validation_evidence.every(e => e.public_scoring_tolerance === .1 && e.calibrated_tolerance === null));

assert.equal(cfd.tasks[0].exec_kind, "cfd_step");
const structural = catalog.packs.find(p => p.pack.id === "aviation-structures-v2");
assert.equal(structural?.runnable, true);
assert.equal(structural.task_count, 1);
assert.equal(structural.issues.some(i => i.code === "partial_engineering_gate"), false);
const folder = mkdtempSync(path.join(tmpdir(), "comac-pack-test-"));
cpSync(path.join(repo, "packs/aviation-core-v1"), path.join(folder, "pack"), { recursive: true });
writeFileSync(path.join(folder, "pack/pack.yaml"), "[]\n");
const bad = await byName.comac_pack_validate.execute({ pack: path.join(folder, "pack") });
assert.equal(bad.runnable, false);
const launch = await byName.comac_agent_run.execute({ mode: "run", pack: path.join(folder, "pack"), agent: "not-needed.json", out: path.join(folder, "run") });
assert.equal(launch.runnable, false);
assert.equal(launch.pid, undefined);
const cfdCopy = path.join(folder, "cfd");
cpSync(path.join(repo, "packs/aviation-cfd-step-v1"), cfdCopy, { recursive: true });
const cfdMeta = path.join(cfdCopy, "pack.yaml");
writeFileSync(cfdMeta, readFileSync(cfdMeta, "utf8").replace("bfs-re100-validated-v1", "re300-v1-failed"));
const rejected = await byName.comac_agent_run.execute({ mode: "run", pack: cfdCopy, agent: "not-needed.json", out: path.join(folder,"blocked-cfd") });
assert.equal(rejected.runnable, false);
assert.equal(rejected.pid, undefined);
assert.ok(rejected.issues.some(i => i.code === "unknown_research_evidence"));
const route=routes[0];
function request(method, remoteAddress) {
  let status, body;
  route.handler({ url: '/comac/packs', method, socket:{remoteAddress} }, {
    writeHead(code) { status=code; }, end(value) { body=JSON.parse(value.toString()); }
  });
  return {status,body};
}
assert.equal(request('POST','127.0.0.1').status,405);
assert.equal(request('GET','192.168.1.2').status,403);
assert.equal(request('GET','127.0.0.1').body.packs.find(p => p.pack.id === "aviation-core-v1").task_count,3);
console.log(JSON.stringify({ tools: tools.length, catalog_tasks: catalog.packs.reduce((n,p)=>n+p.task_count,0),
  cfd_pack_runnable: cfd.runnable, research_matrices: 3, research_cases: 48, invalid_research_agent_launches: 0,
  invalid_pack_blocked: true, invalid_pack_agent_launches: 0, registered_routes: routes.length }));
