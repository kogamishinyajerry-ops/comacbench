# T9 决策票实证：client bundle 打包格式验证

- 日期：2026-08-23（研究子代理 wayfinder 产出）
- 实验插件：`/Users/Zhuanz/projects/jerry-personal/JerryDSH-COMACBench/.attic/t9-hello-client/`（复现步骤见其 README.md）
- scratch 实例：`DSH_HOME=/tmp/dsh-t9-home`，`dsh --profile web --patch .../t9-overlay.yml --port 3199 --no-open`，实际 URL `http://127.0.0.1:3199`（已杀）
- **主实例防护**：全程未重启/未改 3080 实例；`~/.dsh/profiles/web/cordis.patch.yml` 未动（验证后 mtime 仍为 8月22 22:40，早于本任务）；3080 收尾时 curl 200。中间有一次 `dsh web --help` 试图写 `~/.dsh/profiles/web/cordis.yml`（prepareProfile 的固定动作），被 sandbox 拦下（EPERM），未造成任何写入；此后全程 `DSH_HOME=/tmp/dsh-t9-home` 隔离。

---

## 验证点逐项结论

| # | 验证点 | 结果 | 证据 |
|---|---|---|---|
| 0 | 静态契约解析（不起服务） | **PASS** | `validate-static.mjs`：mock 最小 cordis ctx 驱动**真** `ClientModuleRegistry`，图行 `{id:"dsh-t9-hello", url:"/plugins/dsh-t9-hello/client.js?rev=4dff284cc0fe", inject:[...]}` 生成；`serveBundle` 返 200 且正文以 `window.__ModuleLoader__.load({` 开头 |
| a | bundle 被识别并注入 `__DSH_BOOT__` | **PASS** | `curl 3199/` 含 `"id":"dsh-t9-hello","url":"/plugins/dsh-t9-hello/client.js?rev=4dff284cc0fe",...`；headless 浏览器 `window.__DSH_BOOT__` 43 entries 含本行 |
| b | `/plugins/<id>/client.js` 可访问、factory 格式 | **PASS** | `curl -w` → 200, 1844 bytes；首行 `window.__ModuleLoader__.load({` |
| c | `/comac/ping` 返回 JSON | **PASS** | `curl` → `{"ok":true,"ts":...,"plugin":"dsh-t9-hello"}` status 200 |
| d | 页面端到端：`conversation.view` 出现视图并 fetch 到 ping | **PASS（headless 自动化）** | Playwright：会话头部渲染出 **Chat / Trajectory / T9 Hello** 三 tab；点击 T9 Hello → 视图渲染 `build: t9-build-0001` + ping JSON；console/page 错误均为零。截图：/tmp/dsh-t9-home/e2e-1-session.png（tab 栏）、e2e-2-view.png（视图+JSON） |
| 5 | HMR 热替换（不刷新页面） | **PASS（headless 自动化）** | `hmr.py`：打开视图后置 `window.__T9_MARKER__`，sed 改 BUILD_STAMP→`node build.mjs` 重打包；约 1-2s 后视图变为 `t9-build-0002` 且 marker 存活（无整页刷新）；服务器侧 `curl /plugins/dsh-t9-hello/client.js` 立即含新 stamp |

**无遗留人工确认项**——d 与 HMR 两项均已 headless 自动化跑通并留截图。

## 成功的挂载形态

| 形态 | 结果 |
|---|---|
| **scratch profile 的 node_modules 符号链接 + overlay `name: dsh-t9-hello`** | **全通**（host 路由 + client bundle 图行 + 视图 + HMR）。链接位置：`$DSH_HOME/profiles/node_modules/dsh-t9-hello` → 包目录（与官方包共享 `healProfilesModuleFallback` 建的同一目录） |
| 绝对路径 `name: /abs/.../lib/index.js` | **半通**：host 半正常加载（`/comac/ping` 200），但 **client 半不被发现**——`__DSH_BOOT__` 无图行、bundle URL 404。根因：`ClientModuleRegistry.resolveMeta` 用 `require.resolve(`${entryName}/package.json`)` 解析包元数据；entryName 是绝对文件路径时解析失败，被缓存为"非 client 包"（`dsh-client-modules/lib/index.js:377-393`）。双面孔件**必须**以包名可解析形态挂载 |

结论：**双面孔件（host+client）只能走 node_modules/包名形态**；绝对路径形态仅适合纯 host 插件（dsh-comfyui 等先例正是纯 host）。

## 打包配置要点（直接进 T6 规格书）

官方同款 **tsdown 0.22**（`pnpm add -D tsdown`），配置 `.attic/t9-hello-client/tsdown.config.ts`：

```ts
export default defineConfig({
  entry: ["src/client.jsx"],
  format: ["cjs"],            // CJS 体 + 下方 banner/footer 拼出 factory 包装
  platform: "browser",
  deps: { neverBundle: [/^react(\/.*)?$/] },  // react 由宿主静态表提供；勿用已废弃的 external
  outDir: "lib",
  clean: false,               // 关键坑：默认 true 会清空 outDir，把手写的 host 半 lib/index.js 删掉
  minify: false,
  sourcemap: true,
  outputOptions: {
    entryFileNames: "client.js",
    banner: 'window.__ModuleLoader__.load({\n\tid: "<pkg>",\n\tfactory: (require) => {\n\t\tvar module = { exports: {} };\n\t\tvar exports = module.exports;',
    footer: '\t\treturn module.exports;\n\t}\n});\n',
  },
});
```

产物与官方 bundle（`dsh-client-ui-goal/lib/client.js`）逐字节同构：`load({id, factory})` → factory 内 `require("react")` → `exports.apply/inject` → `return module.exports`。

**包契约**（package.json）：`"dsh": {"client": {"platform":"web", "inject":["@deepseek-ai/dsh-client-runtime","@deepseek-ai/dsh-client-ui-conversation"]}}` + `exports["./client"]`。inject 是**客户端 entry 名**（fiber 等待序），不是服务名；`slots` 服务由 `@deepseek-ai/dsh-client-runtime` 提供（其 client.js:35 `super(ctx,"slots")`），`conversation.view` 插槽由 `dsh-client-ui-conversation` 注册——注册视图两者都需要。

**视图注册最小形态**（对标 trajectory bundle:7341）：

```js
ctx.slots.inject("conversation.view", () => ctx.slots.register({
  name: "conversation.view", id: "t9-hello", order: 99, label: () => "T9 Hello",
}, MyComponent));
```

**host 半契约**：`export { apply, inject, name }`；`inject = ["webServer"]`；`ctx.effect(() => ctx.webServer.register({kind:"prefix", path:"/comac", handler}))`。

## 过程中的坑与发现（全是 T6 规格书素材）

1. **tsdown 默认 clean 清空 outDir** → 手写的 host 半 `lib/index.js` 首次构建即被删，scratch 首启报 `Cannot find module .../lib/index.js`。修法：`clean: false`（或 host 半也走构建）。
2. **`--patch` 是顶层 flag**：`dsh --profile web --patch x.yml --port 3199`；`dsh web --patch` 不被 web 子命令接受。
3. **`DSH_HOME` 环境变量完整重定向 home**（`dsh-home-paths/lib/index.js:73`）：scratch 实例零接触 `~/.dsh`。profile 缺失时自动从内置模板初始化（`dsh-app-boot/lib/index.js:539-545`），`healProfilesModuleFallback` 自动把全部官方包链进 `$DSH_HOME/profiles/node_modules`。
4. **GUI 首跑两道弹窗**（Internal Testing Notice → Continue；API key → Configure later）与 **Choose workspace 走原生目录选择器**（`host.pickDirectory`，headless 不可自动化）——e2e 需用 `POST /api/workspace.create`（payload `{path}`）+ `POST /api/session.create`（payload `{workspaceId}`）旁路播种，wire 格式 `{type:"client-request", rpcId, method, payload}`（`dsh-client-connection/lib/client.js:6203-6227`）。
5. **tab 栏只在非 blank 会话渲染**（`ConversationSessionHeader` 的 `hideChrome`，ui-conversation client.js:7315-7330）；无会话时视图已注册但不可见。
6. HMR 生效链路实证：`node build.mjs` 重写 `lib/client.js` → 500ms stat 轮询 → `clientModules.rebuilt` 重算 rev → SSE 广播 → 视图热替换，全程无刷新、无重载标记丢失。

## 对 COMAC 工作台（方案 1）的落地确认

T1 推荐方案的唯一真难点（lazy-CJS factory 打包）已解除：tsdown 公开版即可复刻官方格式，无需源 monorepo。第三方双面孔件的完整配方 = 本仓库 `.attic/t9-hello-client/` + node_modules 形态挂载 + 重启该 dsh web 实例一次（HMR 之后接管全部内容更新）。
