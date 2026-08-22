# T2 · 内网前端运行时事实 — 研究报告

- 票据：`docs/wayfinder/tickets/T2-intranet-runtime.md` · Label: `wayfinder:research`
- 日期：2026-08-22 · 研究子代理（只读研究，唯一写操作 = 本文件）
- 标注体例：**[实证]** = 有仓库文件出处；**[推断]** = 研究员合理外推；**[未知]** = 仓库无证据，需人工确认。

---

## 问题 1：内网 JS 运行时事实

### 1.1 仓库证据里关于内网 node.js / npm / 浏览器 / Web 服务的陈述

逐条检索结论：**仓库几乎没有内网 JS 运行时的直接证据**。唯一沾边的一条：

1. **[实证] env-matrix.md §2 Phase-A（L43）**：
   > `python == 3.11.x  # 与内网 DeepSeek Harness 代理运行时对齐后锁定小版本`

   这是全仓库唯一一处把 DSH 与内网联系起来的陈述。它能确认的 only：内网存在一个"DeepSeek Harness 代理运行时"，且验收纪律假定它存在到"Python 小版本要与它对齐"的程度。它**没有**交代该运行时的实现语言、进程形态、是否含 node、是否含 web GUI。

除此之外的检索结果（均为否定性发现，[实证]=确认无此内容）：

2. **[实证] env-matrix.md 全文（§0–§5）**：两层环境表（§0）只列求解器与 "Python/pip 直连"；§1 env_class 可用性表、§2 分阶段导入清单、§3 商业工具批处理要求、§5 验收人动作清单，**全部只谈 Python 包 / 数据 / 商业求解器**。无 node、npm、浏览器、Web 服务任何字样。
3. **[实证] registry/registry.yaml 头注（L1–16）**：env_policy = "见 env-matrix.md（OpenFOAM 放弃；Python 手工导入；商业求解器走批处理）"；env_class 取值枚举为 `qa | python_sandbox | data_only | commercial_cfd | commercial_fea | matlab | missing`（dev 期增补 `openfoam_dev`）——**枚举中没有、也无法表达"前端/Web"类环境**。
4. **[实证] README.md「内网环境策略」（L35–40）**：只谈求解器无关原则与"内网仍按 env-matrix.md 分阶段清单手工导入（Python 包）"。无 JS 运行时陈述。
5. **[实证] plugin/dsh-comac-benchmark/README.md「环境契约」（L32–41）**：全部契约是 dev 侧事实（COMAC_BENCH_HOME 默认 mac 路径、docker OpenFOAM、macOS Keychain 注密钥）。「安装/更新」（L43–56）描述 `~/.dsh/plugins/` 拷贝安装——同样是 dev 侧路径与做法，**没有内网安装形态的任何交代**。
6. **[实证] docs/wayfinder/000-workbench-ui-map.md「Decisions so far」（L30）**：内网约束已决的是"dev 先行 + 依赖可完全本地化硬规矩"，且明确把"内网运行时事实"挂给本票（T2）——即地图本身承认这块是空白。

### 1.2 DSH 本身（含 web GUI）在内网的存在形式

**[未知] 仓库无证据。** 具体缺口：

- DSH 是 node 生态（dev 侧证据：插件是 `index.js` ES module、`~/.dsh/profiles/web/cordis.patch.yml`、GUI 由 web 服务器提供），但 env-matrix 的"内网 DeepSeek Harness 代理运行时"（1.1-条1）究竟是：完整 DSH（含 web GUI）？仅 agent 内核 headless？还是另一种内网定制形态？——仓库没有任何文件回答。
- 工作台已定载体形态 = "DSH GUI 内嵌页"（000-workbench-ui-map.md L27，用户决策）。**若内网 DSH 不含 web GUI，该决策在内网侧失去载体**——这是 T2 暴露的最大风险点，必须在规格书（T6）之前由人确认。

### 1.3 浏览器约束

**[未知] 仓库无证据。** 内网终端有无浏览器、是什么浏览器/版本、是否允许访问本机 loopback Web 服务、有无组策略限制（禁用 JS？禁 DevTools？强制 IE 兼容？）——全仓库零陈述。

### 1.4 需人工确认问题清单（问验收人/IT/用户本人）

| # | 问题 | 为什么重要 |
| --- | --- | --- |
| Q1 | 内网机器是否装有 node.js？版本？若无，是否允许手工导入 node 发行包（单二进制，类比 wheel 导入）？ | 决定 DSH 及任何前端构建链能否在内网存在 |
| Q2 | "内网 DeepSeek Harness 代理运行时"（env-matrix.md L43）的确切形态是什么？谁部署的？含不含 web GUI 层？ | 工作台"DSH GUI 内嵌页"载体在内网是否成立 |
| Q3 | 内网是否允许跑本机 Web 服务（loopback 端口监听）？有没有端口/进程白名单？ | DSH web 及任何本地服务形态的前提 |
| Q4 | 内网终端浏览器是什么（内核/版本）？组策略限制（JS、DevTools、本地文件、WebSocket）？ | 前端技术选型的兼容性底线（WebSocket 是 DSH GUI 实时通道的候选依赖） |
| Q5 | 内网 DSH 的模型 provider 是什么（外网 LLM API 显然不可用）？本地模型网关？ | 若工作台数据桥走 agent 工具（T1/T3 候选），内网 agent 是否可用决定桥的可行性 |
| Q6 | npm 包是否有与 Python wheel 同等的"手工批量导入"通道与审批纪律？有无内部 npm 镜像（如 Verdaccio/Nexus）计划？ | 依赖本地化流程的形态（见问题 2） |
| Q7 | 内网验收人是谁、对"拷一个目录进去就能跑"的制品接受度如何（对照 env-matrix §5 动作清单的口味）？ | 打包方案该做成"绿色目录"还是"安装脚本" |

---

## 问题 2：依赖本地化映射（pip 纪律 → npm 纪律）

### 2.1 仓库证据：env-matrix 的 Python 分阶段手工导入纪律原文要点

[实证] 出自 env-matrix.md §2（L35–38）与 §5（L102–109）：

1. **无镜像前提**："无内部 PyPI 镜像，Python 包由验收人手工批量导入"（L3）。
2. **减负原则**："一个里程碑一批 wheel，导入后把逐包版本写进 `environment_digest` 归档，之后同阶段 benchmark 共享该环境，不再逐个导入"（L37）。
3. **机械流程**：外网机 `pip download -d <dir> -r <phase>.txt`（或 `pip wheel`）获取**全量依赖闭包** → 整目录拷入内网 → `pip install --no-index --find-links=<dir>`（L38）。
4. **分阶段**：Phase-A（M1/M2 qa+code_exec）/ Phase-B（M3/M4 仿真自建包）/ Phase-C（M4 data_only）/ Phase-D（batch-2 CAD/FEA/飞控）（L40–73）。
5. **数据同纪律**：外网下载子集 → 拷入内网；镜像前先过 license-status（L75–81、L107；license 闸门见 registry/license-notes.md"非 confirmed-* 一律不得镜像"，README.md L17）。
6. **版本归档**：求解器/包版本写入 `environment_digest`（§3 L92）；数据 sha256 锁定进 PROVENANCE.md（各 data/**/PROVENANCE.md 实证）。

### 2.2 机械映射到 npm 的流程（标注证据 vs 推断）

映射骨架（逐条对应 2.1）：

| pip 纪律（[实证]） | npm 对应做法 | 性质 |
| --- | --- | --- |
| 无内部 PyPI 镜像，手工批量导入 | 假定内网无 npm registry 镜像（待 Q6 确认） | [推断]（对称假设） |
| 外网机 `pip download` 全量闭包 | 外网机用 `npm pack` 逐包打 tarball 递归闭包；或更简单：`npm install` 后整个 `node_modules/`（或 `npm cache`）打包；或 `npm ci` 后 `tar` 产物 | [推断]（通用 npm 做法，非仓库证据） |
| 内网 `pip install --no-index --find-links` | 内网 `npm install --offline`（用带过去的 cache）/ `npm i <dir>/*.tgz` / 直接解包 node_modules | [推断] |
| 一个里程碑一批、版本写 environment_digest | 一个工作台版本一批依赖，lockfile（package-lock.json 逐包版本+integrity hash 天然就是 digest 等价物）归档进 git | [推断] + [实证]（lockfile 的 sha 锁定语义与仓库 PROVENANCE sha256 纪律同构） |
| 镜像前过 license-status | npm 依赖逐包 license 清点（`license-checker` 类工具），非 confirmed 不引入 | [推断]（流程类比），[实证]（仓库确有"先许可证后镜像"硬纪律：README.md L26、L79 使用规则 1） |
| 分阶段（Phase-A…D） | 工作台是单一制品，倾向"一次一批、pinned lockfile"，不分阶段 | [推断] |

**关键简化（[推断]，强烈建议写进规格书）**：前端与 Python 沙箱不同——**浏览器运行时根本不需要 npm**。最稳的本地化形态是 dev 侧一次性构建出自包含静态制品（bundler 把所有依赖打进 `dist/`：一个 HTML + 若干 JS/CSS/字体文件，零运行时依赖、零 node_modules），内网只做"拷贝 dist 目录"。这把 2.2 的整张映射表压缩成"拷一个目录"，与 env-matrix §5 验收人动作清单的口味一致。**前提**是内网存在能 serve 或打开这些静态文件的宿主——回到问题 1 的 Q2/Q3（DSH web 在内网的形态），这正是两问的咬合点。

**dev 侧已有先例（[实证]）**：plugin/dsh-comac-benchmark 自身就是零 npm 依赖纪律的样板——package.json 无 dependencies 字段，index.js 只 import `node:` 内建模块（child_process/fs/path/os），README 自称"零依赖、只做薄代理"（L6–7）。说明"能不引依赖就不引"已是本仓库前端侧（广义的 JS 侧）的既定口味。

---

## 问题 3：本地化校验清单草案（"dev 先行 + 本地化硬规矩"）

> 依据的硬规矩原文（[实证] 000-workbench-ui-map.md L16）："任何依赖必须可完全本地化打包，禁止运行时外部请求（字体/CDN/遥测）"。
> 清单分四层：A 依赖引入、B 代码写法、C 构建配置、D 打包验收。每条给检查方法。性质标注：条目多数为 [推断]（研究员起草），凡有仓库出处者标 [实证]。

### A. 依赖引入纪律

| # | 规则 | 违规例 | 检查方法 |
| --- | --- | --- | --- |
| A1 | 每个新增 npm 依赖必须过 license 清点，非 confirmed 不引入（类比 license-notes.md 闸门 [实证]） | 引了 license 不明/传染性许可的包 | `npx license-checker --production --summary` + 逐包复核；结果归档（类比 PROVENANCE） |
| A2 | 拒绝含 `node-gyp`/原生预编译二进制的依赖，除非确认内网可获对应平台预编译产物 | node-canvas、sharp、sqlite3（原生绑定）、esbuild 的平台二进制（注意：构建期用可接受，运行期进制品不可） | `npm ls` 后查各包 `package.json` 的 `scripts.install`/`binary` 字段；CI 加 `npm install --ignore-scripts` 能否通过作为探针 |
| A3 | 拒绝 postinstall 脚本会联网下载的依赖（隐形外部请求） | 某些 headless 浏览器包、下载预编译二进制的 install 脚本 | 审查 lockfile 各包 install 脚本；`npm ci --ignore-scripts` 构建不破 = 合格 |
| A4 | 依赖数最小化；能用平台/Web 标准 API 就不用包（仓库既有口味：插件零依赖 [实证]） | 为一个格式化函数引 lodash | 每个依赖在规格书/PR 里写一句"为什么必须" |
| A5 | lockfile 必须入库且 pinned（integrity hash 即 digest [实证]纪律的 npm 同构） | 只有 package.json 没有 package-lock.json | git 里存在 lockfile；`npm ci`（而非 `npm i`）可重现 |

### B. 代码写法纪律（运行时零外部请求）

| # | 规则 | 违规例 | 检查方法 |
| --- | --- | --- | --- |
| B1 | 禁止任何 CDN 外链（script/link/img src 指向公网域） | `<script src="https://cdn.jsdelivr.net/...">`、unpkg、jsdelivr | 构建产物 `grep -rE "https?://" dist/`，白名单只放行注释/字符串常量中的文档链接 |
| B2 | 禁止运行时 Web 字体外链；字体必须随制品打包（woff2 本地文件 + @font-face 相对路径） | Google Fonts `<link href="fonts.googleapis.com">` | 同上 grep；`@font-face` 的 url 必须解析到 dist 内文件。中文字体大，需决策子集化（fonttools subset）或系统字体栈——[未知] 待规格书定 |
| B3 | 禁止遥测/统计 SDK 与任何埋点外发 | Sentry、Google Analytics、posthog、umami | 依赖清单 + 产物 grep 其域名；运行时网络监听（见 D2）零外连 |
| B4 | 禁止运行时 fetch/XHR/WebSocket 到公网地址；数据只能来自本机宿主（loopback/同源）或内嵌快照 | `fetch("https://api.github.com/...")` | 源码 grep `fetch(\|XMLHttpRequest\|new WebSocket\|EventSource`，逐个确认目标为相对路径/同源 |
| B5 | 图标/图片不用外链图床，全部内联（SVG inline 或 base64）或随包 | `<img src="https://...">` | 产物 grep + 构建资源审计 |
| B6 | 源码地图（sourcemap）不发包含外网引用；错误处理不默认外发 | 默认上报的错误边界库 | 检查产物 .map 与库配置 |

### C. 构建配置纪律

| # | 规则 | 违规例 | 检查方法 |
| --- | --- | --- | --- |
| C1 | 构建必须能在外网机一次完成、产物自包含（单 dist 目录）；内网零构建 | 要求内网跑 `npm install && npm run build` | 验收测试：拷 dist 到干净目录即可用（见 D1） |
| C2 | bundler 配置 `base: './'`（相对路径），不假设部署在域根 | Vite 默认 `/` 绝对路径在 file:// 或子路径下失效 | dist/index.html 中资源引用为相对路径；file:// 打开 smoke 测试 |
| C3 | 构建期本身的下载（npm ci、字体子集化工具）只允许发生在 dev 侧 | CI/内网步骤里藏 npm 联网命令 | 流程审查；构建脚本不引用内网路径 |
| C4 | 产物逐文件 sha256 清单随包（PROVENANCE 同构 [实证]） | 无校验手段的裸拷贝 | 构建脚本生成 `SHA256SUMS`，验收人 `shasum -c` |

### D. 打包验收（移植前必跑）

| # | 规则 | 检查方法 |
| --- | --- | --- |
| D1 | 离线安装测试：在无网机器（或禁网 VM/断网环境）从拷入介质安装并打开工作台，全流程可用 | dev 侧 `networkd`/断网实测；内网首装时复测 |
| D2 | 运行时零外连测试：打开工作台全部页面，系统网络监听（如 `nettop`/proxifier/浏览器 DevTools Network 面板过滤非本机域）确认零公网请求 | 逐页操作 + 监听；特别覆盖图表渲染、字体加载、错误路径 |
| D3 | 版本归档：制品版本 + 依赖清单 + sha256 写入归档（对应 environment_digest/PROVENANCE 纪律 [实证]） | 归档文件入库（里程碑快照纪律与 T4 咬合） |
| D4 | node-gyp/原生模块最终判定：凡进制品的依赖一律纯 JS/WASM（WASM 随包可接受）；构建期工具链原生依赖只存在于 dev 侧 | 制品依赖树审查（`npm ls --omit=dev`）+ A2 探针 |

> **关于 node-gyp 的明确结论（[推断]，回答票据点名的问题）**：原生模块算风险，且判据分两层——**运行时制品**含原生模块 = 违规（内网无法编译、平台预编译产物不可控）；**构建期工具链**（如 esbuild 平台二进制）含原生模块 = 可接受，因为构建只在 dev 外网机发生，产物是纯静态文件。这条分界应写进规格书。

---

## 附：本报告证据文件清单

- `env-matrix.md`（§0 两层环境、§2 分阶段导入、§3 批处理、§5 验收人清单；L43 DSH 内网运行时唯一证据）
- `README.md`（内网环境策略 L35–40；使用规则 L77–84）
- `registry/registry.yaml`（头注 env_policy 与 env_class 枚举）
- `plugin/dsh-comac-benchmark/README.md`（环境契约 L32–41；安装 L43–56；零依赖原则 L6–7）
- `plugin/dsh-comac-benchmark/package.json` / `index.js`（零 dependencies、仅 node: 内建的实证）
- `docs/wayfinder/000-workbench-ui-map.md`（本地化硬规矩 L16；载体形态 L27；内网约束决策 L30）
- `registry/license-notes.md`（"非 confirmed-* 一律不得镜像"闸门）
- `CONTEXT.md`（"本地化硬规矩"词汇定义 L18）
