# CFD 后向台阶 v1：平台保管的求解证据

## 目标与范围

提供独立的 `packs/aviation-cfd-step-v1`，通过已有 simulation_agent 和外部 JSON agent 协议执行一题 Re=100、二维层流后向台阶。保留所有旧任务、修改中的 CFDB YAML、旧包和历史报告。继续单 agent 实施，不引入新框架。

受测 agent 交付 Python 脚本，生成原生 `case/0`、`case/constant`、`case/system` 八份 OpenFOAM 输入文件。平台负责一次性执行脚本、只读检查输入、blockMesh、checkMesh、simpleFoam、原生场降算和结果报告。禁止由受测脚本在求解后重新组装或覆盖判分证据；自报 QoI、预制时间目录和自带日志不参与判分。

新类型 `cfd_step` 是原 simulation_agent 的受限分支。固定求解器 OpenFOAM Foundation 10，使用当前已安装 Docker 镜像的不可变摘要；独立于旧 v2312 配置。容器禁止网络并限 CPU、内存、PID 和总墙钟，超时按本次容器 ID 清理。受测 Python 仍是本地受信执行，不声称操作系统级隔离已完成。

## 实施次序

1. 审查上游题面、参考值和执行方式；复制输入到新目录实跑 Foundation 10。
2. 明确输入方言和固定离散格式；校验单位、层流、入口剖面、边界、几何与网格实际产物。未实现的关键字不静默跳过。
3. 收敛检查使用原生日志的残差下降和收敛声明；质量守恒使用最终场 phi 的边界通量；再附着位置从下游底壁原生壁面剪切场零点重算，排除竖直台阶面。
4. 固定包级工程阈值与参考来源，加入缺边界、粗网格、预制 QoI、未收敛、错误黏度等负例；贡献预检提供字段、问题和修复建议。
5. 通过统一 CLI 校准和 reference agent 接口，更新离线报告，核对历史摘要。

## 验收条件

- `.venv/bin/python -m unittest discover -s tests -v` 退出 0；覆盖缺失、畸形和伪造输入，残差/通量/QoI 异常先行失败。
- `python -m comacbench validate packs/aviation-cfd-step-v1` 可运行；遗漏参考来源、阈值、单位或未知检查项时不可运行。
- `calibrate` 实跑 OpenFOAM，参考题满分，所有故障负例命中预期诊断；不会仅凭进程退出 0 宣称收敛。
- 外部 reference agent 通过同一管线，明确标为接口验证，不作为真实模型排名。
- 报告展示输入、网格、求解、收敛、守恒和 QoI 阶段；可视化曲线来源为原生残差和壁面剪切数据。保留原始输入、mesh、U/p/phi/wallShearStress、原生日志、镜像身份和文件摘要。
- `report/2026-09-06-cfd-step-v1/prior-artifacts.json` 记录的历史文件摘要不变，原先修改中的 CFDB YAML 字节不变。

## 参考与可解释边界

Erturk 2008 原文第 2 节使用平均入口速度和入口水力直径（2 倍入口高度）定义 Re；表 5 的 ER=2、Re=100 对应 X1/h=2.922。本轮已独立核对这两处，不仅依赖仓库 provenance 自述。论文采用更长的上下游域和细网格，本包的 -5h..30h、小样本网格及容差只能作为受限复现，不能声称完整论文复现或飞机工程接受。

- [Erturk 2008 DOI](https://doi.org/10.1016/j.compfluid.2007.09.003)
- [作者论文全文及表 5](https://www.researchgate.net/publication/223115490_Numerical_solutions_of_2-D_steady_incompressible_flow_over_a_backward-facing_step_Part_I_High_Reynolds_number_solutions)
- [Foundation 10 边界条件](https://doc.cfd.direct/openfoam/user-guide-v10/boundaries)
- [Foundation 10 wallShearStress 源码](https://cpp.openfoam.org/v10/wallShearStress_8C_source.html)

单位为 m、s、m²/s、运动压力 m²/s²。壁面剪切按不可压运动应力量读取；rho=1 kg/m³ 时乘 rho 后数值等于 Pa。下游底壁按流动方向定义符号，使用 -tau_x，不能把近壁速度的线性估计标为直接壁面剪切。两次末段场的零点位置用于稳定性检查，网格收敛仍需另行研究。
