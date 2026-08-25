# cad_geometry 维 2D 草图子轴落地：cadbench_seldon.sketch_lite（2026-08-25）

> 窄路 A 落地：Seldon CADBench-Hard 5 道 proc 草图题（CC-BY-4.0）按本仓库协议改编
> + 自建同族 10 题 = 15 题，当日完成全链（改编协议 → 判分模式 → gold 自检 →
> 双向自检 → 固定对基线）。registry 20→**21 integrated**，任务 2424→**2439**。

## 1. 改编协议（GUI → 脚本制）

| 项 | 原任务（Seldon） | 本改编 |
| --- | --- | --- |
| 作答 | 人在 Fusion GUI 操作（禁脚本/API） | 模型写 cadquery 脚本 |
| 产物 | Fusion 文档 | `sketch.step`（边复合体） |
| GT | answer.f3d（私有格式，不可解析） | **题面几何规格**（题面明示拟合点/顶点 authoritative） |
| 判分 | Seldon verifier（私有） | 本地实体级比对（design_artifact `sketch_2d` 模式） |

平面映射：YZ → (0,u,v) 法向 +X；XZ → (u,0,v) 法向 -Y（题面明示 origin 平面）。

## 2. 判分管线（sketch_2d，新增于 design_artifact）

- **gate**：静态检查 → 双跑可执行 → sketch.step 存在 → STEP 可解析出边且共面
  （SVD 法向对齐 ≤0.01mm）→ 双跑实体集规范化串一致；
- **physics** = 实体级匹配：线段端点无序对齐（表示无关，B 样条表示另验共线偏差）；
  样条端点对齐 + 全部拟合点在曲线上（0.01mm）；分数 = (命中−多余)/GT 数；
- **requirements** = 实体数精确 + 闭合环数精确（端点聚类→图分量全 2 度）+ 平面规格。

## 3. 自检与基线

| provider | 均分 | 满分 | gate | 备注 |
| --- | --- | --- | --- | --- |
| stub | 0.0 | — | 0/15 | missing_output 地板 |
| oracle | **1.0000** | 15/15 | 15/15 | gold 全链 15/15 PASS + runner 级满分（含双跑确定性） |
| minimax-m3 | **1.0000** | 15/15 | 15/15 | 满分——**饱和锚**（题面坐标全给时的可达域上限，同 gtm-v1 语义） |
| glm-5.3 | **0.8667** | 13/15 | 13/15 | 2 code_not_executable |

族级：chain 两家全满（5/5）；polygon M3 1.0 / GLM 0.75；spline M3 1.0 / GLM 0.83。

GLM 两败根因（真实能力信号，非判分器问题）：自检断言用幻觉 cadquery API——
`Edge.Vertexes`（应为 `Vertices`）、`Vector.distance()`（不存在）——脚本在**自己的
验证代码**里崩溃，与 pycycle 幻觉 API 同类：「写得出几何，写不对 API」。

## 4. 读数

1. **2D 草图（坐标全给）是高可达域**：M3 全满 → 按锚点纪律标 saturation anchor
   不参与模型排序；区分度来自 API 幻觉（GLM）与后续加难的约束/圆弧/构图题；
2. **改编保真**：改编 5 题 gold 全链 PASS 即题面规格 → cadquery 构造 → 判分闭环
   自证（answer.f3d 侧交叉核验待 Fusion 跑导出脚本后补充，非判分依赖）；
3. **cad_geometry 维厚度 +1**：3D 参数化（cadgen 22 题）之外新增 2D 草图子轴
   （15 题），覆盖 2/4 在册（cadgen + sketch_lite integrated；openvsp paused、
   seldon.hard proposed）。

## 5. 产物清单

```
runners/design_artifact.py   sketch_2d 判分模式（实体级匹配/闭合环/平面；cadgen solid 回归无恙）
runners/gen_tasks_cbsk.py    生成器（15 题定义+gold+内嵌全链自检）
tasks/cadbench_seldon.sketch_lite/        15 yaml + 15 md
data/cadbench-seldon/sketch_lite/         gold/ 15 脚本 + PROVENANCE.md
results/cadbench_seldon.sketch_lite/2026-08-25/  {stub,oracle,minimax-m3,glm-5.3}
registry/registry.yaml       sketch_lite integrated（21/42）；seldon.hard 保持 proposed（窄路 B）
```
