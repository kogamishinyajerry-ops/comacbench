# StarCCM+ 批处理后端落地（commercial_cfd 线第一步）

日期：2026-09-21 ｜ 分支：codex/trusted-resume-and-formula（接 23a759f4 Windows 修复第一批）

## 0. 一句话结论

`runners/solvers/starccm.py` 执行后端落地并**实机验证通过**：本机 STAR-CCM+ 19.02.009-R8 批处理通道（`starccm+.bat -new -batch macro.java`）+ `ccmpsuite` 许可检出（`C:\Users\Kogami\license.dat`，不过期）全部打通，宏冒烟 47s EXIT=0；接口封装 `run_starccm()` 复跑 12.4s 同样 EXIT=0。这是 registry 中 `nasa_tmr.verification` / `crm_dpw_hlpw.coarse`（env_class=commercial_cfd，proposed）从「paused-env 无求解器」到「dev 层可执行」的第一块基础设施——按 env-matrix §1 的既定移植路径（"intranet 增 starccm.py（macro），adapter 与任务 YAML 不变"）。

## 1. 变更清单

| 文件 | 内容 |
| --- | --- |
| `runners/solvers/starccm.py`（新增） | `starccm_binary()` 定位（STARCCM_BIN > 安装探测 > PATH）；`run_starccm()` 批处理执行（超时硬杀，Windows nt 分支 proc.kill）；`StarCCMSolver` 类实现 `runners/solvers/__init__.py` 的 Solver 接口契约（run_case/execution_ok），name=`starccm-19.02.009-batch` |
| `runners/solvers/openfoam.py` | `get_solver()` 注册新后端名（fluent 未实现仍正确拒绝） |
| `tests/test_starccm_solver.py`（新增） | 8 项契约测试：二进制定位/覆写/缺失报错、缺 macro fail-fast、批处理命令构造（-batch/-sim）、execution_ok 判据（Server disconnected 且无 Fatal）、路由注册、未知后端拒绝 |
| `report/2026-09-21-starccm-backend/` | 本报告 + batch-smoke.log（裸跑 47s 证据）+ smoke-macro.java |

## 2. 实测证据

```
$ starccm+.bat -new -batch macro.java        （smoke：打印 COMAC_SMOKE_OK）
1 copy of ccmpsuite checked out from C:\Users\Kogami\license.dat
Feature ccmpsuite does not expire
正在播放宏： ...\macro.java
COMAC_SMOKE_OK
Design Simcenter STAR-CCM+ simulation completed
EXIT=0, 47s

$ python -c "run_starccm(d,'macro.java',240)"  （仓库后端封装）
exit: 0 | timeout: False | duration_s: 12.39 | smoke marker: True
```

测试：`tests.test_starccm_solver` 8/8 OK（不占许可座席——mock Popen，真求解冒烟独立落证据）。

## 3. 边界声明（判分语义零改动）

- 本层只负责「跑起来 + 状态带回」，QoI 抽取走 macro 导出的表/场文件由 grader 侧读取——遵循 kickoff 硬性要求「grader 只认 result.json + 残差/守恒/目标量，不绑求解器 CLI」；
- `execution_ok` 只回答批处理会话是否正常走完（Server disconnected 且无 Fatal），**不是收敛判据**；收敛/QoI 验证属 adapter 层（对齐 backward_step 的 residuals/mass_balance 模式，后续按 nasa_tmr 任务设计）；
- 单元测试不跑真求解器（许可座席纪律，env-matrix §3）；实机冒烟已另行收口于本报告；
- R8 macro API 已知削减（probe/getValue(coordinate)/DynamicQuerySelectorInput 反射不可用）——macro 内只走稳定 API，复杂取值由导出场文件承担。

## 4. 下一步（nasa_tmr 线推进路径）

1. TMR 首个标准算例（2D flat plate / axisymmetric jet，turbmodels.larc.nasa.gov 公开参考数据）的 macro 生成 + CGNS 网格导入批处理实测；
2. grader 侧：残差/收敛判据 + QoI（如 Cd/CF 分布）导出与公开参考比对——参照 cfdb 的 evidence 两阶段协议（判分侧不跑求解器、冻结 QoI 脚本对证据包降算）；
3. registry 条目 `nasa_tmr.verification` 状态流转：proposed → （数据镜像+环境可复现后）staged；
4. 版本锁定记录：STAR-CCM+ 19.02.009-R8 + license 2024.02（写入 environment_digest）。
