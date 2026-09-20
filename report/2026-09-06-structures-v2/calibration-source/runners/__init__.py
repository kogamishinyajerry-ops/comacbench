# benchmarks/runners — 标准五类 adapter 运行器（v0.1）
#
# 规则（见 ../adapters/README.md）：
# 1. 所有基准只允许用五类标准 adapter，禁止为单个 benchmark fork runner；
# 2. 任务全部由 YAML 驱动（契约见 ../contracts/task.example.yaml）；
# 3. grader 只认 result.json 等标准产物，不绑定求解器/模型 CLI；
# 4. 求解器/模型调用单独成层（providers.py / 将来的 solver 层），可替换。
#
# 当前实现：
#   common.py          任务 YAML 校验、environment_digest、result.json 构造、run_manifest
#   providers.py       模型调用层（stub / oracle / openai_compat 占位）
#   qa_grounded.py     qa_grounded adapter + CLI
#   gen_tasks_cfdquery.py  从镜像数据生成 90 个任务 YAML + 题面 prompt 文件
