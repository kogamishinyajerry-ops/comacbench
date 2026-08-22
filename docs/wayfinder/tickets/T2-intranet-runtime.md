# T2 · 内网前端运行时事实

- Label: `wayfinder:research`（AFK） · Status: **closed**（2026-08-22 研究子代理回报） · Blocked by: —

## Question

工作台最终要可移植到 intranet（离线商业栈）。从仓库证据推导并标注置信度：

1. 内网 JS 运行时：node 可用性有无证据？DSH 本身在内网怎么跑（若工作台内嵌 DSH，DSH web 在内网的存在形式是什么）？浏览器约束？
2. 依赖本地化：env-matrix.md 的 pip 分阶段清单精神映射到 npm 依赖时，镜像/打包流程长什么样？
3. 产出"dev 先行 + 本地化硬规矩"的可执行校验清单草案（什么样的依赖/写法违规）。

证据源：仓库 `env-matrix.md`、`README.md`、`plugin/dsh-comac-benchmark/README.md`、`registry/registry.yaml`。
查不到的明确标"未知/需人工确认"，不许编。成果：`research/T2-intranet-runtime.md`。

## Resolution

**结论**：内网 JS 运行时全仓库近零证据——唯一沾边的是 `env-matrix.md` L43"内网 DeepSeek Harness 代理运行时"，但未交代形态/语言/是否含 web GUI；node/npm/浏览器/Web 服务约束零陈述。pip 手工导入纪律已成功机械映射为 npm 流程，并给出关键简化：**dev 侧一次构建自包含静态 dist，内网只拷目录**（浏览器运行时不需要 npm）；仓库已有零依赖先例（comac 插件无 dependencies）。本地化校验清单草案 4 层 20 条（A 依赖/B 写法/C 构建/D 验收），node-gyp 判定分两层：运行时制品含原生模块=违规，构建期工具链=可接受。

**暴露的风险**：若内网 DSH 不含 web GUI，"DSH GUI 内嵌页"载体决策在内网侧落空 → 已毕业为新票 [T8 · 内网 DSH 形态人工确认](T8-intranet-dsh-shape.md)（阻塞 T6）。

详细证据与 7 条人工确认问题清单：[研究报告](../research/T2-intranet-runtime.md)（含 Q1–Q7、npm 映射表、20 条校验清单全文）。
