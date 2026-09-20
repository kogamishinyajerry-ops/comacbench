# B05 输入契约与 GLM-5.3-Flash 接入

日期：2026-09-06。B02/B04 的身份协议、B03 的表格判分继续生效。

修订题的 `changed_params` 使用题面映射表中的固定 JSON 键，仅输出发生变化的参数；
`old` / `new` 保留原数值。公开题和隐藏题共用生成器。
更新公开题面及其 SHA256，隐藏池 `answers.b64` 仅刷新题面哈希，参考答案与 exact_keys 不变。

`formula_cell` 在校验原题面哈希后，由 runner 加入输入文件说明：
只列 `input.assets` 实际暂存的 basename，明确模型脚本自行读取输入并保存 `output.xlsx`。
不暴露 golden/oracle 的文件路径或内容。说明参与有效题面哈希和复跑身份，位于可选 scaffold 之后。
现有题目文件、输入工作簿、参考工作簿、权重和判分逻辑不变。

## GLM-5.3-Flash

复用现有 `glm` provider，通过 `--model glm-5.3-flash` 显式选择。
`GLM_API_KEY` 由环境变量注入，不写入仓库。`GLM_BASE_URL` 使用
`https://open.bigmodel.cn/api/coding/paas/v4`。
保留原 `glm` 默认模型，其他适配器已有相同的 `--model` 接口。

```sh
.venv/bin/python -m runners.qa_grounded \
  --tasks tasks/awcom.compliance --out report/my-glm53flash-run \
  --provider glm --model glm-5.3-flash --seed 20260905 --limit 2 --resume
```

现有 GLM 预设为 temperature=0、thinking enabled、max_tokens=32768。
max_tokens 是单次生成长度上限；本轮没有费用、总 token 或请求次数预算上限。
不因得分不理想重试，仍保留 provider 对解析失败的原有有限重试。

官方模型名与端点依据：[智谱模型切换指南](https://docs.bigmodel.cn/cn/coding-plan/latest-model)。
本项目接入范围是本轮文本与代码任务；本轮不验证该模型的多模态能力。

## 验收

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python report/2026-09-06-b05-live/run_experiment.py --prepare
.venv/bin/python report/2026-09-06-b05-live/run_experiment.py --execute minimax
.venv/bin/python report/2026-09-06-b05-live/run_experiment.py --execute glm
```

prepare 只能对未冻结目录执行一次。源文件变化必须新建实验目录。
相同 8 道题、seed=20260905、H0：MiniMax 设置保持上轮一致；GLM 使用原生预设。
两个模型的生成长度和思考设置不同，本轮不作模型排名。
每组验证相同身份复用、错误 seed 拒绝、隐藏题脱敏，并保留旧实验文件字节。

本次 GLM 初次实验最后一题发生 600 秒传输超时，原记录保持不变。
`report/2026-09-06-b05-live/recover_glm.py` 在独立目录原样继承 7 份已完成结果，
核验身份后仅续跑缺失题；等待上限为 1800 秒，首次续跑的模型参数和请求体不变。
解析失败仍遵循原 provider 重试策略。
该恢复脚本及其协议单独记录哈希，完成后的复核应使用恢复目录。
