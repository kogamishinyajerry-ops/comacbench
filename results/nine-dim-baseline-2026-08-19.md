# v0.1 九维度基线报告（2026-08-19，基线模型 = MiniMax-M3，seed=0）

> 生成：M4 收官。运行环境 dev 终端（docker OpenFOAM v10 / venv aviary+pyvista）。
> **总分仅导航用，不用于决策**（scoring/README.md §1）；每维按基准独立报告，
> gate 失败率与原因分布优先于均分。GLM-4.6 为次要基线（共享端点 429 受限，见 §6）。

## 0. 导航总览（勿据此决策）

| # | 维度 | 构成基准 | M3 均分* | 状态 |
| --- | --- | --- | --- | --- |
| 1 | 航空知识与文档理解 knowledge | cfdquery、aeroengqa | **0.848** | ✅ 完整 |
| 2 | 科学编程 coding | scicode、cfdcode | **0.572** | ✅ 完整 |
| 3 | CAD/几何 cad_geometry | cadgen | — | ⏳ batch-2 |
| 4 | CFD cfd | superwing、foam_basic | **0.22** | ✅ 完整（foam 0/110 为真实能力边界） |
| 5 | 结构 structures | simjeb、engdesign | — | ⏳ batch-2 + engdesign blocked |
| 6 | 动力 propulsion | pycycle | — | ⏳ batch-2 |
| 7 | 飞控 flight_control | gtm | — | ⏳ batch-2 |
| 8 | 总体设计与 MDO mdo_design | aviary | **0.250** | ✅ 完整 |
| 9 | 鲁棒性与审计性 robustness_audit | 全部 robustness 子分 + 审计日志质量 | 见 §5 | ✅ 可部分评 |

\* 均分 = 维度内各基准任务均分的未加权平均（跨基准权重未定，仅导航）。

## 1. knowledge（航空知识 + 有据问答）

| 基准 | 任务 | gate 通过 | 均分 | 满分 |
| --- | --- | --- | --- | --- |
| cfdquery | 90 | 90/90（失败率 0%） | 0.8111 | 73 |
| aeroengqa.gold | 80 | 80/80（失败率 0%） | 0.8852 | 43 |

aeroengqa 四层画像（M3）：拒答正确率 87.5%、误拒 2.5%、证据支持 0.9375、捏造引用 0、
区分声明 100%——引用纪律强、事实作答（客观层 0.585 含 F1 部分分）是主要失分项。

## 2. coding（科学编程）

| 基准 | 任务 | gate 通过 | 均分 | gate 失败原因分布 |
| --- | --- | --- | --- | --- |
| scicode.physics | 52 | 42/52 | 0.6738 | code_not_executable×8, sandbox_escape×1, timeout×1 |
| cfdllm.cfdcode | 15 | 8/15 | 0.4700 | code_not_executable×4, non_physical×2, missing_output×1 |

scicode：42 过 gate 的题中 14 满分、28 部分分（physics 均值 0.54）。cfdcode：过 gate 8 题
物理层均值 0.937（会写代码即高精度），但 7/15 脚本不可执行/NaN。

## 3. cad_geometry —— ⏳ batch-2（cadgen.local_validity）

## 4. cfd（系数预测 + 仿真）

| 基准 | 任务 | gate 通过 | 均分 | 说明 |
| --- | --- | --- | --- | --- |
| superwing.coeff_lite | 100 | 100/100 | 0.4415 | physics 均值 0.080（几何外推）/0.044（内插）——**LLM 无法直接系数回归**（CL rel_err ~240%） |
| superwing（ML 参照） | 100 | 100/100 | 0.7525 | RandomForest(100)：**physics 内插 0.828 / 几何外推 0.485**——同一管线 ML vs LLM 差一个数量级（正例参照，`ml-superwing/`） |
| hilift_aeroml.lite | 100 | 100/100 | 0.4855 | physics 内插 0.186 / 几何外推 0.124；**CM rel_err 218-353%**（高升力俯仰力矩对 LLM 最难），与 superwing 互证 |
| hilift（ML 参照） | 100 | 100/100 | 0.904 | RandomForest(100)：**physics 内插 0.883 / 几何外推 0.821**（1410 训练行，36 保留构型全剔除）——正例参照，`ml-hilift/`（2026-08-20 补） |
| cfdllm.foam_basic | 110 | 0/110 | 0.000 | gate 全败：**87 code_not_executable + 23 simulation_failed**（脚本崩溃 / Allrun 用 `source` bashism 而非 POSIX `.`）——M3 写不出可运行 OpenFOAM 算例 |

> foam_basic 判分器已修：`os.chmod` 曾误列沙箱黑名单（33 例误判 sandbox_escape），移除后
> 重跑，最终诚实分布为 87+23，**无 sandbox_escape**。oracle 110/110 已证判分管线正确，
> 故 0/110 属被测能力真实边界。

## 5. robustness_audit（鲁棒性与审计）

- 各基准 robustness 子分：scicode 确定性两轮（过 gate 题中 8/10=1.0，2 题不一致）、
  cfdcode 确定性（8 过 gate 题 8/10=1.0）——均值的确定性良好，但**仅覆盖过 gate 子集**；
- 沙箱违规告警：scicode 1 例、foam_basic 15/28 例 sandbox_escape（模型尝试越界调用）——
  **robustness_audit 维度核心风险信号**；
- 审计日志：全部 result.json 落 `logs`/`grade_details` 中间量、run_manifest（seed/digest/
  重跑命令/git commit）——可追溯性达标；git 非仓库（git_commit=unknown）为已知缺口。

## 6. 基线模型覆盖与复现性

| 模型 | 完整基准 | 受限基准 | 原因 |
| --- | --- | --- | --- |
| MiniMax-M3 | cfdquery/aeroengqa/scicode/cfdcode/superwing/aviary/foam_basic | — | — |
| GLM-4.6 | cfdquery/aeroengqa/aviary/scicode/cfdcode/foam_basic/superwing/hilift/pycycle（batch-2 三项 2026-08-21 补齐） | — | 429 限流曾致中断，链 v2 重建后全量完成 |

GLM-4.6 次要基线速览（vs M3）：cfdcode 通过率高（11 vs 8）精度低；scicode 通过率低
（29 vs 42）；foam 代码可执行率高近 3× 但仿真失败反超（67 vs 23）；superwing 系数回归
更差（physics 0.025/0.017 vs 0.080/0.044）；hilift 略优（0.150/0.142 vs 0.124/0.186，
CM 两家同灾难级）；pycycle 同败于幻觉 API。**两家模型强弱势互补、无一能在工程可执行层
立足**——详见 results/batch2-round1-summary.md §2。

复现性：stub/oracle 离线逐字节可复现；API 基线受推理非确定性影响（temperature=0 下思考
型仍非逐题确定）。所有命令/seed/digest 落各 run_manifest。

## 7. 结论（能力画像，非排名）

M3 画像：**会答概念题（knowledge 0.85）> 会写科学代码（coding 0.57）> 会做 MDO 脚本
（mdo 0.25，过 gate 即满分）≈ 系数预测（physics 0.08）> 会写可运行 OpenFOAM 算例
（0/110，全部脚本级失败）**。
「懂航空」与「会做工程」之间落差清晰——正是 v0.1 设计要暴露的事实。cad/结构/动力/飞控
四维待 batch-2 补位后方能闭合九维全景。
