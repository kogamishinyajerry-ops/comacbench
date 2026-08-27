# 办公第二板三线落地（2026-08-26）

> 调研 §5 第二批三线同日落地：A 数据锚定文档 / B 条款结构化抽取 / C SpreadsheetBench
> 精选。registry 22→**25 integrated**，任务 2458→**2513**。office_productivity 维
> 四基准在册（engtable/awdoc/awext/ssb）。

## 1. 三线协议与自检

| 线 | 任务 | 判分 | oracle | stub |
| --- | --- | --- | --- | --- |
| A awdoc.office_docs | 18（docx×9/pptx×9） | doc_document：锚定数字命中（源数据派生统计，0.5%）+结构契约+双跑一致 | **18/18 满分** | 0 地板 |
| B awext.clause_extract | 12（自建条款风格卡） | json_extract：9 字段级（数值 2%；列表排序 casefold） | **12/12 满分** | 0.0（空 JSON 可解析地板） |
| C spreadsheetbench.verified_subset | 25（外部 CC-BY-SA-4.0） | formula_cell：soffice 重算→answer 区域 vs golden | **25/25 满分**（含 soffice 链） | 0 地板 |

## 2. 固定对基线（seed=0）

| 基准 | minimax-m3 | glm-5.3 | 读数 |
| --- | --- | --- | --- |
| awdoc | 0.6667（gate 12/18：6 code_not_executable） | **0.9444**（17/18 满分，1 脚本崩） | docx/pptx 构造是高可达域；M3 的 pptx API 使用弱（6 题脚本级失败） |
| awext | 0.8704（1/12 满分） | **0.9074**（2/12 满分） |
  > 勘误（2026-08-26 P1 期间）：M1 exact_keys 修复后同口径重跑——M3 **0.8889**（2/12）/ GLM **0.9074**（2/12），见 results/awext.clause_extract/2026-08-26/ | 字段级区分带：clause_no（§1.23 格式）/family 是主要失分——verbatim 复制纪律 |
| ssb | **0.1600**（1/25 满分，gate 7/25：17 code_not_executable） | **0.3069**（5/25 满分，gate 10/25：14 code_not_executable） | 深水区确认：真实表格加工远难于自建 engtable（0.95/0.99）——sheet 级重构非公式书写是瓶颈 |

## 3. C 线筛选事实（如实）

- verified_400 中 **Cell-Level 275 题全部无 answer 定位**（上游判分靠其 LLM
  validator——违反本仓库判分纪律，不引入）→ 全部出局；
- Sheet-Level 125 题中 107 过「golden 可读+区域可解析+含静态值」筛，取 25。

## 4. 判分器与工程记录（本板四条）

1. **answer 区域 extra 惩罚误杀**（SSB）：init 既有数据被当多余扣分（455_35
   误记 9.3 万 extra）→ 修正为区域内不罚（命中+mismatch 语义）；
2. **oracle 脚本可执行性**：repr(datetime) 不可执行+巨长单行 → JSON 字面量
   分行+日期结构化往返；
3. **providers json_extract 全链补齐**（system prompt/accept/oracle/stub）——
   首跑 M3 12 题 crash 暴露，修复后两模型重跑；
4. **qa_grounded summary 分派**：json_extract 型结果走专用汇总（字段命中率表）；
5. **shutil 黑名单与任务需求冲突**（SSB）：21 例「复制 init 工作簿」被误判
   sandbox_escape——黑名单前提「模型代码无需文件批量操作」对该任务族不成立；
   修正为任务 YAML 声明 `filesystem-copy` 时放行（sandbox.static_check 增参），
   全量重跑（旧口径结果废弃）。教训同 foam os.chmod：环境假设变更须复核黑名单；
6. **head 管道 SIGPIPE 吞跑**：`... | head -1` 使 python 在尾部 print 触发
   BrokenPipe 中途死亡且退出码伪装成功——GLM 首跑只落 19/25、6 题旧口径残留；
   修正：后台跑批一律重定向文件，禁止 head 管道截断。

## 5. 边界与后续

- awdoc 不评文风（LLM judge 违纪律）——锚定数字+结构是「数据一致性」核心；
- awext 条款卡为参数化合成（本会话 civair-kb 端点不返回内容，如实降级；KB
  恢复后按 doc_id 重锚真实条款）；
- ssb 判分依赖 LibreOffice headless（内网移植需带 soffice，env-matrix 已标）；
- 后续：ssb 失败模式族级画像与 H2 脚手架（openpyxl 保格式改写工作流）候选、
  awdoc M3 pptx 弱点复核。

## 6. 产物清单

```
runners/gen_tasks_office2.py            三线生成器（幂等）
runners/design_artifact.py              +doc_document/+formula_cell 两模式
runners/qa_grounded.py                  +json_extract 层与专用 summary
runners/providers.py                    +json_extract 全链（system/accept/oracle/stub）
tasks/{awdoc.office_docs,awext.clause_extract,spreadsheetbench.verified_subset}/
data/{awdoc,awext,spreadsheetbench}/    inputs+gold+PROVENANCE
results/*/2026-08-26/                   {stub,oracle,minimax-m3,glm-5.3}
registry/registry.yaml                  25/46 integrated
```
