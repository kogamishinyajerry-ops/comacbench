# 内网评测环境矩阵（env-matrix）

> 2026-08-19 决策依据：内网商业工具栈 = ANSYS 系、StarCCM+、CATIA、Amesim、FENSAP、MATLAB（均有许可）；无内部 PyPI 镜像，Python 包由验收人**手工批量导入**。
> **2026-08-19 二次决策（最新，以此为准）**：当前开发与评测在**外网开发终端**进行——该终端装有 **OpenFOAM + FoamAgent**，无 Fluent/StarCCM。CFD 端到端开发期用 OpenFOAM 原型；内网商业栈是**最终移植目标**而非当前执行环境。
> 规则：**评测所需环境在目标环境不可启动 => 该 benchmark 进入 `paused-env`**。目标环境分两层：`dev`（开发终端，现在跑评测的地方）/ `intranet`（内网，移植目标）。本文件是 env_class 判定与 Python 导入清单的 SSOT。

## 0. 两层目标环境

| 层 | 机器 | 可用求解器 | 用途 |
| --- | --- | --- | --- |
| `dev`（当前活跃） | 外网开发终端 | **OpenFOAM + FoamAgent**、**MATLAB R2026a**、**CalculiX ccx**（brew）、Python/pip 直连 | 当前一切开发与评测在此跑 |
| `intranet`（移植目标） | 内网 | ANSYS 系、StarCCM+、CATIA、Amesim、FENSAP、MATLAB；无 OpenFOAM | 最终部署；CFD 端到端换 Fluent journal / StarCCM macro runner |

**求解器无关原则**：simulation_agent / design_artifact 的 grader 只认 result.json + 残差/守恒/目标量，不绑定求解器 CLI。开发期 OpenFOAM runner 与内网 Fluent/StarCCM runner 是同一 adapter 下的两个可替换执行后端。

## 1. 环境类别与可用性

| env_class | 依赖 | 可用性 | 需要你做的一次性动作 | 覆盖的 registry 条目 |
| --- | --- | --- | --- | --- |
| `qa` | 仅模型调用 + 文本/图文判分 | ✅ 现成 | 无 | cfdquery、aeroengqa、mechvqa、camb、designqa |
| `python_sandbox` | 纯 Python 包（无原生依赖） | ✅ 可用（手工导入） | 按下方分阶段清单在外网机下载 wheel，批量导入一次 | scicode、cfdcode、engdesign、aviary、pycycle、cadgen、cadbench、afbench、openconcept |
| `data_only` | 参考数据 + 数值比对 | ✅ 可用 | 外网机下载数据子集后导入 | superwing、hilift_aeroml.lite、airfrans、pdebench-NS、aircraftverse |
| `openfoam_dev` | OpenFOAM + FoamAgent（开发终端） | ✅ 可用（dev 层） | FoamAgent/OpenFOAM 已装则无动作 | foam_basic（已恢复 v0.1 核心）、nasa_tmr/crm_dpw_hlpw 的开发期原型 |

> **2026-08-19 M3 实测修正（dev 层 OpenFOAM 形态）**：开发终端无本机 OpenFOAM 安装、无 FoamAgent 包；
> OpenFOAM 以 **docker 镜像**提供——`openfoam/openfoam10-paraview510`（amd64/qemu 模拟，**v10=FoamBench
> 上游指定版本**，判分管线采用此镜像）与 `opencfd/openfoam-default:2312`（arm64 原生但 ESI 方言与
> Foundation v10 算例不兼容，仅备查）。FoamBench 语境中 "Foam-Agent" 为被测算法框架而非 harness 依赖。
> 判分侧经 `runners/solvers/openfoam.py` 调 docker；本条不改变求解器无关原则（grader 只认产物+判据+场结果）。
| `commercial_cfd` | Fluent / StarCCM+ 无界面批处理 | ✅ 已许可（仅内网层） | 与 IT 确认批处理许可座席调度窗口 + 版本锁定 | nasa_tmr、crm_dpw_hlpw（内网移植目标态） |
| `commercial_fea` | ANSYS Mechanical APDL（PyMAPDL gRPC） | ✅ 已许可 | 同上（APDL 座席） | simjeb |
| `matlab` | MATLAB（batch 子进程；matlabengine 不用——版本配对脆弱，`matlab -batch` 更稳且与沙箱隔离子进程语义一致） | ✅ **dev 已就绪**（2026-08-22 装 R2026a U3，Sponsored License，CST/Aerospace TB 齐备，batch 启动 ~28s/次，执行后端 `runners/solvers/matlab.py`，MATLAB_BIN 可覆写） | 内网层移植时版本锁定 | gtm（JSBSim 侧归 python_sandbox） |
| `calculix_native` | CalculiX ccx（`ccx -i` 子进程 + 进程组超时杀；GPL-2.0，执行后端 `runners/solvers/calculix.py`，CCX_BIN 可覆写） | ✅ **dev 已就绪**（2026-08-24 brew calculix-ccx 实测 2.23；烟测与解析互证：悬臂静力 0.06%/模态 0.5%/屈曲 0.5%） | 内网层移植：源码编译或离线二进制导入 + 版本锁定 | calculix.fea_basic（structures 维自建，simjeb 商业 FEA 线之外的 dev 层落地） |
| `missing` | 内网不存在且不部署的工具 | ❌ | 见第 4 节恢复条件 | foam_basic(OpenFOAM)、openvsp、bscw(气弹链)、cadbench_seldon(Autodesk Fusion GUI——dev/intranet 均无，Seldon 沙箱需私下联系) |

## 2. Python 离线导入清单（分阶段，每阶段一次批量导入）

> 无镜像环境下的减负原则：**一个里程碑一批 wheel，导入后把逐包版本写进 `environment_digest` 归档**，之后同阶段 benchmark 共享该环境，不再逐个导入。
> 在外网机用 `pip download -d <dir> -r <phase>.txt`（或 `pip wheel`）获取全量依赖闭包，整目录拷入内网 `pip install --no-index --find-links=<dir>`。

### Phase-A（M1/M2：qa + code_exec）

```
python == 3.11.x            # 与内网 DeepSeek Harness 代理运行时对齐后锁定小版本
pytest
numpy, scipy, pandas
sympy                       # SciCode 部分题依赖
matplotlib                  # 判分报告绘图（可选）
```

### Phase-B（M3/M4：simulation_agent 自建包）

```
openmdao                    # 与 aviary 版本配对锁定
aviary                      # NASA Aviary（含示例模型）
# pycycle（batch-2，可与本批一并导入以省一次操作）
# openconcept（conditional，如法务核对通过可顺手导入）
```

### Phase-C（M4：data_only 判分）

```
# 无新增必选项：pandas 即可完成 superwing/hilift-lite 系数比对
# 可选：torch(CPU 版) —— 仅当要跑 ML 基线模型（superwing/airfrans/pdebench 基线）
```

### Phase-D（batch-2：CAD/FEA/飞控）

```
cadquery                    # 含 OCP(OpenCascade) 预编译 wheel，覆盖 cadgen/cadbench 的 STEP/B-Rep 检查
jsbsim                      # 纯 wheel
ansys-mapdl-core            # PyMAPDL，gRPC 连内网 MAPDL（commercial_fea 判分复算）
matlabengine                # 对应内网 MATLAB 版本（gtm 层）
```

### 数据类导入（外网下载 → 拷入内网）

| 数据 | 体量（Lite 子集） | 用途 |
| --- | --- | --- |
| SuperWing 系数层（CL/CD/CM+截面+激波标签） | 远小于 3.49TB 全量，仅系数层 | superwing.coeff_lite |
| HiLiftAeroML Lite（几何/工况/总力/截面/分离标签） | 从 66.9TB 中仅抽取元数据层 | hilift_aeroml.lite |
| AeroEngQA / SciCode / CFDLLMBench 仓库快照 | 小 | 对应条目（镜像前先过 license-status） |

## 3. 商业工具批处理自动化要求（commercial_cfd / commercial_fea / matlab）

| 工具 | 批处理方式 | 需确认项 |
| --- | --- | --- |
| Fluent | `fluent -t<N> -g -i case.jou`（journal 脚本，TUI 全流程） | 许可座席调度窗口；版本锁定（影响网格/求解器设置兼容性）；CGNS 导入 |
| StarCCM+ | `starccm+ -batch macro.java`（Java macro 录制回放） | 同上 |
| ANSYS MAPDL | PyMAPDL gRPC（ansys-mapdl-core）驱动 APDL 求解 | Mechanical APDL 座席；批处理并发数 |
| MATLAB | matlabengine-for-python 调用 GTM_DesignSim 脚本 | MATLAB↔Python 版本兼容表 |

统一要求：所有商业求解器调用由 runner 串行排队（不并发抢座席）；求解器版本写入 `environment_digest`；每类工具先跑一个 1 例冒烟任务验证批处理链路，再接入正式任务。

## 4. 暂缓条目（paused-env）与恢复条件

| registry_id | 缺失环境 | 恢复条件 | 恢复前的能力承接 |
| --- | --- | --- | --- |
| ~~cfdllm.foam_basic~~ | （已恢复 2026-08-19：开发终端有 OpenFOAM + FoamAgent，env_class=openfoam_dev，回到 v0.1 核心） | — | — |
| openvsp.geometry_aero | OpenVSP 原生二进制 + VSPAERO | 手工导入 OpenVSP 发行包 且 NOSA 法务放行 | CAD/几何能力由 cadgen.local_validity（pythonocc）承接 |
| bscw.aeroelastic | 气弹耦合工具链 | 可用气弹环境出现或 ANSYS FSI 自动化预算获批 | 无（批次 2 末位，无阻塞） |

## 5. 给验收人的最小动作清单（汇总）

1. **一次性**：与 IT 确认 Fluent / StarCCM / MAPDL / MATLAB 的批处理许可座席与版本（第 3 节表格）；
2. **Phase-A 一批 wheel**（M1/M2 启动前）：第 2 节 Phase-A 清单 → 导入 → 回填 `environment_digest`；
3. **Phase-B 一批 wheel**（M3 启动前）：openmdao+aviary（可带 pycycle）；
4. **数据拷贝**：SuperWing 系数层、HiLift Lite、各基准仓库快照（镜像前查 license-notes.md 放行状态）；
5. **Phase-D 一批 wheel**（batch-2 启动前）：cadquery / jsbsim / ansys-mapdl-core / matlabengine。
6. 不需要做：安装 OpenFOAM / OpenVSP / 任何气弹工具链（已明确暂缓）。
