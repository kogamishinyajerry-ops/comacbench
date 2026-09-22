// Thin proxy to the Python contribution/agent CLI. No grading logic here.
import { spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import os from "node:os";

import { decodePackReply, launchPackProcess, resolvePackPython } from "./pack-runtime.js";

export function packCommand(repo, args) {
  const r = spawnSync(resolvePackPython(repo), ["-m", "comacbench.admission", ...args], {
    cwd: repo, encoding: "utf8", timeout: 30000, maxBuffer: 8 * 1024 * 1024,
    env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1" },
  });
  return decodePackReply(r);
}

export function registerPackTools(ctx, repo) {
  const output = { schema: { type: "object", additionalProperties: true },
    render: (_a, v) => [{ type: "text", text: JSON.stringify(v, null, 2) }] };
  const register = (name, description, properties, required, execute) => ctx.tools.register({
    name, description, parameters: { type: "object", properties, required, additionalProperties: false },
    output, async execute(args) {
      try { return await execute(args || {}); }
      catch (e) { return { ok: false, error: String(e.message || e) }; }
    },
  });
  register("comac_pack_catalog", "查看航空工业仿真、企业数据、本体评测包的范围、任务与材料质量。只读，不执行贡献代码。",
    {}, [], () => packCommand(repo, ["catalog"]));
  register("comac_pack_validate", "检查用户贡献评测包。返回缺失材料、摘要异常、答案泄漏、不合理断言/权重/容差和修复建议。不调用 agent，也不自动发布。",
    { pack: { type: "string", description: "本地评测包目录路径" } }, ["pack"],
    (a) => packCommand(repo, ["validate", path.resolve(repo, a.pack)]));
  register("comac_agent_run", "评测工程师明确指定的本地受信 agent，或显式校准贡献包。先预检，阻断项存在时不启动。脱离运行；结果和可离线打开的 report.html 写入新 out 目录。calibrate 执行参考代码与负例，属于自检。",
    { pack: { type: "string" }, agent: { type: "string", description: "agent JSON 配置路径；run 必填" },
      out: { type: "string", description: "运行输出目录" }, mode: { type: "string", enum: ["run", "calibrate"] },
      seed: { type: "integer" }, resume: { type: "boolean" } }, ["pack", "out", "mode"],
    async (a) => {
      if (!["run", "calibrate"].includes(a.mode)) throw new Error("mode 必须是 run 或 calibrate");
      const pack = path.resolve(repo, a.pack), out = path.resolve(repo, a.out);
      const validation = packCommand(repo, ["validate", pack]);
      if (!validation.ok) return validation;
      const args = ["-m", "comacbench.admission", a.mode, pack, "--out", out, "--seed", String(a.seed ?? 0)];
      if (a.mode === "run") {
        if (!a.agent || !existsSync(path.resolve(repo, a.agent))) throw new Error("提供可读取的 agent JSON 配置");
        args.push("--agent", path.resolve(repo, a.agent));
      }
      if (a.resume) args.push("--resume");
      const log = path.join(os.tmpdir(), `comac-agent-${Date.now()}-${process.pid}.log`);
      const pid = await launchPackProcess(repo, resolvePackPython(repo), args, log);
      return { ok: true, status: "launch_requested", pid, log, out,
        result: path.join(out, "run.json"), report: path.join(out, "report.html"),
        note: "进程已创建，不代表应用已就绪或评测完成；完成以 run.json status 为准，用 comac_agent_result 查看。" };
    });
  register("comac_agent_result", "读取工程师 agent 的完成状态、分项结果和贡献质量反馈；仅读取 run.json。",
    { out: { type: "string" } }, ["out"], (a) => {
      const out = path.resolve(repo, a.out), f = path.join(out, "run.json");
      if (!existsSync(f)) return { ok: true, status: "not_started_or_preflight_failed", note: "检查起跑返回的日志。" };
      const data = JSON.parse(readFileSync(f, "utf8"));
      if (data.identity?.protocol !== "comacbench.run.v1") throw new Error("不是本协议的运行档案");
      return { ok: true, status: data.status, error: data.error, agent: data.agent,
        pack: data.pack, results: data.results, controls: data.controls,
        completion: data.completion ?? null, completion_available: data.completion != null,
        calibration_passed: data.calibration_passed, validation: data.validation,
        report: path.join(out, "report.html"), rerun: data.rerun };
    });
}
