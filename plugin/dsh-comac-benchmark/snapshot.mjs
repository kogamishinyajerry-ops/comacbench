#!/usr/bin/env node
/**
 * comac-snapshot — 工作台里程碑快照生成器（规格书 §3.4，T4 决议）。
 *
 *   node plugin/dsh-comac-benchmark/snapshot.mjs --tag M4
 *   node plugin/dsh-comac-benchmark/snapshot.mjs --tag M4 --full
 *
 * - 默认：聚合 ViewJSON 落 results/_snapshots/<tag>.json（<2MB，进 git——
 *   明细 SSOT 永在 results/，git 历史即"那一刻"的冻结）
 * - --full：另产 results/_snapshots/<tag>-full/（快照 + 全部 result.json 拷贝
 *   + 零依赖 HTML 查看器），断网可开，供评审外发——不进 git（.gitignore 有条目）
 *
 * 与 /comac/* 路由共享同一数据层（index.js 导出），聚合逻辑零复写。
 */
import { mkdirSync, readdirSync, copyFileSync, writeFileSync, statSync, existsSync } from "node:fs";
import path from "node:path";
import { buildViewJSON } from "./index.js";

const HOME = process.env.COMAC_BENCH_HOME
  ?? "/Users/Zhuanz/projects/jerry-personal/JerryDSH-COMACBench";
const SNAP_DIR = path.join(HOME, "results", "_snapshots");

const args = process.argv.slice(2);
const tag = (() => {
  const i = args.indexOf("--tag");
  return i >= 0 ? args[i + 1] : null;
})();
const full = args.includes("--full");
if (!tag) {
  console.error("用法: snapshot.mjs --tag <里程碑或日期> [--full]");
  process.exit(2);
}
if (!/^[\w.-]{1,64}$/.test(tag)) {
  console.error(`非法 tag: ${tag}（只允许 [A-Za-z0-9_.-]，≤64 字符）`);
  process.exit(2);
}

const t0 = Date.now();
const view = buildViewJSON("snapshot", tag);
mkdirSync(SNAP_DIR, { recursive: true });
const snapPath = path.join(SNAP_DIR, `${tag}.json`);
writeFileSync(snapPath, JSON.stringify(view));
const snapKB = Math.round(statSync(snapPath).size / 1024);
console.log(`✓ 快照 ${tag}: ${snapKB}KB · runs=${view.runs.length} tasks=${view.tasks.length} · ${Date.now() - t0}ms`);
console.log(`  ${snapPath}`);

if (full) {
  const t1 = Date.now();
  const outDir = path.join(SNAP_DIR, `${tag}-full`);
  mkdirSync(outDir, { recursive: true });
  copyFileSync(snapPath, path.join(outDir, "snapshot.json"));
  // 全部 result.json 拷贝（保持 results/<rid>/<date>/<provider>/ 结构）
  let nFiles = 0;
  const resultsRoot = path.join(HOME, "results");
  for (const run of view.runs) {
    const src = path.join(resultsRoot, run.registry_id, run.date, run.provider);
    const dst = path.join(outDir, "results", run.registry_id, run.date, run.provider);
    mkdirSync(dst, { recursive: true });
    for (const f of readdirSync(src)) {
      if (/^result_.*\.json$/.test(f) || f === "run_manifest.json" || f === "summary.md") {
        copyFileSync(path.join(src, f), path.join(dst, f));
        nFiles += 1;
      }
    }
  }
  writeFileSync(path.join(outDir, "index.html"), fullViewerHtml(tag));
  const fullMB = (Math.round(dirSize(outDir) / 1048576 * 10) / 10).toFixed(1);
  console.log(`✓ --full 外发包: ${nFiles} 文件 · ${fullMB}MB · ${Date.now() - t1}ms`);
  console.log(`  ${outDir}/index.html（file:// 断网可开）`);
}

function dirSize(p) {
  let s = 0;
  for (const f of readdirSync(p)) {
    const fp = path.join(p, f);
    s += statSync(fp).isDirectory() ? dirSize(fp) : statSync(fp).size;
  }
  return s;
}

/** 零依赖 HTML 查看器（file:// 打开，fetch 同目录 snapshot.json；方案 B 的最小 v1 形态） */
function fullViewerHtml(tag) {
  return `<!doctype html><html lang="zh"><head><meta charset="utf-8">
<title>COMACBench 快照 ${tag}</title><style>
body{font:13px/1.5 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;margin:24px;background:#111418;color:#ced4da}
h1{font-size:18px;color:#fff}h2{font-size:14px;color:#74c0fc;margin-top:24px}
table{border-collapse:collapse;width:100%;margin:8px 0}
th,td{border:1px solid #2b3038;padding:4px 8px;text-align:left;font-size:12px}
th{background:#1a1f26;color:#fff}tr:hover td{background:#1c232c}
.gate1{color:#69db7c}.gate0{color:#ff8787}a{color:#74c0fc}
#meta{color:#868e96;font-size:12px}
</style></head><body>
<h1>COMACBench 快照「${tag}」</h1><div id="meta">读取中…</div><div id="app"></div>
<script>
fetch('./snapshot.json').then(r=>r.json()).then(v=>{
  document.getElementById('meta').textContent =
    '生成于 '+v.header.generated_at_utc+' · '+v.runs.length+' runs · '+v.tasks.length+' tasks · git '+v.header.git_commit;
  const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  let h='<h2>Runs（date × provider × 基准）</h2><table><tr><th>基准</th><th>日期</th><th>provider</th><th>gate</th><th>均分</th><th>失败模式</th></tr>';
  for(const r of v.runs){
    const fm=Object.entries(r.failure_modes||{}).filter(([k])=>k!=='PASS').map(([k,n])=>k+'×'+n).join(', ')||'—';
    h+=\`<tr><td>\${esc(r.registry_id)}</td><td>\${esc(r.date)}</td><td>\${esc(r.provider)}</td><td>\${r.gate_passed}/\${r.n_tasks}</td><td>\${r.score_mean??'—'}</td><td>\${esc(fm)}</td></tr>\`;
  }
  h+='</table><h2>Registry</h2><table><tr><th>id</th><th>status</th><th>tier</th><th>adapter</th><th>license_status</th></tr>';
  for(const e of v.registry){h+=\`<tr><td>\${esc(e.id)}</td><td>\${esc(e.status)}</td><td>\${esc(e.tier)}</td><td>\${esc(e.adapter)}</td><td>\${esc(e.license_status)}</td></tr>\`;}
  h+='</table><h2>Tasks（逐题）</h2><table><tr><th>run</th><th>基准/日期/provider</th><th>task</th><th>gate</th><th>failure_mode</th><th>score</th></tr>';
  for(const t of v.tasks){
    const r=v.runs[t.run];
    h+=\`<tr><td>\${t.run}</td><td>\${esc(r.registry_id+'/'+r.date+'/'+r.provider)}</td><td>\${esc(t.task_id)}</td><td class="gate\${t.gate}">\${t.gate}</td><td>\${esc(t.failure_mode)}</td><td>\${t.score}</td></tr>\`;
  }
  document.getElementById('app').innerHTML=h+'</table>';
}).catch(e=>{document.getElementById('meta').textContent='读取失败: '+e+'（请通过本地 HTTP 服务打开，如 python3 -m http.server）';});
</script></body></html>`;
}
