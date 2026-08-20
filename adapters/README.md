# Benchmark Adapter 规范（v0.1）

> 原则：**不要为每个 benchmark 单独写 runner。** 所有基准按任务声明归入五类标准 adapter 之一；benchmark 特有的差异只允许通过任务 YAML 的字段表达，不允许 fork adapter 代码。
> 一个 adapter = 输入契约 + 运行器职责 + 输出契约 + 判分管线 + 失败模式定义。

## 通用约定（所有 adapter 继承）

### 运行器职责

1. 读取任务 YAML（见 `contracts/task.example.yaml`），校验必填字段与环境摘要（`environment_digest`）；
2. 准备隔离执行环境（容器/沙箱），挂载 `assets_revision` 锁定的数据与资产，只读；
3. 以任务声明的 `model_profile` 调用被测 Agent/模型，施加 `allowed_tools` 白名单与 `limits`；
4. 收集 `output_contract` 声明的产物；缺产物即判 `missing_output`，进入失败模式；
5. 调用本 adapter 的判分管线，产出标准化 `result.json`（见下）；
6. 全程写审计日志：模型调用参数、工具调用序列、产物摘要、判分中间量。

### 标准输出 result.json

```json
{
  "task_id": "crm_dpw_case_001",
  "registry_id": "crm_dpw_hlpw.coarse",
  "adapter": "simulation_agent",
  "validity_gate": 0,
  "gate_failures": ["simulation_diverged"],
  "subscores": {"physics": 0.0, "requirements": 0.0, "objective": 0.0, "robustness": 0.0},
  "score": 0.0,
  "artifacts": {"case_directory": "...", "result_json": "..."},
  "timings": {"setup_s": 0, "agent_s": 0, "grade_s": 0},
  "environment_digest": "sha256:...",
  "assets_revision": "nasa_crm_revision_x",
  "logs": ["..."]
}
```

### 通用失败模式（failure modes）

| 代码 | 含义 | 计分 |
| --- | --- | --- |
| `missing_output` | output_contract 声明的产物缺失 | score=0 |
| `env_mismatch` | environment_digest 不匹配 | 该任务作废（不计分，需修环境后重跑） |
| `timeout` / `oom` | 超出 limits | score=0 |
| `tool_violation` | 使用了 allowed_tools 之外的工具 | score=0 |
| `crash` | 运行器/判分器自身故障 | 该任务作废并告警（不计入模型分） |

---

## 1. qa_grounded（有据问答）

**适用**：aeroengqa.gold、cfdllm.cfdquery、gsm8k.math_reasoning、mechvqa.public_eval、camb.selective（若放行）

**输入契约**：题目（文本或图文）、可选证据文档集（RAG 目标语料）、参考答案 + 参考证据定位、是否"应拒答"标记。

**模型输出**：答案字段（选择题=选项；问答=自由文本+引用列表；数学题=CoT+最终数 `#### <number>`）。

**判分管线**：

1. **客观层**：选择题精确匹配；自由文本按 Exact/F1/关键字数值容差（数值题 ±ε）；数学题（`answer_format: math_answer`，GSM8K 型）最终数抽取（`####` 优先 → `answer is`/`答案` → 全文末数）后数值精确匹配，gate=最终数可解析。
2. **证据层**（仅提供证据语料的任务）：
   - `evidence_support`：引用的段落是否真实存在且支持结论（段落级匹配，规则判）；
   - `fabrication_rate`：引用不存在段落的比例。
3. **拒答层**：对"应拒答"题，回答了记 0，正确拒答记 1；对"应回答"题拒答记 0。
4. **区分层**（可选，AeroEngQA 专项）：是否区分 报告原文 / 计算结果 / 模型推断（由答案的声明结构规则抽取）。

**子分映射**：`requirements`=客观层，`physics`=证据层+拒答层，`objective`=区分层（无则并入 requirements），`robustness`=多次采样答案一致性（可选）。

**边界**：LLM judge 只允许评估"解释质量"并单独报告，不进入 `score`。

---

## 2. code_exec（科学代码执行）

**适用**：scicode.physics、cfdllm.cfdcode、humaneval.python、mbpp.sanitized

**输入契约**：自然语言任务 + 函数签名/模板 + 隐藏测试集（模型不可见）+ 每测试的数值容差。

**运行器**：Python 沙箱（无网络、受限 imports、CPU/内存/墙钟限额）；每题可编译/运行的尝试次数上限由任务声明。

**判分管线**：

1. `executability`：代码可导入、可调用入口（0/1）；
2. `hidden_tests`：隐藏单元测试通过率（每测独立计）；`unit_tests_problem`（humaneval/mbpp）= 官方断言逐条执行（humaneval 由 `check(candidate)` 块 AST 拆分为逐断言 case，helper 逐 case 前置），summary 另报 pass@1（全断言通过任务占比，社区口径）；
3. `numerical_tolerance`：数值断言按 相对/绝对 容差判定，非布尔；
4. `stability`：边界输入、退化输入不崩溃（如奇点、零向量、空数组）；
5. `determinism`：同输入重复运行结果一致（捕获未固定种子/迭代顺序问题）。

**子分映射**：`physics`=隐藏测试+数值容差，`requirements`=入口契约满足，`objective`=稳定性，`robustness`=确定性。

**失败模式追加**：`sandbox_escape_attempt`（尝试网络/文件系统越界）记 0 并单独告警。

---

## 3. simulation_agent（仿真工程 Agent）

**适用**：cfdllm.foam_basic（paused-env）、aviary.transport_mission、pycycle.engine_cycle、gtm.transport_control、nasa_tmr.verification、crm_dpw_hlpw.coarse、bscw.aeroelastic（paused-env）

> 环境注（2026-08-19）：内网无 OpenFOAM。TMR/CRM 的求解侧使用内网已许可的 Fluent（journal 批处理）/StarCCM+（macro 批处理）；FoamBench 因题目与判分绑定 OpenFOAM 算例格式而暂缓。详见 env-matrix.md。

**输入契约**：任务描述 + 资产（几何/网格/模型文件，锁定 revision）+ 参考指标（带不确定度）+ 检查器配置。

**运行器**：容器内提供任务声明的求解器/框架；Agent 可创建、修改、运行算例并后处理。

**判分管线**（严格顺序，前置不过即短路）：

1. **validity gate（硬门槛，任一失败=0 分）**：
   - 代码/脚本可执行；
   - 算例结构合法（对 CFD：网格合法、边界条件完备、单位正确）；
   - 求解收敛（按任务声明的收敛定义：残差阈值 + 监控量平稳）；
   - 基本守恒/物理约束（质量/能量闭合、场变量在物理范围）；
   - 硬性设计约束逐条满足（若任务声明）。
2. `physics`：目标量对参考的误差带评分（CL/CD/CM、油耗、推力、模态频率等，考虑参考不确定度）；
3. `requirements`：任务声明的全部输出项与工况覆盖；
4. `objective`：任务有目标函数（如最小起飞重量）时按阈值达成度；
5. `robustness`：隐藏扰动重算（改工况/改网格/注入参数扰动后仍收敛且误差带内）。

**特别规则**：
- "算例跑完"≠通过，gate 检查器缺一不可；
- 参考指标必须预计算、锁版本、记录不确定度；
- 隐藏动态题（`hidden_dynamic: true`）从参数空间采样生成，采样种子与答案不入库明文。

---

## 4. design_artifact（设计制品评审）

**适用**：cadgen.local_validity、simjeb.structure、openvsp.geometry_aero（paused-env）

**输入契约**：设计需求（包络/接口/质量等约束）+ 可选输入制品（STEP/模型）+ 制品检查器清单。

**模型输出**：设计制品文件（STEP/STL/VSP/参数文件）+ 生成代码（可重复执行）。

**判分管线**：

1. **validity gate**：
   - 文件可解析（STEP/OCCT 加载成功）；
   - B-Rep 有效（无自交、无开放壳体、无退化面）；
   - 生成代码可重复执行且复现同一制品（哈希级或几何容差级）。
2. `physics`：几何/结构指标——体积、质量、包络、关键截面、位移/应力范围（对结构任务）；
3. `requirements`：接口配合尺寸、翼展/面积/展弦比等设计约束逐条核对；
4. `objective`：任务目标的达成度（轻量化排序、Pareto 改进量）；
5. `robustness`：**隐藏复算层**——对 Agent 提交的候选方案重新执行 FEA 验证（内网 ANSYS MAPDL，经 PyMAPDL gRPC 串行调用），而非只比对预存标签。

**边界**：依赖私有 ground truth 的相似度分数（如 CADGenBench 官方服务端分数）不得混入本地分数；本地分数只覆盖上列可复现项，报告须标注覆盖范围。

---

## 5. field_prediction（流场/系数预测）

**适用**：superwing.coeff_lite、hilift_aeroml.lite、airfrans.level1（若放行）、pdebench.compressive_ns（若放行）

**输入契约**：输入条件（几何参数、Mach、迎角、Re 等）+ 预测目标（系数/截面分布/表面场）+ 参考真值 + 容差带。

**模型输出**：结构化数值预测（JSON 数组 / npy / 网格函数）。

**判分管线**：

1. **validity gate**：
   - 输出格式与形状合法；
   - 无非物理值（NaN/Inf、C_L 超出物理包络、违反单调性等任务声明的不变量）。
2. `physics`：系数误差带评分（CL/CD/CM 相对误差）；
3. `requirements`：截面压力分布、激波位置标签等扩展目标的逐项误差；
4. `objective`：任务化目标（反设计命中、候选方案排序一致性）；
5. `robustness`：**划分纪律**——内插集 + 几何外推集 + 工况外推集分开报告；任何划分必须按几何构型分组，禁止同一构型不同工况跨集随机分布。

---

## adapter 选型速查

| 基准 | adapter |
| --- | --- |
| cfdllm.cfdquery / aeroengqa.gold / gsm8k.math_reasoning / mechvqa / camb | qa_grounded |
| scicode.physics / cfdllm.cfdcode / humaneval.python / mbpp.sanitized | code_exec |
| cfdllm.foam_basic（paused-env）/ aviary / pycycle / gtm / nasa_tmr / crm_dpw_hlpw / bscw（paused-env） | simulation_agent |
| cadgen.local_validity / simjeb / openvsp（paused-env） | design_artifact |
| superwing.coeff_lite / hilift_aeroml.lite / airfrans / pdebench-NS | field_prediction |
