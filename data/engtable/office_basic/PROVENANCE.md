# PROVENANCE — engtable.office_basic（工程表格加工族，office_productivity 维首批）

> 创建：2026-08-25（用户裁决：自建工程表格加工族先行）。生成器
> `runners/gen_tasks_engtable.py`（幂等）；判分 = `runners/design_artifact.py`
> `xlsx_table` 模式。同 calculix/sketch_lite DNA：自建参数化、判分 100% 本地复现、
> 无 LLM judge、无 GUI、无外部数据——内网可移植（仅依赖 openpyxl）。

## 1. 任务协议

- **输入**：cwd 下的 CSV（题面给定文件名，sha256 锁定注入隔离目录）；
- **输出**：`output.xlsx`（openpyxl 静态值；契约明示禁公式——data_only 读取下
  公式单元格读为 None 即失分，题面 CONTRACT 段如实声明）；
- **判分**：gold 非空单元格命中（数值 0.5% 相对容差 + 3 位小数契约；字符串精确）
  − 多余单元格惩罚；requirements = 结构契约（sheet 名集/表头行精确）；
- **gate**：静态检查 → 双跑可执行 → output.xlsx 存在可解析 → 双跑单元格集一致。

## 2. 任务族（5 族 19 题）

| 族 | 题数 | 变换 | 工程画像 |
| --- | --- | --- | --- |
| bom | 4 | 杂乱 BOM（重复件号跨行/干扰列）→ 规范 BOM（排序+合并数量） | 配套清点 |
| pivot | 4 | 长表（构型×通道×重复测量）→ 宽表汇总（mean/max 按规格） | 试验数据汇总 |
| si | 4 | 混合单位（lbf/in/°F）→ SI 规范表（固定系数 round 3） | 报告规范化 |
| flag | 3 | 时序测量 → 状态列（OK/OVER/MISSING，含缺失语义）+ STATS 摘要 sheet | 越限筛查 |
| exceed | 4 | 时序载荷 → 阈值过滤 + 降序 top-K 事件清单 | 载荷谱筛选 |

输入数据全部参数化确定性生成（航空试验数据风格：构型/通道/载荷/时序），
无外部数据依赖。

## 3. 自检记录（2026-08-25）

- gold 全链自检（生成器内嵌，判分管线对 gold 实跑）：**19/19 PASS**
  （physics=1.0、结构契约全中；flag 族 120-162 单元格最大）；
- runner 级：stub 19/19 地板 / oracle **19/19 满分 mean=1.0000**（双跑确定性含）。

## 4. 工程记录（当日踩坑）

- **资产注入名不匹配**：首版题面/gold 写死 `input.csv`，而沙箱按仓库 basename
  （`eng_bom_01.csv`）注入——oracle 0/19 暴露（stub 不读文件故先未显形）；
  修正为题面/gold/注入统一用真实文件名，无隐藏别名；
- **OCP 惰性加载**：design_artifact 顶部硬 import OCP 使 xlsx 任务无法在 .venv
  （无 OCP）运行——改为 try/except + solid/sketch 路径显式守卫；
  rerun 命令的解释器从硬编码 .venv-cad 改为 sys.executable（manifest 如实记录）。

## 5. 已知边界与后续

- 判分只读值不看格式（颜色/加粗/列宽不计）——契约明示，办公格式学属后续扩展；
- 数值容差 0.5% + 3 位小数契约双保险：换算系数给足 13 位有效数字，round 3 后
  任何实现路径偏差 < 0.001；
- flag 族「空单元格保持空」语义（openpyxl None）已在契约中显式定义（写 0/空串
  均判失分）；
- 后续扩容方向：多 sheet 跨表引用、透视两级分组、异常行剔除规则、日期/文本
  规范化、xlsx 公式族（引入 LibreOffice headless 重算，dev 已备）。

## 6. 复现

```bash
.venv/bin/python -m runners.gen_tasks_engtable    # 生成+gold 自检（19/19）
.venv/bin/python -m runners.design_artifact \
    --tasks tasks/engtable.office_basic \
    --out results/engtable.office_basic/<date>/<provider> \
    --provider <stub|oracle|minimax|glm> [--model glm-5.3] --seed 0
```
