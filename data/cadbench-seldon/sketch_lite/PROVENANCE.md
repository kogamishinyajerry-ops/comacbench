# PROVENANCE — cadbench_seldon.sketch_lite（CADBench-Hard proc 草图题改编，窄路 A）

> 创建：2026-08-25（用户裁决路径 A）。改编源：Seldon CADBench-Hard 公开子集 5 道
> proc 草图题（`data/cadbench-seldon/hard/tasks/proc_*/`，CC-BY-4.0 镜像，sha256
> 与官方 manifest 一致）。生成器 `runners/gen_tasks_cbsk.py`（幂等）；判分 =
> `runners/design_artifact.py` 新增 `sketch_2d` 模式。

## 1. 改编协议（GUI → 本仓库脚本制）

| 项 | 原任务（Seldon） | 本改编 |
| --- | --- | --- |
| 作答方式 | 人在 Fusion GUI 操作（题面禁脚本/API） | 模型写单个 ```python（cadquery） |
| 起始态 | 空文档（proc 题不依赖种子） | 无状态脚本 |
| 产物 | Fusion 文档（环境自动导出） | `sketch.step`（cadquery 导出边复合体） |
| 判分 | Seldon verifier（私有） | 本地实体级比对（下 §3） |
| GT | answer.f3d（私有格式） | **题面几何规格**（一手源，"describe the required final geometry"） |

平面映射（题面明示 origin 平面）：YZ → 全局 (0,u,v) 法向 +X；XZ → (u,0,v) 法向 -Y。

## 2. 任务集（15 题 = 改编 5 + 自建 10）

- **改编 5**（CC-BY-4.0，几何规格取题面原文逐字）：chain_s01（4 段正交开链）、
  polygon_s01（正八边形 中心(-7,11) R24 首顶点 296°）、spline_s01/s02/s03
  （闭合轮廓，样条 4/4/6 拟合点 + 2 线段）；
- **自建 10**（同族参数化变体，GT 解析计算）：chain×3（3/5/6/7 段）、polygon×3
  （正五/六/十二边形，各异中心半径朝向）、spline×3（5/6/7 拟合点）。
- 改编题 license_provenance 标 `confirmed-adapted-ccby4`（CC-BY-4.0 Seldon
  Technologies 署名衍生，协议变更如实标注）；自建题 `confirmed-selfbuilt`。

## 3. 判分口径（design_artifact sketch_2d 模式）

- **gate**（顺序短路）：静态检查 → 双跑可执行 → sketch.step 存在 → STEP 可解析出边
  且共面（法向对齐规格，SVD 拟合最大偏差 ≤0.01mm）→ 双跑实体集规范化串一致
  （nondeterministic_artifact）；
- **physics** = 实体级匹配：线段端点无序对齐（0.01mm）；非 line 表示另验共线偏差
  （表示无关，STEP 往返线↔B样条）；样条=端点对齐且全部拟合点在模型曲线上
  （0.01mm）；分数 = (命中数 − 多余实体数) / GT 实体数（下限 0）；
- **requirements** = n_entities 精确 + n_closed_profiles 精确（端点聚类成顶点、
  边建图、分量内全 2 度 ⇔ 闭合环）+ 平面规格；
- oracle_source = gold cadquery 脚本（题面几何直接转写）。

## 4. 自检记录（2026-08-25）

- **gold 全链自检**（gen_tasks_cbsk 内嵌）：15/15 PASS——gold 实跑 sketch.step 经
  判分管线 physics=1.0、实体数/闭合环/平面全中；
- **runner 级**：stub 15/15 地板（missing_output）/ oracle **15/15 满分 mean=1.0000**
  （含双跑确定性）——判分管线双向验证。

## 5. 工程记录（当日踩坑）

- **闭合环计数初版全错**：把「端点重合簇」误当图分量（三角形 3 顶点簇各自计数，
  判 n_v==n_e 恒假）——重构为两阶段（端点聚类→按边建图分量→全 2 度判环）后
  开链=0/闭合=1 全部正确；
- **样条拟合点映射**：`map_fn(*u, *v)` 对标量对误用双解包——修正 `map_fn(*pt)`；
- **physics 全 1.0 但 closed 全错**的自检暴露模式：gold 自检是判分器的判分器，
  每次修改判分逻辑必须重跑（生成器内嵌保证）。

## 6. 已知边界与后续

- 拟合样条判「点在曲线上」（0.01mm）而非形状全等——cadquery makeSpline 与
  Fusion 默认拟合样条形状有差，改编口径只锚定题面声明的拟合点与端点
  （题面原文即以拟合点列表为 authoritative），如实声明；
- answer.f3d 侧交叉核验：待 Fusion 跑 `tools/fusion_export_gt.py` 导出
  sketch_gt/*.json 后比对（非判分依赖，5 题样条形状差将在此量化）；
- 规模 15 题为 cad_geometry 维 2D 草图子轴首批；后续可加圆弧/构造几何/约束题扩容。

## 7. 复现

```bash
.venv-cad/bin/python -m runners.gen_tasks_cbsk      # 生成+gold 自检（15/15）
.venv-cad/bin/python -m runners.design_artifact \
    --tasks tasks/cadbench_seldon.sketch_lite \
    --out results/cadbench_seldon.sketch_lite/<date>/<provider> \
    --provider <stub|oracle|minimax|glm> [--model glm-5.3] --seed 0
```
