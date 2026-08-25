# office_productivity 维落地：engtable.office_basic（2026-08-25）

> 调研（report/2026-08-25-office-benchmark-survey.md）首选项 2 落地：自建工程表格
> 加工族。同 calculix/sketch_lite DNA 当日闭环：生成器 → gold 自检 → 双向自检 →
> 固定对基线。registry 21→**22 integrated**，任务 2439→**2458**。
> **九维 → 十维**：新增 office_productivity（工程办公生产力）。

## 1. 协议与判分

- 输入：CSV（sha256 锁定注入沙箱）；输出：`output.xlsx`（openpyxl 静态值，
  契约禁公式——data_only 读取下公式=None 即失分）；
- physics = gold 非空单元格命中（数值 0.5% 相对容差 + 3 位小数契约；数字文本
  双向强转）− 多余单元格惩罚；requirements = 结构契约（sheet 名集/表头精确）；
- gate：静态检查 → 双跑可执行 → 工作簿可解析 → 双跑单元格集一致；
- 100% 本地复现（仅 openpyxl，无 LLM judge/GUI/外部数据）——内网可移植。

## 2. 任务族（5 族 19 题）

| 族 | 题数 | 变换 | 画像 |
| --- | --- | --- | --- |
| bom | 4 | 重复件号合并+排序 → 规范 BOM | 配套清点 |
| pivot | 4 | 长表（构型×通道×重复测量）→ mean/max 透视 | 试验汇总 |
| si | 4 | lbf/in/°F → SI（13 位系数，round 3） | 报告规范化 |
| flag | 3 | 越限状态列（OK/OVER/MISSING）+ STATS 摘要 | 越限筛查 |
| exceed | 4 | 阈值过滤 + 降序 top-K 清单 | 载荷谱筛选 |

## 3. 自检与基线（判分器修正后全量重跑口径）

| provider | 均分 | 满分 | gate | 备注 |
| --- | --- | --- | --- | --- |
| stub | 0.0 | — | 0/19 | missing_output 地板 |
| oracle | **1.0000** | 19/19 | 19/19 | gold 全链 19/19 PASS |
| minimax-m3 | **0.9474** | 18/19 | 18/19 | eng_flag_01 code_not_executable（API 非确定性：前一轮同题通过，本轮脚本崩溃——thinking 模型 temp=0 仍非逐题确定，既往口径） |
| glm-5.3 | **0.9903** | 18/19 | 19/19 | eng_flag_01 列错位（C/D/F 列整体右移一格，77/120 命中）——真实语义错误 |

族级：bom/pivot/si/exceed 四族两家全满（14 题）；**flag 族是唯一区分带**
（缺失语义 + 三状态判定 + 双 sheet 联动）。

## 4. 判分器修正记录（本轮核心工程事实）

- **初版双跑**：M3 19/19 饱和 / GLM 0.981——GLM flag 族失分集中于
  `DATA!B2 got='10000' ref='10000.0'`：模型把 CSV 串原样写入（文本数字），
  初版判分器类型敏感判 mismatch。裁定：**值内容是契约，存储类型不是**——
  `_xlsx_numlike` 双向强转后重跑全部 provider（旧结果整体废弃，不混口径）；
- **资产注入名 bug**（首版）：题面写 `input.csv`、沙箱按仓库 basename 注入
  → oracle 0/19 当场暴露（stub 不读文件故先未显形）——统一真实文件名修复；
- 附带工程：OCP 惰性加载（xlsx 模式跑 .venv 无需 cadquery）；rerun 命令
  解释器改 sys.executable。

## 5. 读数

1. **基础表格加工是两家高可达域**（0.95/0.99）：bom/pivot/si/exceed 全满——
   与 gtm-v1/sketch_lite 同类「可达域锚点」，锚点纪律适用（不参与模型排序）；
2. **flag 族保留区分度**：缺失语义（空≠0）+ 阈值边界 + 双 sheet 一致性是
   真实办公错误的浓缩（GLM 列错位即真实错误的典型形态）；
3. 加难路径明确：多 sheet 跨表引用、两级分组透视、异常行剔除、日期规范化、
   xlsx 公式族（LibreOffice headless 重算，dev 已备）。

## 6. 产物清单

```
runners/design_artifact.py        xlsx_table 模式（单元格级比对+结构契约；OCP 惰性化）
runners/gen_tasks_engtable.py     生成器（5 族参数化+gold+内嵌全链自检）
tasks/engtable.office_basic/      19 yaml + 19 md
data/engtable/office_basic/       inputs/ 19 csv + gold/ 19 py + gold_output/ 19 xlsx + PROVENANCE.md
results/engtable.office_basic/2026-08-25/  {stub,oracle,minimax-m3,glm-5.3}
registry/registry.yaml            engtable.office_basic integrated（22/43）
```
