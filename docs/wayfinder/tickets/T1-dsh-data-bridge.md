# T1 · DSH 内嵌页的数据桥

- Label: `wayfinder:research`（AFK） · Status: **closed**（2026-08-22 研究子代理回报） · Blocked by: —

## Question

DSH Web GUI 的 client plugin 机制能否支撑"内嵌工作台页"？必须回答：

1. client plugin 如何注册页面/路由、bundle 如何加载（与 `~/.dsh/profiles/web/cordis.patch.yml`、HMR 的关系）？
2. client plugin ↔ 后端的数据通道：前端能否调用 agent 工具（如 comac_*）？server 端插件能否暴露 HTTP/RPC 端点给自家前端？有没有第三条桥（如静态注入、文件 API）？
3. checkout 内有无既有 client plugin 示例可抄？
4. dev 工作流事实：改 client plugin 代码后如何生效（HMR 条件、构建产物位置）？

证据源：DSH 实现 checkout `/Users/Zhuanz/.npm-global/lib/node_modules/@deepseek-ai/dsh/`。
成果：`research/T1-dsh-data-bridge.md`——能力矩阵 + 候选桥接方案清单（各带证据文件路径）。

## Resolution

**结论：能内嵌。** DSH 无 URL 路由，页面 = client plugin 向命名 slot 注册组件（工作台最自然落点：`conversation.view` ViewMap，对标 ui-trajectory 整页视图）。数据通道四选一：

- ✗ 前端直调 agent 工具：**无此机制**（工具在 per-session agent plane，全 grep 无 tools/call）
- ✓ **host 插件 `ctx.webServer.register({kind:"prefix"})` 挂 `/comac/*` JSON 路由活读仓库文件，前端 fetch——研究推荐方案**（本机 `~/.dsh/plugins/dsh-comfyui` 的 /comfyui 代理即实证先例；薄代理/活读/内网可移植/实现面四标准全优）
- ✓ Typert Remote Service + 通用 `ctx.connection.rpc.call("/api","ns/method")`：机制实证，但自定义 namespace 无代码生成的组合未实证；走 Gateway 有 trusted-host 围栏，安全性优于裸路由——备选
- ✗ index-inject 静态全局：仅加载期快照，不能作主通道

**三大风险**：① client bundle 必须打成 `window.__ModuleLoader__.load` lazy-CJS factory 格式（官方 tsdown，npm dist 不含配置，需自建打包）→ 已切出验证票 [T9](T9-client-bundle-packaging.md)；② 裸路由无鉴权，绑 0.0.0.0 时 LAN 裸露；③ 新增插件包须重启 dsh web（HMR 只覆盖 bundle 内容变化——第三方有 watch 脚本重写产物即可热替换）。

能力矩阵、四候选方案粗评、全部证据路径：[研究报告](../research/T1-dsh-data-bridge.md)。
