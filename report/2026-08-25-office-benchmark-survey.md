# 日常办公类 Benchmark 调研（2026-08-25）

> 触发：用户裁决放弃 Fusion 手工通道，转向「日常办公」类高价值基准。
> 数据来源：HF/GitHub API 实测（web 搜索余额尽，API 直连）；判分纪律与 adapter 兼容性
> 按 `scoring/README.md` / `adapters/README.md` / `env-matrix.md` 评估。
> 本文是决策文件：§1 约束 → §2 空间映射 → §3 外部候选事实表 → §4 出局项 → §5 推荐组合。

## 1. 硬约束（从本次会话与项目历史导出）

1. **无 GUI 通道**（今日双实验证死）：macOS Fusion/AutoCAD 均无无头入口——
   一切「截图/computer-use/桌面自动化」类基准（OSWorld 系、OfficeBench-GUI、
   AgentCompany 桌面部分）在 dev 层不可执行；
2. **内网离线生产**：无 web——GAIA/WebArena 类浏览依赖基准出局；
3. **多模态单厂商**：截图 VQA 类（DocVQA/ChartQA/SlideVQA）外部效度不足，暂缓；
4. **判分纪律**：客观本地可复现、oracle/stub 双向自检、LLM judge 不替代判分——
   自由文本写作类（邮件/文风）不可评，只能评「结构化抽取/数字锚定」形态；
5. **许可**：NC 一票否决（CAMB/FinanceBench 先例）；SA 需同许可衍生策略
   （superwing 先例可处理）；干净 = CC-BY-4.0 / Apache-2.0 / MIT / self-built；
6. **民机院所真实办公画像**（价值锚点）：工程数据处理（Excel/CSV）、
   报告/汇报文档（Word/PPT）、长文档查证（标准/适航/技术报告）、
   跨语言（中英术语）、结构化清单（BOM/行动项/合规表）。

## 2. 空间映射：办公工作 → 可评测族（按 adapter 兼容性）

| 族 | 测什么 | adapter | 判分方式 | 可评性 |
| --- | --- | --- | --- | --- |
| **表格公式** | Excel 公式生成 | code_exec | 执行结果 vs gold（客观） | ✅ 高 |
| **工程数据加工** | 原始数据→规范表/BOM/透视 | design_artifact（xlsx 制品） | 单元格级比对 + 结构契约 | ✅ 高 |
| **数据查询** | text-to-SQL（工程库） | code_exec | sqlite 执行 vs gold 结果集 | ✅ 高 |
| **文档生成** | 数据→报告（docx/pptx） | design_artifact（文档制品） | 结构契约 + 数字与源数据一致（正则锚定） | ✅ 中高 |
| **长文档抽取** | 标准/条款→结构化清单/行动项 | qa_grounded | exact/F1 | ✅ 高 |
| **表格问答** | 表格→代码→答案 | code_exec | 数值 vs gold | ✅ 高 |
| **跨语言** | 航空中英互译 | qa_grounded | 术语命中+数字一致（BLEU 仅导航） | ⚠️ 中 |
| **自由写作** | 邮件/纪要成文 | — | 需 LLM judge | ❌ 违纪律 |
| **GUI 操作** | 桌面软件使用 | computer_use（未立项） | — | ❌ 无头通道 |

## 3. 外部候选事实表（2026-08-25 API 实测）

| 基准 | 许可（实测） | 规模/形态 | 判分 | 离线 | 初判 |
| --- | --- | --- | --- | --- | --- |
| **SpreadsheetBench**（KAKA22/HF） | CC-BY-SA-4.0 | 912 题，真实表格公式生成 | 执行比较（其 eval 依赖待核：LibreOffice headless 或公式引擎） | ✅（数据本地） | **可接**——SA 同 superwing 先例；公式执行引擎是集成工作量主体 |
| **TableBench** | Apache-2.0 | 表格 QA（代码式作答通道） | 数值 vs gold | ✅ | **可接**——code_exec 直吃；域相关性弱于工程表格 |
| **DABstep**（Adyen） | CC-BY-4.0 | 金融 PDF 多步数据分析 | 数值/结构 | ✅ | 许可干净；金融域与民机相关性弱，价值中等 |
| **DS-1000** | CC-BY-SA-4.0 | 数据科学代码生成（pandas/numpy） | 测试执行 | ✅ | 与 scicode/mbpp 重叠度高，边际价值低 |
| **FinanceBench** | **CC-BY-NC-4.0** | 金融文档 QA | — | — | ❌ NC 一票否决 |
| **BIRD**（birdsql） | gated（401，未卡可见；已知 NC 风险） | 12.7k text-to-SQL | sql 执行 | ✅ | ⚠️ 许可待核（NC 嫌疑）；gated 需账号 |
| **GAIA** | gated，license 未标（validation 已知 NC） | 通用 agent 问答 | — | ❌ 依赖 web | ❌ 双否 |
| **tau2-bench**（Sierra） | GitHub API 限流未核（社区记 MIT，待核） | API 工具调用+模拟用户（航空客服域！retail/airline） | 状态机判定 | ✅ | **高契合**（airline 场景+harness-first）但需新 agent_tool_use runner——**立项级**，周级 scope |

## 4. 出局项（原因存档）

- **GUI/computer-use 全家族**（OSWorld / WindowsAgentArena / OfficeBench-GUI /
  AgentCompany 桌面段）：dev 无无头通道（本日 Fusion/AutoCAD 双实验证死），
  computer_use adapter 未立项；
- **Web 依赖**（GAIA / WebArena / WorkArena / BrowseComp）：内网离线无浏览器农场；
- **截图 VQA**（DocVQA / ChartQA / SlideVQA / OfficeBench-VQA）：VLM 单厂商；
- **NC 许可**（FinanceBench；BIRD 嫌疑；CAMB 旧案）：法务口径一票否决；
- **自由写作**（邮件/纪要/文风）：唯一判分路径是 LLM judge——违反 scoring §3/§4；
- **会议纪要成文**：同上；仅「纪要→结构化行动项 JSON」形态可评（入 §2 抽取族）。

## 5. 推荐组合（价值 × 成本 × 环境可移植性）

**框架影响**：新增第十维 **office_productivity（工程办公生产力）**，九维→十维。

### 首批（本会话可落，全部复用既有 adapter）

1. **SpreadsheetBench 接入**（外部，表格公式维）：code_exec adapter；
   集成主工作量 = 公式执行引擎选型（LibreOffice headless `soffice --convert-to`
   是 mac 可行通道；内网移植风险如实标注——备选自建 openpyxl 判分子集）；
2. **工程表格加工族（自建，10-20 题）**：design_artifact 模式扩展（sketch_2d
   先例已证模式扩展成本低）：原始 CSV/杂表 → 规范 BOM/汇总表 xlsx，
   判分 = openpyxl 读回单元格级比对（纯 Python，内网可移植，100% 本地复现）；
   题源 = 自建参数化（气动/结构/动力试验数据风格）。

### 第二批（短会话级）

3. **数据锚定文档生成（自建）**：数据集+模板契约 → docx 报告/pptx 汇报；
   判分 = 结构契约（标题层级/表格/图注）+ 关键数字与源数据一致（正则锚定）；
4. **长文档结构化抽取（自建/联动）**：适航条款/技术标准 → 行动项/合规清单
   JSON（exact/F1）；题源可与 civair-kb 知识底座联动（防泄漏审查必须前置——
   知识库出题不得泄漏底座快照外内容）；
5. **TableBench 或 text-to-SQL 自建**（Apache-2.0 干净 / 或自建航空工程库
   schema+sqlite 判分）。

### 立项级（单独决策，不混入常规 batch）

6. **tau2-bench**（agent 工具调用，airline 域）：与 harness-first 范式最契合
   （测的就是工具编排工作流），但需第六类 agent_tool_use adapter + 模拟用户
   环境——周级 scope，建议在办公轴首批落地后再议。

### 排除重申

自由写作/GUI/Web/NC 四类不进入（§4 存档，防重复调研）。
