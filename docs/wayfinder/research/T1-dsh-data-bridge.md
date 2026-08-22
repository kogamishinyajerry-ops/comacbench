# T1 决策票研究：DSH 内嵌页的数据桥

- 日期：2026-08（研究子代理 wayfinder 产出）
- 证据源：`/Users/Zhuanz/.npm-global/lib/node_modules/@deepseek-ai/dsh/`（npm 安装的 dsh 0.1.1-rc.2；只含 CLI + 全部 cordis 插件包的构建产物，**不含** apps/web 源码）
- 纪律：每条结论附 checkout 内文件路径；【推测】与实证分开标注。

---

## 问题 1：页面注册 —— client plugin 如何注册新页面/导航项

### 结论（实证）

DSH Web GUI **没有 URL 路由器**（对全部 `dsh-client-*/lib/client.js` grep `pushState|location.hash|react-router|useNavigate` 零命中）。UI 是 **slot（插槽）组合制**：client plugin 通过 `ctx.slots.register(...)` / `ctx.slots.inject(...)` 把 React 组件挂进命名插槽，即完成"页面/区块"注册。

**client plugin 的包契约**（证据：`node_modules/@deepseek-ai/dsh-client-modules/lib/index.js`）：

1. `package.json` 声明 `"dsh": { "client": { "platform": "web", "inject": [...], "immediately"?: bool, "external"?: [...] } }`（解析逻辑：`dsh-client-modules/lib/index.js:120-134` `parseDshClient`）。
2. `exports["./client"]` 指向**预构建的浏览器 bundle**（`clientExportOf`，同文件 `:136-146`）。bundle 必须是 lazy-CJS factory 格式：执行时调 `window.__ModuleLoader__.load({id, factory})` 注册工厂，副作用在物化时才跑（同文件 `:16-31` 头注释）。
3. 包同时是一个 **host loader entry**（node 半，`lib/index.js` 导出 `apply`/`inject`，纯 UI 插件可以是空 apply——实证：`dsh-client-ui-goal/lib/index.js` 全文就是一个空 `apply() {}` 加注释）。
4. host 侧 `ClientModuleRegistry`（`dsh-client-modules/lib/index.js:258-491`）增量扫描 Loader entries → 解析 `${name}/package.json` → 把图行 `{id, url: /plugins/<id>/client.js?rev=<sha1-12>, inject, external}` 组成 `window.__DSH_BOOT__`，并通过 `ctx.webServer.register({kind:"prefix", path:"/plugins", ...})` 供 bundle 文件（`:295-299`、`:459-490`）。

**注册入口 = cordis loader 行**。web profile 的组合顺序：`~/.dsh/profiles/web/package.json` 的 `dsh.profile.bundles`（dsh-base → dsh-web-app → 其他 bundle）→ 各 bundle 的 `cordis.patch.yml` → `~/.dsh/profiles/web/cordis.patch.yml`（用户层）→ `--patch` overlays。官方 roster 实证：`node_modules/@deepseek-ai/dsh-web-app/cordis.patch.yml`（全部 `dsh.client` 行的 insert 列表）。用户层实证：`~/.dsh/profiles/web/cordis.patch.yml` 已用 `- insert: - id: ... / name: /绝对路径/index.js` 挂载了 dsh-comfyui、dsh-comac-benchmark 等 host 插件。

**可挂的"页面"位点**（实证自各 client bundle）：

| 插槽 | 语义 | 证据 |
|---|---|---|
| `root` 的 children：`sidebar` / `conversation` / `details` / `shell.overlay` | 三栏壳的四个区 | `dsh-client-ui-layout/lib/client.js:405-426` |
| `conversation.view`（ViewMap） | 会话区可切换视图（trajectory 即一例"整页"） | `dsh-client-ui-trajectory/lib/client.js:7341-7342`；package.json 描述 "registering into the conversation ViewMap" |
| `conversation.chat.node` / `conversation.input.dock` | 聊天节点/输入坞 | `dsh-client-ui-goal/lib/client.js:387-410` |
| `settings.section` 等 | 设置页命名空间分节 | `dsh-client-ui-settings-general/lib/client.js:497-522` |

> 【推测】COMAC "工作台"页最自然的落点：`conversation.view` ViewMap 新增一个视图（对标 trajectory），或 `details` 面板。无需新建壳层。

---

## 问题 2：数据通道

### (a) 前端直接调 agent 工具（如 comac_registry）——**未发现可行路径**

工具注册在 agent plane（每会话 preset realm），web 表的 `dsh-web-app/cordis.patch.yml` 尾部把 `tool-*` 行全部 `disabled: true` 并移到 preset 后面；API Gateway 暴露的是 **Service 的 Typert Remote 端点**，不是工具目录。全 grep `tools/call|callTool` 于 `dsh-host-apiproxy` / `dsh-api-gateway` 零命中。未发现任何"浏览器调 agent 工具"的 RPC。

### (b) server 端插件注册自定义 HTTP 端点 ——**可行，且有本机实证**

host 插件 `inject: ["webServer"]` 后：

```js
ctx.webServer.register({ kind: "prefix"|"exact", path, handler(req,res) })
```

- API 定义：`dsh-host-webserver/lib/index.js:128-140`（`register`，重复 (kind,path) 抛错）、`:142` `registerUpgrade`（WebSocket 升级路由）、`:157` `registerFallback`。
- **本机实证**：`~/.dsh/plugins/dsh-comfyui/lib/index.js:138-152` —— 注册 `kind:"prefix", path:"/comfyui"` 的反向代理，前端直接 `fetch("/comfyui/...")`。该插件经 `~/.dsh/profiles/web/cordis.patch.yml` 绝对路径挂载，注释自述 "hot-reloads"。
- SSE 推送也可走此路：`dsh-client-hmr/lib/index.js:132-159` 在 `/plugins/events` 上挂 text/event-stream。
- 风险：webserver 服务本身**不做鉴权**（`dsh-host-webserver/lib/index.js` 全文无 trust/auth 逻辑）；默认绑 127.0.0.1，若绑 0.0.0.0 则自定义路由对 LAN 裸露。对比：Gateway RPC 走 `authority: "trusted-host"` 围栏（`dsh-api-gateway/lib/index.js:62`）。

### (c) 其他桥

1. **Typert Remote RPC（类型化 Service 远程调用）—— 官方数据通道**。host 侧：class 继承 `TypertRemoteService`、方法加 `@Remote("name")` 装饰器，`super(ctx, "serviceKey")` 的 key 即默认 wire namespace（`dsh-typert-protocol/lib/index.js:42-64` `bindTypertRemote`；实证服务：`dsh-host-plugin-inventory/lib/index.js:64-117` 暴露 `pluginInventory/list`）。Gateway 动态认领任何带 `typertRemote` 绑定的 Service（`dsh-api-gateway/lib/index.js:65-85` `claimsEndpoint/collectSrcClaims`）。浏览器侧：
   - 类型化客户端是**编译期生成**的（`dsh-api-remotes/lib/client.js:6041-6065`，内置 goals/commands/cordis-runner 等 7 个 contribution）；
   - **但存在通用调用口**：`ctx.connection.rpc.call("/api", "<namespace>/<method>", payload)`（`dsh-client-connection/lib/client.js:10196-10235` `createWebConnectionRpc`），任何 client plugin 可用它打自定义 namespace，无需代码生成。
   - 前端消费实证：`dsh-client-ui-goal/lib/client.js:419-434` `ctx.remote.goals.edit/pause/resume/clear(...)`。
2. **index 静态注入（window 全局）**：host 插件监听 `"webserver/index-inject"` 事件，往注入表 push `{kind:"global", name, value}` 行，渲染进 index.html `<head>`（实证：`dsh-client-modules/lib/index.js:300-302` 注入 `__DSH_BOOT__`；渲染器：`dsh-host-webserver/lib/index.js:24-78` `renderIndexInjections`）。适合启动期静态快照，**非活读**。
3. `window.__DSH_BOOT__` 本身只是 client 模块图（`{rev, entries[]}`），不是应用数据通道。
4. WebSocket：connection 本身是 "HTTP-up/WebSocket-down"（`dsh-client-connection/package.json` 描述），自定义 ws 可经 `webServer.registerUpgrade` 挂，但无现成客户端协议封装——【推测】实现面大，不建议。

---

## 问题 3：既有示例

checkout（npm dist + 本机 profile）内的 client plugin 实例：

| 插件 | 形态 | 用的通道 |
|---|---|---|
| `dsh-client-ui-goal` | slot 注入（dock + chat node） | Typert Remote `ctx.remote.goals.*`（类型化生成客户端） |
| `dsh-client-ui-trajectory` | `conversation.view` ViewMap 整页 | session projection 事件流（connection 下行） |
| `dsh-client-ui-jobs` / `ui-deliverables` / `ui-message-feedback` 等 30+ `dsh-client-ui-*` | slot 区块 | 各自 Remote namespace / 投影 |
| `dsh-client-hmr` | 无 UI | **自定义 exact 路由 + SSE**（`/plugins/events`） |
| `dsh-client-modules` | 无 UI | **自定义 prefix 路由**（`/plugins/<id>/client.js`）+ index-inject 全局 |
| `~/.dsh/plugins/dsh-comfyui`（本机，第三方） | host-only（无 client 半） | **webServer prefix 代理 `/comfyui` + tools** —— 与 COMAC 需求最接近的先例 |

纯 UI 插件的 node 半为空 apply（`dsh-client-ui-goal/lib/index.js`）；需要数据的插件 = host 半提供 Service/路由 + client 半消费。

---

## 问题 4：dev 工作流

- **生产模式**：client bundle 是**预构建产物**（`lib/client.js`，sha1-12 作 rev 缓存戳）。源 monorepo 里构建工具是 **tsdown**（`dsh-client-ui-goal/package.json` scripts: `"bundle": "tsdown"`, `"watch": "tsdown --watch"`）。改 client 源码后必须重新出 bundle 文件。
- **HMR 链路**（全实证）：`dsh-client-hmr` node 半以 500ms stat 轮询每个 graph 行的 bundle 文件（`dsh-client-hmr/lib/index.js:78-114`）→ 内容变了调 `clientModules.rebuilt(id)` 重算 rev（`dsh-client-modules/lib/index.js:325-339`）→ SSE 广播 `rebuilt` 帧 → 浏览器半热替换该 entry（`dsh-client-hmr/lib/client.js:36-60`：`invalidate → prefetch → dispose 旧 fiber → entry.refresh()`，**不刷新页面**）。
- **成立条件**：有人**重写 bundle 文件**。npm 安装形态下没有源码 watch；官方形态是源 monorepo 根跑 `pnpm run dev:web`（`dsh-web-app/README.md:17` 与 `dsh-web-app/cordis.patch.yml` 的 client-hmr 行注释均证实）。注意 `dsh-web-app/cordis.patch.yml` 里 host 侧 `hmr` 行被禁用，但 **client-hmr 行是常驻挂载的**（"always mounted … idle until a rebuild watcher actually rewrites client bundles"）——即第三方只要让构建产物被重写（自己的 watch 脚本即可），热替换就生效。
- **新增/移除 client plugin 包**：包元数据缓存不过期，**须重启 dsh web**（`dsh-client-modules/lib/index.js:80-85`："plugin-set changes take effect on restart"）。
- 【推测】第三方 client 包可用绝对路径挂载（host 插件已实证可行：`~/.dsh/profiles/web/cordis.patch.yml` 里 5 个绝对路径插件）；但 entry id 会含路径分隔符，`/plugins/<id>/client.js` URL 形态未验证——**更稳的做法**是把包装进 `~/.dsh/profiles/web/node_modules`（该目录已有 package.json + 已装 `dsh-routing-suite` 先例）或以包名 link。

---

## 能力矩阵

| 通道 | 可行性 | 证据 | 风险 |
|---|---|---|---|
| A. 前端调 agent 工具 | ✗ 未发现机制 | 全 grep 无 tools/call；工具在 per-session agent plane | — |
| B. webServer 自定义 HTTP 路由（prefix/exact，含 SSE） | ✓ 实证可用 | `dsh-host-webserver/lib/index.js:128`；本机 `~/.dsh/plugins/dsh-comfyui` /comfyui 代理 | 裸路由无鉴权，绑 0.0.0.0 时 LAN 裸露；需自己管缓存/一致性 |
| C. Typert Remote Service + 通用 `ctx.connection.rpc.call("/api", ...)` | ✓ 机制实证；自定义 namespace 的组合（无代码生成客户端）为【推测】可行 | `dsh-typert-protocol/lib/index.js:42-64`；`dsh-api-gateway/lib/index.js:65-85`；`dsh-client-connection/lib/client.js:10196-10235` | 依赖 `@deepseek-ai/dsh-typert-protocol` 可解析性；wire 校验 schema 需手写（strict decode）；版本耦合 |
| D. index-inject 静态全局 | ✓ 实证 | `dsh-client-modules/lib/index.js:300-302`；`dsh-host-webserver/lib/index.js:24-78` | 仅加载期快照，非活读 |
| E. 自定义 WebSocket | 机制存在（registerUpgrade）但无先例封装 | `dsh-host-webserver/lib/index.js:142` | 实现面最大，不建议 |

## 候选数据桥方案（COMAC 工作台）

四标准：薄代理 / 活读时延 / 内网可移植 / 实现面。

| # | 方案 | 薄代理 | 活读时延 | 内网可移植 | 实现面 | 粗评 |
|---|---|---|---|---|---|---|
| 1 | **host 插件加 `/comac/*` prefix 路由，实时读仓库 registry.yaml/results/reports 吐 JSON；client plugin fetch + slot 注册页面** | 优（路由里直接读文件，SSOT 仍在仓库） | 优（每次请求活读） | 优（零代码生成、零协议依赖，只需 node 内置模块，照抄 dsh-comfyui 形态） | 小：1 个 host 半（路由）+ 1 个 client 半（fetch+渲染，需 tsdown 类打包出 factory 格式） | **推荐**。唯一真难点是 client bundle 的 lazy-CJS factory 打包格式 |
| 2 | host 插件提供 TypertRemoteService（comac namespace）+ 前端 `ctx.connection.rpc.call("/api","comac/...")` | 优 | 优 | 中（import typert-protocol，与 dsh 内部包版本耦合；通用 rpc.call 打自定义 namespace 为【推测】未实证组合） | 中 | 备选。走 Gateway 有 trusted-host 围栏，安全性优于裸路由 |
| 3 | 纯 host 插件 + 复用现有 UI（如让 agent 用 comac_* 工具把结果写进会话/deliverables） | 优 | 中（非页面） | 优 | 最小 | 不满足"内嵌工作台页"诉求，仅作降级 |
| 4 | index-inject 启动快照 | 优 | 差（刷新才更新） | 优 | 小 | 仅适合静态元信息，不能作主通道 |

**最大风险**（方案 1）：① client bundle 必须打成 `window.__ModuleLoader__.load({id, factory})` 的 lazy-CJS 格式（官方用 tsdown，配置在源 monorepo，npm dist 不含），需自建打包；② 裸路由无鉴权，绑定面扩大时需自行加围栏；③ 新增插件包须重启 dsh web 生效（HMR 只覆盖 bundle 内容变化）。
