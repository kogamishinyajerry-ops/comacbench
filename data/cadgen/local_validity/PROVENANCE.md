# cadgen.local_validity 数据来源与判分边界（PROVENANCE）

- 定位：**自建参数化任务**（受 CADGenBench「本地可复现子集」定位启发；
  registry `cadgen.local_validity`，adapter `design_artifact`，adapters/README.md §4）。
- **未镜像其 ODC-BY 输入**：题面/尺寸全部由 runners/gen_tasks_cadgen.py 的
  参数化族生成，不使用 CADGenBench 官方 text+image 输入与输入制品。
- **未用其私有 GT**：CADGenBench 服务端相似度分数与私有 ground truth
  （cadgenbench-data-gt 空仓）不可得也不纳入——私有 GT 相似度分数不得混入本地分数。
- **判分 100% 本地可复现**：
  - STEP 可解析（STEPControl_Reader）+ B-Rep 有效（BRepCheck_Analyzer）；
  - 体积/包络（GProp / Bnd_Box）对 gold 预计算参考的相对误差（1%）；
  - 接口几何（TopExp 遍历圆柱面数/半径，±1%）与总面数（精确）；
  - 生成代码可重复执行复现同一制品（体积/包围盒 1e-6 相对一致）。
- 环境：仓库根 `.venv-cad`（Python 3.12.13 + cadquery 2.8.0 + OCP wheel），
  assets_revision `cadgen-local@selfbuilt-2026-08-21+cadquery2.8.0`。
- gold 全量预计算锁定：每题 `gold/<tid>.py` 在干净目录执行导出 part.step，
  测量结果（与判分器同一实现 `runners/design_artifact.measure_step`）落
  `references/<tid>.json` 并内嵌任务 YAML `reference.values`。
- 生成器幂等校验：`.venv-cad/bin/python -m runners.gen_tasks_cadgen --check`。

## 任务族（6 族 22 题，同族变体体积互差 >2%）

| 族 | 题数 | 参数 |
| --- | --- | --- |
| 圆法兰+螺栓孔环 cg_flange_* | 4 | plate_d, thickness, n_holes, hole_d, pcd |
| 矩形板+四角孔+边倒圆 cg_plate_* | 4 | L, W, t, hole_d, corner_r, hole_inset |
| L 角支架 cg_lbracket_* | 4 | leg_x, H, t, width, fillet_r, hole_d |
| 套筒/环形件 cg_sleeve_* | 3 | OD, ID, h |
| 阶梯轴+中心孔 cg_shaft_* | 4 | segments[(d,l)x3], bore_d |
| 带凸台底板 cg_bossplate_* | 3 | L, W, t, boss_d, boss_h, hole_d, hole_inset |

## 负路径验证（2026-08-21，父会话补）

- `code_not_executable`：stub 全 22 题 gate=0（地板均分 0.0）；
- `nondeterministic_artifact`：pid 驱动随机尺寸（`os.getpid()%500`）的坏代码
  3/3 触发 gate 失败——检测逻辑无 bug。
- **平台事实（测试方法论，后人勿再踩）**：本机（macOS + CPython 3.12）沙箱内
  `time.time_ns()` 低三位恒为 0（毫秒级时钟粒度），`time_ns()%N` 小 N
  「随机」代码实际为确定代码——曾致一轮误判 gate 漏检。验证非确定性检测须用
  pid 等必然不同的差异源。
