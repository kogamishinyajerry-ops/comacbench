# 产品收口：工作包主线，诊断和研究分开

决策版本：2026-10-02。机器可读入口为 `registry/product-scope.json`，研究集成、资产版本和许可仍以 `registry/registry.yaml` 及其许可记录为准。

## 默认入口

```bash
python -m comacbench.catalog
python -m comacbench.catalog --role all
python -m comacbench.catalog --research-policy
python -m comacbench.catalog --check
```

默认只推荐 `aviation-workload-starter-v1`，作为文件级工作包 pilot。`workload-change-v1` 是独立的 experimental 工作环境，不能拿它的记录代替 pack 或 Campaign 成绩。data starter 继续作为低门槛接入例子；结构和 CFD 的简单经典题作为校准锚点；core 包保留兼容入口。

`material_present` 只表示入口文件存在。`--check` 核对入口路径及角色表引用的 registry ID，不执行任务或验证 solver readiness。源码工作区缺文件时会明确显示或报错，不默认为部署完成。角色清单不改变旧命令的默认参数，也不是新的离线安装包排除规则。

## 对现有资产怎样取舍

| 内容 | 角色与处理 |
| --- | --- |
| GSM8K、MATH-500、HumanEval、MBPP 及加强测试 | diagnostic；退出工程主线，停止继续扩充同类题库 |
| CFDQuery、AeroEngQA、文献问答、孤立条款抽取 | diagnostic；用于解释知识或证据定位缺口，后续嵌入工作包 |
| CalculiX 基础题、经典 CFD verification/validation | calibration；保留独立检查和工具链回归，减少无新增机制的参数扩题 |
| 基础 CAD、草图、表格、Word/PPT、公式检查器 | component；保留检查器，逐步承担完整工作包的验收子步骤 |
| SuperWing、HiLift 系数、PINN 等 | research；单列物理预测研究，停止以通用 LLM 裸猜系数承载工程主线 |
| 未显式分配产品角色的 registry 条目 | 默认 research；integrated 不自动变成 pilot，新增使用需明确工作包与验收证据 |

本轮没有删除历史任务、重写历史分数、扩大物理容差或放松负例。简单题仍可保护重要的回归能力；退出主线不等于失去全部价值。首页和 CLI 不再用研究题量代表独立工程场景覆盖。

## 下一笔开发投入

当前代码交付了一个可执行的公开合成变更工作包，用来验证以下机制：源资料变化如何传播、哪些证据仍有效、怎样独立复核交付、失败如何被记录。它不应继续扩展成很多孤立合成例子。

后续主线按任务族推进，优先级如下：

1. **把一个已有工程后端接入变更工作包。** 选定参数化通风组件或安装支架，明确公开／授权数据、原生输入和输出、正常与故障样例、最小验证要求。不要在状态重放里重新运行求解器。
2. **完成固定配置的真实 Agent 对照。** 同一批实例、同一预算与工具，比较 Skill／经验包前后；使用逐项改进与退步而非一个平均分。参考程序和故障负例不参与模型成绩。
3. **完成独立同类新任务。** 冻结开发内容、隔离评测材料，明确哪些任务共享机制。公开参数变体与多个随机种子都不能自动构成隐藏迁移证据。

多保真与学习型近似模型在这些基础上接入。应记录前期准备、训练、单次任务及复核成本，最终验收不能只重复调用被测 Agent 使用的近似模型。本轮没有实现这些后端或训练能力。

## 新内容进入主线前的判定

维护者应能回答：这项任务会改变哪一个工程决策？输入是否足够且合法可用？哪项交付可以独立检查？有没有正常与错误负例？已有任务未覆盖的机制是什么？投入成本和环境依赖是什么？

缺少真实后端、可靠参考或可执行判定的内容，可以保留研究记录，但不标为产品主线完成。优先交付一个完整闭环，再扩充专业覆盖。

## 新增实验入口：原生结构变更校准

`structures-change-v1` 归 experimental，待本地 CalculiX 2.23 验收。它只检验
固定校准梁上的原生执行、原始证据复查与变更传播。未加入pilot、未成为通用支架
设计任务、没有隐藏迁移结论，也不修改旧结构pack的真值与评分。
详见 [本地接手规格](native-calibration-handoff.md)。
