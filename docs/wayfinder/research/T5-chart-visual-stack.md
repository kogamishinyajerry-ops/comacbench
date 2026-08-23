# T5 · 图表库与视觉系统选型 — 研究报告（实测）

- 日期：2026-08-23 · 由主会话直接执行（两次子代理因 `~/.npm` 属主 EPERM 阵亡，改仓库内 npm cache 后手工完成）
- 实验场：`.attic/t5-chart-lab/`（每候选一目录，复用 T9 tsdown 配方：factory 包装 + react neverBundle + `alwaysBundle: /^(?!react($|\/))/`）
- 测量口径：**react 外部化**（宿主提供），minify 开/关两轮，gzip 为 `gzip -c | wc -c`
- 教训（进 T6）：tsdown 默认把 dependencies external——必须显式 `alwaysBundle`；`clean:false` 会保留陈旧产物，静默失败时数字是假的

## 一、宿主事实（读 DSH checkout）

1. **React 18.3.1**（dsh node_modules 实测）——所有候选兼容
2. **宿主自带完整设计令牌系统**（`dsh-client-ui-theme/lib/client.js`，80KB）：
   - 原语层 `--dsw-static-{neutral,neutral-bluish,deepseek,blue,green,amber,red}-*` 色阶
   - 语义层 `--dsw-alias-{bg-layer-*,border-*-l,label-primary,brand-primary,button-*,scrollbar-*}`
   - **字号梯度** `--dsw-font-{xxxs,xxs,xs,s,base,m,l,xl}[-strong]`——高密度工程台原生素材
   - **中文字体栈已解**：`--dsw-font-family` = `-apple-system, …, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei"`；代码字体 SF Mono/JetBrains Mono
   - **明暗双主题**：`.light`/`.dark` 类 + `prefers-color-scheme`
3. 结论：工作台**直接继承宿主令牌**即原生观感；中文与明暗零成本

## 二、候选实测矩阵（react external、factory 包装含内）

| 候选 | min bytes | min gzip | 雷达图 | 热力图 | 渲染 | license | React18 |
| --- | ---: | ---: | --- | --- | --- | --- | --- |
| **echarts 按需**（radar+heatmap+bar+grid/tooltip/legend，CanvasRenderer） | 554,165 | **183,529** | ✅ 内置 | ✅ 内置 | canvas | Apache-2.0 | 无关（命令式） |
| echarts 全量（对照） | 2,718,433† | 643,502† | ✅ | ✅ | canvas | Apache-2.0 | — |
| **visx**（scale+shape+group+grid+tooltip+legend+axis） | 38,618 | **14,528** | ⚠️ LineRadial 组装 | ⚠️ Rect 组装 | SVG | MIT（d3 ISC） | ✅ |
| **chart.js 4** + react-chartjs-2（radar） | 169,344 | 58,613 | ✅ 内置 | ⚠️ 需 matrix 插件（+未测） | canvas | MIT | ✅ |
| d3 直用（scale+shape+selection+array） | 70,196† | 17,845† | 🔧 手写 | 🔧 手写 | SVG | ISC | 无关 |
| recharts | 2,163,465† | 412,279† | ✅ | ⚠️ 自组 | SVG | MIT | ✅（victory-vendor 拖全量 d3；且含 121 个未打包外部件，真实体积更大） |
| uplot + uplot-react | 137,586† | 35,693† | ❌ | ❌ | canvas | MIT | ✅（线图专精，雷达/热力双缺） |

† = minify:false 轮（未做 minify 对照，仅量级参考）。

## 三、分析

- **echarts 按需**：184KB gzip 换雷达/热力开箱质量 + 内置 `dark` 主题 + 中文生态成熟（防重叠、字体回退）+ tooltip/legend 免费实现。代价：canvas 无法直接吃 CSS 变量——令牌映射需启动时 `getComputedStyle` 读 `--dsw-static-*` 色阶构造 JS 主题（~20 行，一次性）。
- **visx**：14.5KB，SVG 原生吃 `var(--dsw-*)`（令牌零成本），React 组件式。代价：雷达轴标签防重叠、热力交互、图例全部自建自磨——"好看"的风险全在我们手上。
- chart.js：折中但热力要插件、主题系统弱。
- d3 直用：实现面最大；recharts：重且拖 d3 全量；uplot：雷达热力双缺——三淘汰。

**Top-2**：echarts 按需（功能完备、开箱即深色、打磨风险最低）vs visx（最轻、令牌原生、打磨风险自担）。决定性权衡：**bundle 从本地磁盘加载不走网络，184KB 的运行时代价≈0**——买质量几乎免费。

## 四、样式方案速评

| 方案 | scoped 安全 | 可打包 | 评 |
| --- | --- | --- | --- |
| **命名空间 CSS 字符串注入**（`<style>` 注入 `.comac-wb-` 前缀 CSS，CSS vars 直用） | ✅ 前缀隔离 | ✅ 纯 JS 内联 | 零依赖、与 factory 单文件 bundle 契合（**loader 只认一个 client.js，CSS 必须内联**） |
| CSS Modules | ✅ 构建期哈希 | ⚠️ 需构建链 CSS 支持并把 CSS 回灌成 JS——factory 契约下要额外加工 | 可行但绕 |
| Tailwind | ✅ 前缀可配 | ⚠️ 构建链复杂化 | 宿主令牌已有，无需再引一套设计系统 |

## 五、复现

```bash
cd .attic/t5-chart-lab/<候选>
npm_config_cache=../.npm-cache npm install
node node_modules/tsdown/dist/run.mjs --minify
wc -c lib/client.js; gzip -c lib/client.js | wc -c
```
