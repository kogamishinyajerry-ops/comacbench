// Host-side process plumbing only. Never compute engineering scores here.
import { spawn } from "node:child_process";
import { closeSync, existsSync, openSync } from "node:fs";
import path from "node:path";

/** Respect the configured interpreter, then the native venv, then PATH.
 * Selection is not proof that Python, dependencies, or solvers work.
 * Options make platform selection testable without claiming Windows execution.
 */
export function resolvePackPython(repo, {
  env = process.env, platform = process.platform, exists = existsSync,
} = {}) {
  if (env.COMAC_BENCH_PYTHON) return env.COMAC_BENCH_PYTHON;
  const paths = platform === "win32" ? path.win32 : path.posix;
  const candidate = platform === "win32"
    ? paths.join(repo, ".venv", "Scripts", "python.exe")
    : paths.join(repo, ".venv", "bin", "python");
  return exists(candidate) ? candidate : platform === "win32" ? "python" : "python3";
}

/** The process result, not an arbitrary JSON `ok`, decides command success. */
export function decodePackReply(result) {
  if (result.error || result.signal || !Number.isInteger(result.status)) {
    const reason = result.error?.code || result.signal || "unknown_process_error";
    throw new Error(`评测包进程失败（${reason}）；检查 COMAC_BENCH_PYTHON 与运行环境。`);
  }
  let data;
  try { data = JSON.parse(result.stdout?.trim() || result.stderr?.trim() || ""); }
  catch { throw new Error(`评测包命令未返回有效 JSON（退出码 ${result.status}）。`); }
  if (!data || typeof data !== "object" || Array.isArray(data)) {
    throw new Error("评测包命令必须返回 JSON 对象。");
  }
  return { ...data, ok: result.status === 0, command_exit_code: result.status };
}

/** A spawn acknowledgement is NOT application readiness or evaluation success.
 * Wait for the OS spawn/error event before returning; close the parent's log
 * descriptor on both synchronous and asynchronous failures. The child inherits
 * its own descriptor and may continue after the host returns.
 */
export async function launchPackProcess(repo, executable, args, log) {
  const fd = openSync(log, "wx");
  let child;
  try {
    child = spawn(executable, args, {
      cwd: repo, detached: true, stdio: ["ignore", fd, fd],
      env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1" },
    });
  } finally {
    closeSync(fd);
  }
  await new Promise((resolve, reject) => {
    child.once("error", (error) => reject(new Error(
      `评测进程未能启动（${error.code || "spawn_error"}）；启动日志：${log}`,
    )));
    child.once("spawn", resolve);
  });
  child.unref();
  return child.pid;
}
