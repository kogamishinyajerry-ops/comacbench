# 结构仿真契约 v2：可连接的载荷与可检查的悬臂梁

目标：让旧样本中已确认的 8 个悬空受载节点在求解前失败，并逐项核验现有梁题的网格、材料、固定端、均分载荷与输出要求。

## 范围与实现次序

1. 在公共 `simulation_agent.run_task` 入口复现历史错误未被有效性门拦截。
2. 新增可选 `grader.deck_contract`，profile 为 `ccx.cantilever.v1`。只覆盖轴对齐、共节点、完整结构化 C3D20 长方体、单一线性静力步。未知关键字/选项明确反馈不支持，不静默跳过。
3. 新建 `packs/aviation-structures-v2`，保留 v1 的文件、参考数值和结果。声明几何、最小网格、材料和合载荷；题面明确支持范围。
4. 贡献预检检查该契约及输出抽取的一致性；运行报告展示逐项检查、错误位置和修复建议，保留生成输入、求解日志与 dat 原文和摘要。
5. 参考实现及单一故障负例校准；两个冻结模型答案离线回放；适当回归与历史证据摘要校验。

## 验收

- `.venv/bin/python -m unittest discover -s tests -v` 全部通过，包括两个历史模型拦截、有效模型通过、网格/连接/材料/边界/载荷/输出/不支持语法负例。
- `.venv/bin/python -m comacbench validate packs/aviation-structures-v2` 退出 0；缺失/畸形/矛盾契约退出 2，反馈字段可定位。
- 新包 `calibrate` 退出 0，参考分数 1、故障负例全为预期失败；使用原生 CalculiX。
- 新身份回放的两个旧答案 gate=0、score=0，`unconnected_loaded_nodes` 各为 8，未启动求解器；原始 live 成绩保持不变。
- 新结果能复核 deck、dat、求解日志摘要与完整文本；新报告实际浏览检查。
- 本轮修改前记录的 `report/2026-09-06-structures-v2/prior-artifacts.json` 全部摘要不变。

## 工程边界

这是一种明确支持范围的输入契约审查，不是通用 CalculiX 解析器、连续体模型验证或飞机结构接受。单位来自公开题面和显式量纲字段，无法从无单位数字自动推断。参考值、5% 数值容差和均分节点力的原题语义保留；均分节点集中力并不声明为均匀面力。

语法依据：[CalculiX 2.23 官方手册](https://www.dhondt.de/ccx_2.23.pdf)，C3D20、NSET/ELSET、CLOAD、BOUNDARY、SOLID SECTION 章节。同一步内重复 CLOAD 累加；集合只引用已定义集合；不支持幅值、坐标变换、接触、多步或 include。
