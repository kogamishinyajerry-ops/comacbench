// Run: node --test plugin/dsh-comac-benchmark/test-pack-runtime.mjs
// No Python, solver, DSH installation, package install, network or credentials.
import assert from "node:assert/strict";
import { test } from "node:test";
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, existsSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { setTimeout as delay } from "node:timers/promises";
import { decodePackReply, resolvePackPython, launchPackProcess } from "./pack-runtime.js";
import { registerPackTools } from "./packs.js";

function temp(t) {
  const dir = mkdtempSync(path.join(tmpdir(), "comac-pack-runtime-"));
  t.after(() => rmSync(dir, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 }));
  return dir;
}
function reply(data, changes = {}) {
  return { status: 0, stdout: JSON.stringify(data), stderr: "", ...changes };
}
function tools(repo) {
  const registered = {};
  registerPackTools({ tools: { register: t => { registered[t.name] = t; } } }, repo);
  return registered;
}
function resultFile(repo, changes = {}) {
  const dir = path.join(repo, "out");
  mkdirSync(dir, { recursive: true });
  const data = { identity: { protocol: "comacbench.run.v1" }, status: "interrupted",
    results: [], calibration_passed: false, ...changes };
  writeFileSync(path.join(dir, "run.json"), JSON.stringify(data));
  return data;
}

test("explicit Python override wins without invoking filesystem discovery", () => {
  assert.equal(resolvePackPython("D:\\bench", { platform: "win32",
    env: { COMAC_BENCH_PYTHON: "C:\\approved env\\python.exe" },
    exists: () => { throw new Error("must not be called"); } }), "C:\\approved env\\python.exe");
});
test("Windows native venv uses Scripts/python.exe, including spaces", () => {
  const expected = "D:\\工程 bench\\.venv\\Scripts\\python.exe";
  assert.equal(resolvePackPython("D:\\工程 bench", { platform: "win32", env: {},
    exists: p => { assert.equal(p, expected); return true; } }), expected);
});
test("Windows fallback is python on PATH, not python3", () => {
  assert.equal(resolvePackPython("D:\\bench", { platform: "win32", env: {}, exists: () => false }), "python");
});
for (const platform of ["linux", "darwin"]) {
  test(`${platform} prefers the repository POSIX venv`, () => {
    assert.equal(resolvePackPython("/repo with spaces", { platform, env: {},
      exists: p => p === "/repo with spaces/.venv/bin/python" }), "/repo with spaces/.venv/bin/python");
  });
  test(`${platform} keeps the python3 PATH fallback`, () => {
    assert.equal(resolvePackPython("/repo", { platform, env: {}, exists: () => false }), "python3");
  });
}
test("empty override still discovers the platform venv", () => {
  assert.equal(resolvePackPython("/repo", { platform: "linux",
    env: { COMAC_BENCH_PYTHON: "" }, exists: () => true }), "/repo/.venv/bin/python");
});
test("nonzero exit cannot be hidden by payload ok=true", () => {
  const r = decodePackReply(reply({ ok: true, error: "blocked" }, { status: 2 }));
  assert.equal(r.ok, false); assert.equal(r.command_exit_code, 2);
  assert.equal(r.error, "blocked");
});
test("exit code provenance cannot be overwritten by a payload", () => {
  assert.equal(decodePackReply(reply({ command_exit_code: 0 }, { status: 3 })).command_exit_code, 3);
});
test("transport success is independent of a negative calibration verdict", () => {
  const r = decodePackReply(reply({ calibration_passed: false }));
  assert.equal(r.ok, true); assert.equal(r.calibration_passed, false);
});
test("structured stderr is parsed when stdout is whitespace", () => {
  const r = decodePackReply({ status: 2, stdout: " \n", stderr: '{"error":"missing dependency"}' });
  assert.equal(r.ok, false); assert.equal(r.error, "missing dependency");
});
for (const bad of [null, [], "ok", 1, true]) {
  test(`non-object JSON is rejected: ${JSON.stringify(bad)}`, () => {
    assert.throws(() => decodePackReply(reply(bad)), /JSON 对象/);
  });
}
test("malformed JSON is reported without echoing arbitrary stdout", () => {
  assert.throws(() => decodePackReply({ status: 1, stdout: "sensitive fixture text" }),
    e => e.message.includes("有效 JSON") && !e.message.includes("sensitive"));
});
for (const failure of [
  { status: null, error: { code: "ENOENT" } },
  { status: null, error: { code: "ETIMEDOUT" } },
  { status: null, signal: "SIGTERM" },
]) {
  test(`process error takes precedence over JSON: ${failure.error?.code || failure.signal}`, () => {
    assert.throws(() => decodePackReply(reply({ ok: true }, failure)), /进程失败/);
  });
}
test("valid result fields are preserved", () => {
  const payload = { completion: { complete: false, missing_tasks: ["suite/b"] }, packs: [] };
  const r = decodePackReply(reply(payload));
  assert.deepEqual(r.completion, payload.completion); assert.deepEqual(r.packs, []);
});
test("result tool forwards completion without recalculating the denominator", async t => {
  const repo = temp(t);
  const completion = { expected_tasks: 2, recorded_results: 1, scorable_results: 1,
    missing_tasks: ["suite/b"], complete: false };
  resultFile(repo, { completion, results: [{ id: "a", full_pass: true }] });
  const r = await tools(repo).comac_agent_result.execute({ out: "out" });
  assert.equal(r.ok, true); assert.equal(r.status, "interrupted");
  assert.equal(r.completion_available, true); assert.deepEqual(r.completion, completion);
});
test("legacy archive does not fabricate a complete verdict", async t => {
  const repo = temp(t); resultFile(repo, { status: "complete" });
  const r = await tools(repo).comac_agent_result.execute({ out: "out" });
  assert.equal(r.completion, null); assert.equal(r.completion_available, false);
});
test("malformed run archive returns a tool error", async t => {
  const repo = temp(t); resultFile(repo);
  writeFileSync(path.join(repo, "out", "run.json"), "{");
  assert.equal((await tools(repo).comac_agent_result.execute({ out: "out" })).ok, false);
});
test("unknown archive protocol remains rejected", async t => {
  const repo = temp(t); resultFile(repo, { identity: { protocol: "other" } });
  assert.equal((await tools(repo).comac_agent_result.execute({ out: "out" })).ok, false);
});
test("missing archive is not silently declared complete", async t => {
  const repo = temp(t);
  const r = await tools(repo).comac_agent_result.execute({ out: "out" });
  assert.equal(r.status, "not_started_or_preflight_failed");
});
test("failed OS spawn rejects instead of returning an undefined pid", async t => {
  const repo = temp(t), log = path.join(repo, "startup.log");
  await assert.rejects(launchPackProcess(repo, path.join(repo, "missing-python"), [], log), /未能启动/);
  assert.equal(existsSync(log), true);
  rmSync(log); // the parent's descriptor must have been closed
});
test("successful OS spawn returns a pid and preserves argv without a shell", async t => {
  const repo = temp(t), log = path.join(repo, "startup.log"), marker = path.join(repo, "marker.json");
  const arg = "literal $HOME ; & 中文 path";
  const script = "require('node:fs').writeFileSync(process.argv[1], JSON.stringify(process.argv[2]));";
  const pid = await launchPackProcess(repo, process.execPath, ["-e", script, marker, arg], log);
  assert.ok(Number.isInteger(pid) && pid > 0);
  const deadline = Date.now() + 5000;
  while (!existsSync(marker) && Date.now() < deadline) await delay(20);
  assert.equal(JSON.parse(readFileSync(marker, "utf8")), arg);
});
test("startup log is exclusive and cannot overwrite an earlier attempt", async t => {
  const repo = temp(t), log = path.join(repo, "startup.log");
  writeFileSync(log, "old evidence");
  await assert.rejects(launchPackProcess(repo, process.execPath, ["-e", ""], log), /EEXIST/);
  assert.equal(readFileSync(log, "utf8"), "old evidence");
});
