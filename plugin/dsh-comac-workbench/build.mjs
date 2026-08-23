// fail-loud 构建包装（T5 实验室教训：clean:false 下构建失败会留陈旧产物冒充新构建）。
// 退出码非零即中止；成功后断言产物首行是 factory 注册（防格式回归）。
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { readFileSync } from "node:fs";

const here = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const bin = join(here, "node_modules", "tsdown", "dist", "run.mjs");
const r = spawnSync(process.execPath, [bin, ...args], { cwd: here, stdio: "inherit" });
if (r.status !== 0) {
  console.error("\n✗ tsdown 构建失败（exit " + r.status + "）——产物未更新，禁止继续。");
  process.exit(r.status ?? 1);
}
if (!args.includes("--watch")) {
  const out = join(here, "lib", "client.js");
  const head = readFileSync(out, "utf8").slice(0, 80);
  if (!head.startsWith("window.__ModuleLoader__.load(")) {
    console.error("\n✗ 产物首行不是 factory 注册——格式回归，禁止继续。首行: " + head.split("\n")[0]);
    process.exit(1);
  }
  console.log("✓ bundle OK, factory 格式断言通过");
}
