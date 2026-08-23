// 冒烟测试：mock ctx 逐个调用插件工具的 execute（离线只读部分 + stub 起跑）
import { readFileSync } from "node:fs";

const src = readFileSync(new URL("./index.js", import.meta.url), "utf8");
const mod = await import(new URL("./index.js", import.meta.url));

const registered = [];
const ctx = {
  tools: { register: (t) => registered.push(t) },
  // 工作台路由挂载（effect 立即执行；webServer 缺省时不注册——真实环境由 dsh 提供）
  effect: (fn) => fn(),
};
mod.apply(ctx);
console.log(`registered ${registered.length} tools: ${registered.map((t) => t.name).join(", ")}`);

const byName = Object.fromEntries(registered.map((t) => [t.name, t]));
const call = async (name, args) => {
  const r = await byName[name].execute(args);
  console.log(`\n===== ${name} ${JSON.stringify(args ?? {})} =====`);
  console.log(JSON.stringify(r).slice(0, 600));
  return r;
};

// 1) registry
const reg = await call("comac_registry", {});
if (!reg.ok || reg.n < 10) throw new Error("comac_registry 异常");
// 2) bench 详情
const b = await call("comac_bench", { registry_id: "hilift_aeroml.lite" });
if (!b.ok || b.n_tasks !== 100) throw new Error("comac_bench 异常");
// 3) 环境预检失败路径（glm 但先不真起）
await call("comac_bench", { registry_id: "pycycle.engine_cycle" });
// 4) 起跑 stub（离线、快）——验证脱离 spawn + 日志
const run = await call("comac_run", { registry_id: "hilift_aeroml.lite", provider: "stub", date: "smoke-plugin" });
if (!run.ok) throw new Error("comac_run 失败: " + run.error);
console.log("\n[smoke] run launched pid=" + run.pid + " log=" + run.log);
// 5) 报告列表 + 命中
const docs = await call("comac_report", {});
if (!docs.ok) throw new Error("comac_report list 异常");
await call("comac_report", { name: "nine-dim", lines: 5 });
// 6) 状态查询（结果可能尚未写完，只验证不抛）
await call("comac_run_status", { registry_id: "hilift_aeroml.lite" });
console.log("\nALL SMOKE OK");
