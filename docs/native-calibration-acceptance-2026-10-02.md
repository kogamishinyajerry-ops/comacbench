# 原生校准桥接增量：开发环境实测记录

> 维护者材料：含参考流程或验收期望，不提供给受试 Agent。受试入口见 [公开操作合同](public-workbench-contract.md)；权限边界见 [受限试验说明](restricted-public-trial.md)。

2026-10-02；Linux / Python 3.13.5。

## 源码来源

实时读取GitHub：默认分支仍为`8f949436...`；PR7仍open，head为`59f3dbe659b750964f5a81c99eb619352657c2ae`。
开发容器DNS无法解析github.com，git ls-remote失败。使用既有PR7证据ZIP中的patch重建源码子集，
逐文件核对原Git blob；未克隆完整仓库。新增文件基于该子集开发。
本轮GitHub连接器的可发现动作没有创建分支/commit/PR接口；交付补丁与PR草稿，由本地接手后提交，未声称新PR已上线。

## 执行结果

`python -m unittest discover -s tests -p 'test_workbench*.py' -v`

106 tests：**105 passed，1 skipped，0 failure，0 error**。
skip是显式opt-in的真实CalculiX流程。本容器无ccx，不能将该项概括为通过。

已有PR7的66个Workbench相关专项保留（catalog的入口数量断言随新增experimental入口更新）。
新增36项native相关测试（其中1项待实机）和4项交接脚本测试。
新测试覆盖：部分失效、限值变更不重算、预算包含失败、不能put伪造native产物、stdout误报、缺失/重复节点、
Fortran D指数、签名位移与反力、退出码失败、超时、源输入漂移、归档篡改、残留任务、迁移和报告复查。

原生control测试使用**明确标记的合成DAT与进程double**，包括参考路径15行动/3请求、stale/false-ready负例。
这不是物理求解证据，不是模型成绩。另实际启动普通Python测试进程，检验退出/超时清理；同样不是ccx。

`compileall`和`git diff --check`通过。完整仓库、旧pack solver、线上CI、本机浏览器均未在本轮运行。

## 交接后如何更新

由本地真实运行生成独立记录，不改写以上开发环境历史。需要保留二进制版本/摘要、每次INP、DAT、日志、
状态文件、原始事件及命令日志。单独说明真实Agent调用是否执行；不得以参考脚本代替。

详细规格与检查阈值见`native-calibration-handoff.md`。公开模板仅作校准，不能代表完整支架设计或飞机工程放行。
