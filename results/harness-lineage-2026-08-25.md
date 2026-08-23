# Harness 谱系化报告（v0.3 §8，2026-08-25）

> 三向推进：(1) 脚手架谱系化铺开（gtm-hard / cadgen）；(2) foam 物理层 v2；
> (3) 臂自动路由生产化。固定模型对 {minimax-m3, glm-5.3} 不变；证据全部为
> 2026-08-25 实测臂（同子集口径见各节）。

## 1. 谱系化增益总表（H0 → 最优臂）

| 基准 | 模型 | H0 | 最优臂 | 最优分 | 主靶族变化 | 判定 |
| --- | --- | --- | --- | --- | --- | --- |
| cadgen（22 全量） | M3 | 0.7083 | H3 | **0.9792** | lbracket 0.25→**0.771** | ✅ 命中（≥0.75 线） |
| cadgen（22 全量） | glm-5.3 | 0.8636 | H2 | **1.0000**（22/22 满分） | lbracket 已 1.0，全面满分 | ✅ 满分 |
| gtm-hard（sub10） | M3 | 0.6500 | H2/H3 | **0.8000** | margin 0.833→**1.0**；id 0.25→**0.50** | ✅ 双靶命中 |
| gtm-hard（sub10） | glm-5.3 | 0.5250 | H2/H3 | **0.6000** | margin 0.75→**1.0**；id 0（长度墙） | ✅ margin 命中 |
| pycycle（sub10） | M3 | 0.0 | H2 | 1.0000（v0.3 已录） | — | ✅（历史） |
| foam（sub10） | M3 | 0.0 | H2v2c | **0.40**（gate 8+/10） | 结构层打开；**physics 仍 0** | ⚠️ 部分达成（见 §3） |

谱系化成功率：**4/5 基准完全命中**（pycycle/cadgen×2/gtm-hard×2 族）。

## 2. 两条模型级边界发现（scaffold 的能力边界，非缺陷）

1. **glm-5.3 的 provider 长度墙**（gtm-hard id 辨识族）：32768 token 被长思考
   耗尽，134KB 数据矩阵输出写到一半 `finish_reason: length` 截断——脚手架
   无法治模型输出带宽，H3 反馈轮同样无效（rounds 烧满）。id 族 0.0 是
   **模型/协议边界**，与 M3（0.50，跨过门槛）形成对照。
2. **M3 的输出转写脆弱性**（foam v2 / gtm id 残留）：嵌套 f-string 三引号
   抄写三连语法错（v2.1 改字符串拼接 helper 后消除）、数据矩阵列写半截。
   残留失败从「知识缺失」变为「转写带宽」——harness 已把知识给足。

## 3. foam 物理层的诚实边界（方向 2 未竟事项）

- **v2 迭代史**（全部 docker 实证定稿）：v2（gauge p / U 微扰 / endTime 全量）
  → v2.1（字段头字符串拼接）→ v2.2（2D 网格纪律：Z 向恒 1 段，总格 ≤5000
  防 qemu 900s 超时——v2 初版「薄方向 8-10 段」自造的超时坑）→ v2.3（GT
  原文稳定方案：linearUpwind + nCorrectors 2 + e/h 双保险）→ v2.4（闭合胞
  拓扑：floor/ceiling/sideWalls 全墙，无 inlet/outlet）。
- **结果**：结构层完全打开（M3 v2c gate 8+/10，此前 0）；但 **NMSE physics
  仍 0**——模型产出与我的 scaffold 验证算例（GT 同构配置）在 qemu docker 下
  均数值发散（末态场 NaN；判分器按无公共场记 0）。GT 的稳定性是其全套配置
  （90×10 网格 / 1000s / 精确参数组）的乘积效应，逐项对齐后仍有未定位差异。
- **读数**：foam 是谱系化的**硬边界样本**——「能跑起来」可注入（结构知识），
  「物理保真」不是 prompt 知识能完全注入的（数值稳定性=配置×求解器×硬件）。
  下一步若继续：逐项二分 GT 与 scaffold 算例的配置差（每项单独消融）定位
  发散源，工作量一个会话。

## 4. 臂自动路由（方向 3，生产化落地）

`runners/arm_router.py`：策略表 (模型家族×基准)→最优臂+可执行命令行，
证据分固化自 v0.3 矩阵+本轮谱系化；H1（反馈单独）四组合全零已入「不推荐」；
未知组合回退 H3（安全上界）。演示：
`python3 -m runners.arm_router --provider minimax --benchmark cadgen.local_validity`
→ H3（证据 0.9792）。内网生产接入：新模型按行为归类（遵循型/改写型）入表
即可获得臂调度。

## 5. 设计原则沉淀（本轮新增两条，入 scaffold 范式）

- **防抄写歧义**：示例代码禁用嵌套 f-string 三引号（M3 高频抄错点），一律
  字符串拼接 helper；
- **数据转写显式化**：题面「数据已给」必须 ⚠️ 声明「需在脚本内原样转写」
  （gtm id 初稿暴露的误读：模型以为 X/u 是预置变量）。

## 6. 产物清单

- scaffolds：`data/{cadgen,gtm.transport_control_hard}/.../scaffold.md`（本轮）
  + `data/cfdllm/foam_basic/scaffold_v2.md`（v2→v2.4 迭代定稿）+ 既有 pycycle
- 臂数据：`results/{cadgen.local_validity,gtm.transport_control_hard,
  cfdllm.foam_basic}/2026-08-25/`（manifest 含 harness_arm/scaffold）
- `runners/design_artifact.py` 臂接线（--scaffold/--iterate/--limit，回归验证）
- `runners/arm_router.py`（策略表路由器）
