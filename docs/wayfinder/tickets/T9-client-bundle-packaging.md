# T9 · client bundle 打包格式验证

- Label: `wayfinder:task`（AFK——agent 可独立完成） · Status: **closed**（2026-08-23，六项验证全 PASS） · Blocked by: —（阻塞 T3）

## Question

T1 研究证明载体可行，但全压在同一个打包风险上：client plugin bundle 必须是 `window.__ModuleLoader__.load({id, factory})` 的 lazy-CJS factory 预构建格式（官方插件用 tsdown 打出，配置在源 monorepo，npm dist 不含）。

本票 = 最小实证：写一个 hello-world client plugin（往 `conversation.view` ViewMap 注册一个静态页），用自建的 tsdown/rollup/esbuild 配置打出 factory 格式 bundle，挂进本机 dsh web（推荐装进 `~/.dsh/profiles/web/node_modules` 或以包名 link——绝对路径挂载的 `/plugins/<id>/client.js` URL 形态未验证，见 T1 报告 §问题4），验证：

1. bundle 被 `ClientModuleRegistry` 识别并出现在 `window.__DSH_BOOT__`；
2. 浏览器端工厂物化、页面在 ViewMap 出现；
3. HMR：watch 重写 bundle 后页面不刷新热替换（dsh-client-hmr 常驻挂载，第三方产物被重写即生效，T1 已实证链路）；
4. 顺路验证 host 半挂 `/comac/ping` prefix 路由 + 页面 fetch 打通（方案 1 的端到端最小闭环）。

成功标准：hello-world 页在 DSH GUI 可见、可 fetch 到 `/comac/ping` 的 JSON、改 bundle 热替换生效。失败则携失败细节回 T3 裁 fallback（Typert 备选 / 独立 app）。

参考：`docs/wayfinder/research/T1-dsh-data-bridge.md`（格式头注释见 `dsh-client-modules/lib/index.js:16-31`；挂载先例 `dsh-client-ui-goal`、`~/.dsh/plugins/dsh-comfyui`）。

## Resolution

**结论：全过，方案 1 的唯一技术雷已拆。** 六项验证点（静态契约解析 / `__DSH_BOOT__` 图行 / bundle URL factory 格式 / `/comac/ping` JSON / ViewMap 页面端到端 / HMR 无刷新热替换）全部自动化 PASS，无遗留人工确认项（Playwright headless 实证，截图留证）。

**三个直接进 T6 规格书的定论**：

1. **打包配方**：tsdown 0.22 公开版即可复刻官方 lazy-CJS factory 格式——`format:"cjs"` + banner/footer 拼 `window.__ModuleLoader__.load({id,factory})` 包装 + `deps.neverBundle:[/^react/]` + **`clean:false`**（默认 true 会删掉手写 host 半，首坑）。产物与官方 bundle 逐字节同构，无需源 monorepo。
2. **挂载形态定论**：双面孔件（host+client）**只能** node_modules/包名形态挂载；绝对路径形态 host 半可用但 client 半不被发现（根因：`ClientModuleRegistry.resolveMeta` 用 `require.resolve("<name>/package.json")`，路径形态解析失败被缓存为"非 client 包"）。
3. **隔离验证法**：`DSH_HOME=/tmp/...` 完整重定向 + 顶层 flag `--patch`（非 web 子命令）+ 独立端口——scratch 实例零接触主实例，本票全程 3080 未碰。

e2e 旁路播种（workspace.create/session.create API）、GUI 首跑弹窗、tab 栏 hideChrome 条件等 6 条坑全部记录在案。完整证据：[研究报告](../research/T9-client-bundle-packaging.md)；可复现插件源码：`.attic/t9-hello-client/`。
