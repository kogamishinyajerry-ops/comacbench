# Batch-2 首轮接入总结（2026-08-19）

> 本轮范围：GLM 429 补跑 + superwing ML 基线 + batch-2 逐项探查与 dev 可行子集接入。
> 运行环境：dev 终端（.venv: om-pycycle 源码装 / aviary / pyvista / sklearn）。

## 1. Registry 状态变化（batch-2 八项全部落定状态）

| registry_id | 之前 | 之后 | 说明 |
| --- | --- | --- | --- |
| pycycle.engine_cycle | proposed | **integrated** | 自建 7 任务（vendored 官方 turbojet 引擎）+ oracle 7/7 + M3 基线（0/7，幻觉 API） |
| hilift_aeroml.lite | proposed | **integrated** | 系数层镜像（1800 样本 + 180 构型几何）+ oracle 100/100 + M3 基线（CM err 200-350%） |
| mechvqa.public_eval | proposed | staged | 镜像完成（Apache-2.0，1185 题+图纸）；**多模态通道缺失 blocked** |
| cadgen.local_validity | proposed | proposed | 探查完成：GT 私有 + text+image 输入 + design_artifact 未实现——三重前置 |
| simjeb.structure | proposed | proposed | **blocked-env**：dev 无 ANSYS MAPDL；许可 needs-verification |
| gtm.transport_control | proposed | proposed | **blocked-env**：dev 无 MATLAB（JSBSim 快层可先行但许可未核） |
| nasa_tmr.verification | proposed | proposed | **blocked-env**：dev 无 Fluent/StarCCM+；逐案例许可未核 |
| crm_dpw_hlpw.coarse | proposed | proposed | **blocked-env**：同上 + 版本锁定未做 |

## 2. GLM 429 补跑（端点恢复后串行）

| 基准 | 结果 |
| --- | --- |
| cfdllm.cfdcode | **gate 11/15，均分 0.586**（过 gate 题 physics 0.598）——GLM 通过率高于 M3（11 vs 8），精度低于 M3（0.598 vs 0.937）：画像分化 |
| scicode.physics | **gate 29/52，均分 0.477，满分 11**（23 code_not_executable——通过率低于 M3 42/52，画像分化） |
| cfdllm.foam_basic | **gate 0/110**：36 code_not_executable + 67 simulation_failed + 7 missing_output——vs M3（87+23）：GLM 可执行率高近 3× 但仿真失败反超，「写得出来 ≠ 算得出来」 |
| superwing.coeff_lite | gate 100/100，均分 0.4135：physics 外推 **0.025**/内插 **0.017**（M3 0.080/0.044）——CL err 300-479%，跨声速系数回归 GLM 更差 |
| hilift_aeroml.lite | gate 100/100，均分 0.4885：physics 外推 **0.150**/内插 0.142（M3 0.124/0.186）——CM err 338-370%，两家 LLM 同败于高升力俯仰力矩（ML 正例 0.82/0.88） |
| pycycle.engine_cycle | **gate 0/7**：7 code_not_executable——同类幻觉 API（`ThermoZone` 不存在等，solve <2s 即败）；环境无责（oracle 7/7） |

> 运行学（2026-08-20/21 补齐过程）：v1 串行链随仓库迁移死亡（见 §8.1）→ v2 重建
> （`--resume` 断点续跑 + venv 兼容栈重建）后进一步拆 4-5 条并行流（任务族不相交、
> 同 out 目录幂等、峰值 ~0.6 req/min 无 429），20:32→02:32 共 6h 跑完余下
> foam 96 + superwing/hilift/pycycle 全量 207 题；单题时长 3-44 min 波动
> （长尾 = 反应流算例 OpenFOAM 仿真本身 + 偶发超长思考重试）。

## 3. superwing ML 基线（正例参照）

RandomForest(100 trees, sklearn) on 25985 训练样本（38 几何参数 + aoa + mach）：

| 组 | LLM (M3) | **ML (RF)** | 差距 |
| --- | --- | --- | --- |
| 内插 physics | 0.044 | **0.828**（CL 13.7%/CD 4.7%/CM 8.8%） | ~19× |
| 几何外推 physics | 0.080 | **0.485**（CL 21.6%/CD 13.4%） | ~6× |

**结论成立**：同一判分管线下 ML 与 LLM 差一个数量级——field_prediction 维度的「LLM 不会」
有了正例对照（后续 AeroTransformer 级深度模型可再刷新上限）。

## 4. hilift_aeroml.lite（新增 integrated）

- Lite 镜像 ~280KB（force_mom_all.csv 全量系数 + geo_values_all.csv 180 构型 8 维几何，
  hub snapshot 批量下载——直连被限流）；
- 任务 100 = 几何外推 70（36 保留构型）+ 内插 30；
- M3：gate 100/100、physics 内插 0.186/外推 0.124——**CM 相对误差 218-353%**（高升力
  俯仰力矩对 LLM 最难），与 superwind 同结论互相印证；
- **ML 正例基线（ml-hilift，2026-08-20 补齐）**：RF 同款（1410 训练行 = 36 保留构型
  全剔除 + 30 内插测试行剔除），gate 100/100，physics 内插 **0.883** / 几何外推
  **0.821**（CL 2-3%/CD 3-4%/CM 16-17%）——与 LLM 差 ~4.7×/6.6×；几何外推衰减远小于
  superwing（0.82 vs 0.49）；CM 对 RF 也最难但低一个数量级（或近 WMLES 真值噪声地板），
  详见 `results/hilift_aeroml.lite/2026-08-19/ml-hilift/README.md`。

## 5. pycycle.engine_cycle（新增 integrated）

- **PyPI `pycycle` 是抢注空壳**（仅 cli/utils）——真包须源码装 `om-pycycle`（已入 PROVENANCE）；
- vendored 官方 turbojet 引擎（Apache-2.0）+ 参数化 `solve_design`（官方完整初值序列
  保证收敛：SL 设计点域 Fn∈[9k,16k]/T4∈[2200,2900]/OPR∈[11,16] 稳定；巡航高度参数化
  会使 OD 发散——高度权衡任务未纳入，待议）；
- oracle 7/7；M3 0/7（5 code_not_executable = 幻觉 API 如 `TabularThermo`，2 missing_output）；
- 隐藏动态试点 1 例（base64 隔离）。

## 6. 判分器缺陷修正（本轮第 2 个）

- 沙箱裸 `system(`/`popen(` 子串模式**误伤 `prob.model.add_subsystem(...)`**（OpenMDAO
  标准调用）——已移除裸子串模式（`os.system` 全名仍拦），pycycle M3 重跑后 sandbox_escape
  清零。与 M4 的 os.chmod 误封同类：**子串式黑名单对科学计算 DSL 调用名过敏**，
  教训已固化在 sandbox.py 注释。

## 7. 九维度报告更新点

- cfd 维：hilift 加入（M3 physics 内插 0.186/外推 0.124 + superwing ML 正例 0.83/0.49）；
- propulsion 维：**pycycle 从 N/A 变为有数**（M3 0/7）；
- 其余维度不变。

## 8. 待议清单（本轮新增）

1. ~~GLM 串行链遗留~~ **已闭环（2026-08-21 02:32）**：v1 死因（旧路径 cwd + .venv 删除）
   → v2 重建（`--resume` + venv 兼容栈 + 沙箱 3.12 修复，commit 5e251dda）→ 4-5 并行流
   6h 跑完全量，四基准 GLM 基线全部落盘（§2 终版数据）；
2. ~~hilift ML 正例基线（RF 同款）待跑~~ **已补齐**（ml-hilift，见 §4）；
3. mechvqa 多模态 provider（expect="vlm"）+ 规则判分口径评审；
4. cadgen 三重前置（design_artifact adapter / 多模态 / GT 私有边界声明）；
5. pycycle 高度权衡任务（需参数化 OD 点序列避免发散）；
6. simjeb/gtm/nasa_tmr/crm 四项 intranet 环境就绪后接入（许可多数未核）。

## 9. 产出文件

```
benchmarks/
├── runners/gen_tasks_{hilift,pycycle}.py + providers.py（ml_superwing / ml_hilift + json 模式）
├── tasks/hilift_aeroml.lite/     100 yaml + 100 md
├── tasks/pycycle.engine_cycle/   7 yaml + 7 md
├── data/hilift/lite/             系数层镜像 + PROVENANCE + sha256
├── data/pycycle/engine_cycle/    vendored 引擎 + gold + references + hidden + PROVENANCE
├── data/mechvqa/public_eval/     镜像（1185 题 + 图纸，383MB）+ PROVENANCE
├── results/hilift_aeroml.lite/2026-08-19/{README.md, oracle/, stub/, minimax-m3/, ml-hilift/}
├── results/pycycle.engine_cycle/2026-08-19/{README.md, oracle/, stub/, minimax-m3/}
├── results/superwing.coeff_lite/2026-08-19/ml-superwing/（ML 正例基线）
├── results/cfdllm.cfdcode/2026-08-19/glm-4.6/（GLM 补跑完成 11/15）
└── registry/registry.yaml（batch-2 全八项状态落定）
```
