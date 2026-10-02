# 2026-10-02 本机原生验收记录

在 PR #7 的工作包中接入真实 CalculiX 2.23。两工况基线后，载荷变更仅重算 limit；位移限值收紧时只重验 review。参考流程以 `complete=true, claim=needs_review` 结束，陈旧结果与虚报通过被拒绝。

Draft，叠在 `review/change-workbench-product-scope-20261002`；PR #7 实时仍 OPEN、未合并，HEAD 为 `59f3dbe659b750964f5a81c99eb619352657c2ae`。不包含 PR #6，不自动合并。

## 实现与现场修复

- 集成工作包的 15 文件原生增量：固定 C3D20 模板、broker-owned solve、原始产物归档、独立复读及本机验收脚本。
- 修复 macOS `/var` 系统目录别名导致合法快照误拒；仍拒绝快照内部文件/目录链接与文件漂移。
- 版本查询接受严格的 2.23 banner 及 upstream `-v` 正常退出约定 201，并归档退出码。真实求解仍要求退出码 0；超时、异常、混入错误输出、错误版本继续拒绝。物理阈值保持 3% / 1e-5 / 1e-6。
- 修复 `python -m comacbench.workbench` 加载两份异常类导致篡改错误逃出结构化 CLI 的问题；新增真实子进程负例。
- 公开 `observe.contract` 补充 `op`、各行动字段和可执行 solve 示例，修复真实 Agent 首次接入暴露的格式缺口。

## 本机实际验证

macOS 26.5.2 / Apple Silicon；既有 Python 3.12.13、PyYAML 6.0.3；已有 `/opt/homebrew/bin/ccx`，解析至 Cellar 2.23。没有安装软件或修改全局环境。

受测源码：`df96c27f986a9d8297de0117f8ba23457b266f7f`（后续提交只更新交付文档）。ccx SHA-256：`2c50665d81815b4f425552ad604d16b12f338169aa1e13447a1cb173902965e4`。

- 最终专项 **114 tests：113 passed、1 skipped、0 failed / errors**；skip 为单独 opt-in 单测，真实求解另由验收流程记录，未把 skip 算作 pass。
- 参考：15 行动 / 3 求解，complete=true、needs_review。
- stale：8 行动 / 2 求解，`unverified_targets`；false-ready：15 行动 / 3 求解，`false_completion_claim`。
- 迁移复读成功；篡改副本返回结构化 `native_archive_changed` / exit 2。
- 独立复核 8 个真实 job 的 INP、DAT、日志、节点集合与反力方向：1077 nodes、160 C3D20、根部/远端各 37 节点；service job 与摘要保留，限值变化后零新增 solve。
- service -100 N：uy=-0.3811745 mm、RFy=+100.00001 N；limit -120 N：-0.4574094 mm、+120.00003 N；变更后 -140 N：-0.5336443 mm、+140.00003 N。最终 limit 超过 0.45 mm。
- 既有文件型 Workbench 三流程回归、4 项 campaign source-export 测试、真实目录 `catalog --check`、compileall 与 diff 检查通过。不是全仓测试。

## 真实 Agent 公开开发试验

仅运行一次既有 `dsh headless` 0.2.0-rc.2；配置声明 `zai-coding-cn / glm-4.7`，没有配置覆盖或模型批测。独立 user_agent session 基于 `997ef4eadb394683d5e977251af5c6b4a5677f9b`，原引擎源码已冻结，可独立复读。

实际 48 次工具调用，16 次受理行动（含 1 次 `action_contract` 拒绝）、3 次真实求解，complete=true、needs_review；无维护者中途干预，未执行参考脚本。

状态为 **EXECUTED_TASK_COMPLETE_WITH_PROTOCOL_DEVIATIONS**：Agent 读取了包含预期行为的公开 native handoff 文档，使用过 `/tmp` 中间输出及行动副本，另有一次 observe 把 session ID 当路径的失败。完整轨迹和临时文件副本保留。不得称无辅助成绩、盲测或迁移能力；本轮不重跑模型挑选更好结果。

## 证据、未完成项

原生通过包：`COMACBench-Native-Local-2026-10-02/native-acceptance-05.zip`。
ZIP SHA-256：`51261c21dbca79bc09eae8ace1d196a1482d28f494508aee66aa6cb85f6daea9`。
manifest SHA-256：`edeb522b57305f938ac5a25794134c6b729c7c133f5f703dc100ed3f85beb49b`。
完整本机回传包另包含初始现场、前四次验收、所有失败现场、原始 INP/DAT/日志、冻结源码、独立审计和真实 Agent 轨迹；原始证据未上传 GitHub。

浏览器视觉验收 **BLOCKED**：工具安全策略拒绝 `file://`，未绕过。HTML 内容已核查，仍需人工打开三份报告。
POSIX 正常退出/超时进程测试通过；Windows 本机 native / 超时实测 **NOT_RUN**（线上控制测试另记）。
完整仓库全量测试 / wheel / 离线部署 **NOT_RUN**；工程批准 **NOT_RUN**。

版本退出约定参考 [CalculiX.c](https://github.com/Dhondtguido/CalculiX/blob/master/src/CalculiX.c) 与 [stop.f](https://github.com/Dhondtguido/CalculiX/blob/master/src/stop.f)，并有本机版本探测原始日志。这里只验证可信本地固定线性静力校准，不代表应力、疲劳、网格收敛或型号工程放行。

## 保留的失败与运行顺序

1. native-acceptance-01：维护者传入缩写 HEAD，严格身份检查拒绝；0 求解。
2. native-acceptance-02：106 项原始专项中 103 passed、2 failed、1 skipped；macOS 外部目录链接误拒，0 求解。
3. native-acceptance-03：112 项中 111 passed、1 skipped；三流程 8 次求解成功，最终篡改 CLI 错误退出码使验收 BLOCKED。
4. native-acceptance-04：113 项中 112 passed、1 skipped；8 次真实求解，完整 PASS；随后执行唯一 Agent 试验。
5. native-acceptance-05：公开行动格式修复后，以新输出目录重跑，114 项中 113 passed、1 skipped；8 次真实求解，完整 PASS。

本轮合计参考/负例 24 次真实求解，加唯一 Agent 的 3 次，共 27 次；版本探测另记，不计为 solver request。
测试夹具中的合成 DAT/进程 double 没有计入真实求解数。两个 CLI 修复单测中间失败日志也全部保留。
