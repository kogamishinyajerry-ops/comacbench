# CFD 后向台阶基础评测包

一题 Re=100、二维层流、原生 OpenFOAM Foundation 10 算例。工程师 agent 返回生成八份 `case/` 输入的 Python 脚本，平台独立执行网格、检查、求解与 QoI 降算。

- `templates/`：明确交给受测 agent 的有限输入方言和起点。可调整允许的网格数量、入口面剖面和迭代上限，其他设置语义固定。
- `tasks/aviation.cfd/`：完整题面、来源、单位、阈值和需求追踪。
- `private/`：校准参考及 6 个故障控制，不能作为受测 agent 公开材料。
- `LICENSE`：上游模板的 MIT 声明。

```bash
.venv/bin/python -m comacbench validate packs/aviation-cfd-step-v1
.venv/bin/python -m comacbench run packs/aviation-cfd-step-v1 --agent examples/agents/cfd-reference.json --out ./cfd-interface-01
.venv/bin/python -m comacbench calibrate packs/aviation-cfd-step-v1 --out ./cfd-calibration-01
```

原生输入改编自 `GLM-CFD-Benchmark` b26799e；变化为 Foundation 10 的 simpleGrading、静态非均匀入口、每 100 次保存与高精度 ASCII 输出。壁面剪切 function object 由平台注入，受测脚本不得提供。参考来源为 Erturk 2008 表 5，DOI https://doi.org/10.1016/j.compfluid.2007.09.003；Re 以平均速度及两倍入口高度定义。该论文使用更长域与细网格，本包 10% 相对带仅为受限短域基础题，尚需网格/域长度敏感性研究。

全部六阶段通过并落在参考带才为满分。错误负例必须命中指定诊断，退出 0 或自报 2.922 不能代表通过。参考接口程序有答案，只是接口证明。公开开发题、参考/负例校准、真实模型成绩与飞机工程接受分别解释，不自动发布材料或安装 DSH 配置。
