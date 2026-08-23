// 工作台样式 — .comac-wb- 前缀命名空间（T3/T5 决议：零依赖、单文件 bundle 内联、不污染宿主）。
// 颜色/字体一律 var(--dsw-*) 直读宿主令牌，明暗主题随宿主切换。
export const css = `
.comac-wb-root{--wb-pad:12px;height:100%;display:flex;flex-direction:column;
  font-family:var(--dsw-font-family,inherit);background:var(--dsw-alias-bg-base,transparent);
  color:var(--dsw-alias-label-primary,#ced4da);overflow:hidden}
.comac-wb-root *{box-sizing:border-box}

/* 顶栏 */
.comac-wb-topbar{display:flex;align-items:center;gap:4px;padding:6px var(--wb-pad);
  border-bottom:1px solid var(--dsw-alias-border-l2,#2b3038);flex-shrink:0;flex-wrap:wrap}
.comac-wb-tab{padding:4px 12px;border-radius:6px;cursor:pointer;font-size:12px;
  color:var(--dsw-alias-label-secondary,#868e96);border:none;background:transparent}
.comac-wb-tab:hover{background:var(--dsw-alias-bg-layer-2,#1a1f26);color:var(--dsw-alias-label-primary,#ced4da)}
.comac-wb-tab.on{background:var(--dsw-alias-bg-layer-3,#232a33);color:#fff;font-weight:600}
.comac-wb-mode{margin-left:auto;font-size:11px;color:var(--dsw-alias-label-dimmed,#868e96);display:flex;gap:8px;align-items:center}
.comac-wb-dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:4px}
.comac-wb-dot.live{background:#69db7c}.comac-wb-dot.snap{background:#fab005}
.comac-wb-snapselect{background:var(--dsw-alias-bg-layer-2,#1a1f26);color:var(--dsw-alias-label-primary,#ced4da);
  border:1px solid var(--dsw-alias-border-l2,#2b3038);border-radius:4px;font-size:11px;padding:2px 6px}

/* 通用 */
.comac-wb-body{flex:1;overflow:auto;padding:var(--wb-pad)}
.comac-wb-h{font-size:13px;font-weight:600;color:#fff;margin:14px 0 6px}
.comac-wb-h:first-child{margin-top:0}
.comac-wb-sub{font-size:11px;color:var(--dsw-alias-label-dimmed,#868e96);margin-bottom:8px}
.comac-wb-crumb{font-size:11px;color:var(--dsw-alias-label-dimmed,#868e96);padding:4px 0 8px}
.comac-wb-crumb b{cursor:pointer;color:#74c0fc;font-weight:500}
.comac-wb-charts{display:flex;flex-wrap:wrap;gap:16px;align-items:flex-start}
.comac-wb-card{background:var(--dsw-alias-bg-layer-1,#15191f);border:1px solid var(--dsw-alias-border-l2,#2b3038);
  border-radius:8px;padding:10px 12px;overflow:auto}
.comac-wb-flex2{flex:2 1 420px}.comac-wb-flex1{flex:1 1 280px}
.comac-wb-warn{background:rgba(250,176,5,.08);border:1px solid rgba(250,176,5,.35);color:#fab005;
  font-size:11px;padding:6px 10px;border-radius:6px;margin-bottom:8px}

/* 表格 */
.comac-wb-table{border-collapse:collapse;width:100%;font-size:11px}
.comac-wb-table th,.comac-wb-table td{border-bottom:1px solid var(--dsw-alias-border-l1,#22272e);
  padding:4px 8px;text-align:left;white-space:nowrap}
.comac-wb-table th{color:var(--dsw-alias-label-secondary,#868e96);font-weight:500;position:sticky;top:0;
  background:var(--dsw-alias-bg-layer-1,#15191f);cursor:default;user-select:none}
.comac-wb-table th.sortable:hover{color:#74c0fc}
.comac-wb-table tbody tr:hover td{background:var(--dsw-alias-bg-layer-2,#1a1f26)}
.comac-wb-table tr.clickable{cursor:pointer}
.comac-wb-num{font-family:var(--dsw-font-family-code,Menlo,monospace);font-size:11px}
.comac-wb-g1{color:#69db7c}.comac-wb-g0{color:#ff8787}
.comac-wb-fm{display:inline-block;padding:0 6px;border-radius:3px;font-size:10px;margin-right:3px;
  background:var(--dsw-alias-bg-layer-3,#232a33)}

/* 分段计数条（总览家底） */
.comac-wb-seg{display:flex;border-radius:5px;overflow:hidden;font-size:11px;height:22px}
.comac-wb-seg>div{display:flex;align-items:center;justify-content:center;color:#fff;padding:0 8px;white-space:nowrap}

/* 徽章/空态/加载/错误 */
.comac-wb-badge{display:inline-block;font-size:10px;padding:1px 8px;border-radius:10px;font-weight:600}
.comac-wb-badge.integrated{background:rgba(105,219,124,.15);color:#69db7c}
.comac-wb-badge.active{background:rgba(77,171,247,.15);color:#4dabf7}
.comac-wb-badge.staged{background:rgba(116,192,252,.12);color:#74c0fc}
.comac-wb-badge.proposed{background:rgba(255,169,77,.12);color:#ffa94d}
.comac-wb-badge.deferred,.comac-wb-badge.excluded{background:rgba(134,142,150,.12);color:#868e96}
.comac-wb-badge.paused-env{background:rgba(255,135,135,.12);color:#ff8787}
.comac-wb-empty{padding:40px 0;text-align:center;color:var(--dsw-alias-label-dimmed,#868e96);font-size:12px}
.comac-wb-load{padding:40px 0;text-align:center;color:var(--dsw-alias-label-dimmed,#868e96);font-size:12px}
.comac-wb-err{padding:24px;text-align:center}
.comac-wb-err button{margin-top:10px;padding:4px 16px;border-radius:6px;cursor:pointer;
  background:var(--dsw-alias-bg-layer-3,#232a33);color:#74c0fc;border:1px solid var(--dsw-alias-border-l2,#2b3038)}

/* 键值小面板（registry 卡/信封区） */
.comac-wb-kv{display:grid;grid-template-columns:auto 1fr;gap:3px 12px;font-size:11px}
.comac-wb-kv dt{color:var(--dsw-alias-label-dimmed,#868e96);white-space:nowrap}
.comac-wb-kv dd{margin:0;color:var(--dsw-alias-label-primary,#ced4da);word-break:break-all}

/* 单题下钻 */
.comac-wb-drill{display:flex;gap:14px;flex-wrap:wrap}
.comac-wb-drill .comac-wb-card{max-height:60vh}
.comac-wb-gatebadge{font-size:16px;font-weight:700;padding:4px 14px;border-radius:8px;display:inline-block;margin-bottom:8px}
.comac-wb-gatebadge.pass{background:rgba(105,219,124,.15);color:#69db7c}
.comac-wb-gatebadge.fail{background:rgba(255,135,135,.15);color:#ff8787}
.comac-wb-pre{font-family:var(--dsw-font-family-code,Menlo,monospace);font-size:11px;white-space:pre-wrap;
  word-break:break-all;background:var(--dsw-alias-bg-base,#0d1117);border:1px solid var(--dsw-alias-border-l1,#22272e);
  border-radius:6px;padding:8px;margin:6px 0 0;max-height:340px;overflow:auto;color:#ced4da}

/* 监控卡片 */
.comac-wb-moncard{display:flex;flex-direction:column;gap:4px}
.comac-wb-bar{height:6px;border-radius:3px;background:var(--dsw-alias-bg-layer-3,#232a33);overflow:hidden;margin-top:4px}
.comac-wb-bar>div{height:100%;background:#4dabf7}
.comac-wb-copy{cursor:pointer;color:#74c0fc;font-size:11px;border:none;background:none;padding:0}
.comac-wb-chip{font-size:10px;border:1px solid var(--dsw-alias-border-l2,#2b3038);border-radius:10px;
  padding:1px 8px;color:var(--dsw-alias-label-dimmed,#868e96);margin-right:6px}
`;
