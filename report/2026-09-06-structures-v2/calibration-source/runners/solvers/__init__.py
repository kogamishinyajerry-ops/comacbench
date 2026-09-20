# runners/solvers — 求解器调用层（与 grader 解耦，可替换）
#
# 硬性要求（kickoff）：grader 只认 result.json + 残差/守恒/目标量，不绑求解器 CLI；
# 求解器调用单独成层。dev 终端 = openfoam.py（docker v10）；intranet 移植时
# 增加 fluent.py（journal 批处理）/ starccm.py（macro），adapter 与任务 YAML 不变。
#
# 接口（所有实现必须满足）：
#   class Solver:
#       name: str
#       def run_case(self, case_dir: Path, timeout_s: float) -> RunResult
#           # 在 case_dir 内执行算例（Allrun 或等价入口），返回统一结果
#       def execution_ok(self, case_dir: Path) -> bool
#           # 求解「跑完」判据（openfoam: log.*Foam 倒数第二行 == "End"；
#           # fluent: journal 退出码 + 收敛文件；实现自定，语义对齐）
#
# RunResult: {ok, exit, stdout, stderr, duration_s, timeout, last_time}
# 场读取（NMSE 判分）不在此层——属于 grader 侧（field_reader）。
