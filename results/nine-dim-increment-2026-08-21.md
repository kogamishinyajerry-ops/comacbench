# v0.1 三线补强增量报告（2026-08-21，接 nine-dim-baseline-2026-08-19.md）

> 基线模型：glm-4v-flash（mechvqa 多模态）/ MiniMax-M3（其余），seed=0。
> 本轮三线：mechvqa 多模态翻盘、cadgen CAD 维解零、pycycle/aviary 补厚。
> 分数仅导航用（scoring/README.md §1）；gate 失败率与原因分布优先于均分。

## 0. 本轮总览

| 线 | 基准 | 任务 | stub | oracle | 真实基线 | registry |
| --- | --- | --- | --- | --- | --- | --- |
| 多模态 | mechvqa.public_eval | 180（新建） | 0.0692 | **1.0×180** | glm-4v-flash **0.3504**（满分率 20.6%） | staged→integrated |
| CAD 维 | cadgen.local_validity | 22（新建） | 0.0×22 | **1.0×22** | minimax-m3 **0.7083**（满分 15/22） | proposed→integrated |
| 动力补厚 | pycycle.engine_cycle | 7→**28** | 0.0×28 | **1.0×28** | minimax-m3 **0.0393**（gate 2/28） | integrated（扩容） |
| 总体补厚 | aviary.transport_mission | 8→**27** | 0.0×27 | **1.0×27** | minimax-m3 **0.2222**（gate 6/27） | integrated（扩容） |

integrated 基准 15→**17**，任务总量 2119→**2376**。

## 1. mechvqa.public_eval（多模态，knowledge 维 +1）

- **通道**：providers 新增 `glmvl` 预设（bigmodel paas v4 多模态 image_url）；`glm-4v-flash`
  免费档实测可用（max_tokens 上限 1024）。GLM-4.6V/4.5V 为有效模型名但账户欠费（1113），
  充值后 `--model glm-4.6v` 覆写即升级，不改代码。MiniMax 端点无 VL 模型（2013）、
  Gemini key 区域封锁——**VLM 单通道为环境事实**。
- **判分**：`free_vqa`（中文感知归一化精确 → 数值集容差 → ASCII 词+CJK 单字混合 token F1）；
  纯文本 preset 收到图像任务直接拒绝（multimodal_only 准入纪律）。
- **任务集**：1117 行 qualityscore==1.0 池，capability×difficulty 九格最大余数法抽 180 题
  （seed 20260821，`runners/gen_tasks_mechvqa.py`，逐图 sha256 锁定）。
- **glm-4v-flash 画像**（均分 0.3504）：

| capability | Easy | Medium | Hard |
| --- | --- | --- | --- |
| Recognition | **0.486** (68) | 0.281 (27) | 0.232 (3) |
| Reasoning | 0.219 (10) | 0.272 (17) | 0.240 (15) |
| Judging | 0.389 (13) | 0.277 (19) | **0.127** (8) |

  识别易题最强、判断难题最弱——免费档 VLM「看得见、判不稳」。stub 5 题撞满分
  （样板数字集恰为参考答案数字集超集，grader 既有语义，见 PROVENANCE）。

## 2. cadgen.local_validity（cad_geometry 维 0→1）

- **adapter**：design_artifact 首次接线（`runners/design_artifact.py`）。五 gate：
  脚本可执行 → part.step 存在 → STEP 可解析+BRepCheck 有效+体积>0 → 双执行复现一致
  （1e-6）；physics=体积/包围盒三边相对误差（1%）；requirements=圆柱面孔数/半径接口检查。
- **任务集**：自建参数化 6 族 22 题（法兰/矩形板/L 角支架/套筒/阶梯轴/凸台底板），
  100% 本地可复现判分（不镜像 ODC-BY 输入、不用 CADGenBench 私有 GT），gold 全量预计算。
- **minimax-m3 画像**：均分 0.7083、满分 15/22、gate 16/22（5 code_not_executable +
  1 invalid_geometry）。L 角支架族全灭（多特征定位困难），法兰/板/凸台族几乎全满——
  **「会写参数化 CAD 脚本」与「会写 pycycle 脚本」（0.04）形成鲜明画像分化**。
- **负路径**：nondeterministic_artifact 3/3 命中。方法论教训：本机 time_ns() 毫秒粒度，
  `%N` 假随机代码实为确定代码——验证非确定性须用 pid 差异源（PROVENANCE 已记）。

## 3. pycycle.engine_cycle 7→28（propulsion 补厚）

- 新增 21 题：设计点网格（fn 10-16k × t4 2300-2900 × opr 11-17 域内 10 组）、
  T4/OPR 扫描敏感性、多组油耗比、修复题变体。gold 全量重算锁定。
- **存量 gold 修复**：内嵌旧仓库绝对路径（仓库搬迁致 oracle 必挂）→ __file__ 锚定重写，
  等效验证 7/7（max rel 1.5e-10，对 references）。
- **minimax-m3 画像**：均分 0.0393、gate 2/28（25 code_not_executable + 1 missing_output）。
  与旧 7 题 0/7 一致且更厚：**M3 基本写不出可执行 pycycle 脚本（幻觉 API），扩题不改结论**；
  2 题过 gate 但物理值近零（mean 0.039）。

## 4. aviary.transport_mission 8→27（mdo_design 补厚）

- 新增 19 题：任务分析网格（range×mach 10 组）、总重权衡加点、燃油比、航程扫描、修复题。
- 存量 gold 同样修复 + 等效验证 8/8（0.0 偏差）。解释器迁移 `.venv-aviary`
  （aviary 1.0.1+openmdao 3.45 栈；pyvista import 走 runners/vendor_shim，NMSE 判分仍在 .venv）。
- **minimax-m3 画像**：均分 0.2222、gate 6/27（20 code_not_executable + 1 越界尝试 + 6 过）。
  过 gate 即高分的旧观察保持（6 过 gate 中 6 满分）——**MDO 脚本门槛在「写得出可执行
  Aviary 脚本」，写得出就基本做对**。

## 5. 九维覆盖变化（vs 2026-08-19）

| # | 维度 | 2026-08-19 | 2026-08-21 | 增量 |
| --- | --- | --- | --- | --- |
| 1 | knowledge | 2/4 在册（0.50） | 3/4（0.75） | +mechvqa（多模态首个落地面） |
| 3 | cad_geometry | **0.00** | **0.50**（1/2 在册） | +cadgen；openvsp 仍 paused |
| 6 | propulsion | 1/1 但 7 题（薄） | 1/1 厚证据（28 题） | 样本 ×4，结论不变 |
| 8 | mdo_design | 1/3 且 8 题（薄） | 1/3 厚证据（27 题） | 样本 ×3.4，结论不变 |
| — | 多模态评测轴 | 0.05 | **0.55** | VLM 通道+判分+基线全链落地（单通道） |
| — | Adapter 覆盖轴 | 0.80（4/5 类） | **1.00**（5/5 类接线） | design_artifact 首接线 |

结构/飞控两维仍为零（simjeb/gtm 等商业栈 blocked-env，待内网环境）。

## 6. 环境与复现口径

- 三 venv：`.venv`（om-pycycle 钉子栈，不变）/ `.venv-aviary`（aviary 1.0.1+openmdao 3.45）
  / `.venv-cad`（cadquery 2.8.0+OCP）；plugin 已配路由。
- GLM 账户欠费（文本 glm-4.6 与 GLM-4.6V 均 1113）→ 本轮 GLM 系基线仅免费档
  glm-4v-flash；GLM 文本基线待充值后补跑（--resume 幂等）。
- 全部 run_manifest 含 seed/rerun_command/digest；gold 等效验证记录入 PROVENANCE。
