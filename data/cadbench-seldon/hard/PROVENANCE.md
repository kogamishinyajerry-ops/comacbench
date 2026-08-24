# PROVENANCE — cadbench_seldon.hard（Seldon CADBench-Hard 公开子集镜像）

> 镜像：2026-08-24。来源 https://huggingface.co/datasets/Seldon-Technologies/CADBench-Hard
> （commit e68ec13a14cd1f88932db5d2a568d8a85695c8ad，lastModified 2026-08-21）。
> 用户裁决路径 A：registry 收录 proposed（blocked），镜像公开子集留弹药，不排期集成。

## 1. 镜像内容（88 文件，~7.3MB）

- `tasks/<task_id>/task.md`（43 题：jaw 分章装配建模系列 26 + j4/j5 多阶段构建 7 + proc 草图程序 5 + jaw_se 轴系 5）
  与 `tasks/<task_id>/answer.f3d`（Autodesk Fusion 私有二进制参考工件）
- `manifest.csv`（官方清单：task_id/difficulty/title/artifact/bytes/sha256）+ `README.md`
- `sha256.txt`（本镜像自算逐文件校验，与官方 manifest 的 answer sha256 逐一核对一致）

难度分布（官方 manifest）：hard 35 / expert 8。变体对（`*_free` 同章自由式、`*_spec`
规格式）共享同一 answer.f3d（字节级相同）。

## 2. 许可

- 任务题面、元数据与 Seldon 自建参考 CAD 工件：**CC-BY-4.0**（卡片明示）——
  许可干净，镜像与改编（含 attribution）均允许； Autodesk Fusion 商标归 Autodesk。
- license-notes.md 已记录。

## 3. 为何不能集成（三重阻塞，2026-08-24 核验）

1. **任务形态与 adapter 不匹配**：题面明令 *"Using only Autodesk Fusion's visible
   user interface... Do not use scripts, add-ins, the Fusion API, a terminal, or
   another CAD program"*——纯 GUI/computer-use 操作基准（tags: gui-agents /
   computer-use / autodesk-fusion）。我们五类 adapter（qa_grounded/code_exec/
   simulation_agent/design_artifact/field_prediction）无一匹配；「写 CadQuery 脚本」
   恰是它禁止测的能力。
2. **环境缺失**：Autodesk Fusion 不在 dev 层（未安装）也不在 intranet 层（内网 CAD
   栈为 CATIA）；Seldon 沙箱环境需私下联系（"please reach out"）。
3. **判分与输入态均不可本地复现**：官方 verifier 未随数据集发布；任务「starting
   from the supplied body」——**种子文档也不在数据集内**（属沙箱）；answer.f3d 为
   Fusion 私有格式，无 Fusion 无法导出/解析，连 cadgen 式自建几何判分（体积/包围盒）
   都被格式挡死。

结论：与 engdesign.open 同为「官方判分不可本地复现」模式且更严（输入态亦缺）——
**直接集成不可行**，收录为 proposed（blocked）。

## 4. 解阻条件（任一满足后重审）

1. Seldon 公开 verifier + 种子文档 + 沙箱（或可本地部署的 Fusion 批处理通道）；
2. 出现合法的 f3d→STEP 转换通道（Fusion 导出或官方 API），使自建几何判分可行——
   仍需第六类 computer_use adapter 与 GUI agent runner（重大 scope 扩张，需立项）；
3. 上游发布脚本/API 版任务变体（若发生则与现有 design_artifact 协议直接兼容）。

## 5. 与既有条目的关系

- `cadbench.cadquery`（anniedoris/CADBench，deferred）是**另一个项目**：CadQuery
  代码生成基准（MIT 代码/数据混合许可，needs-per-task-audit）——两者仅同名，
  来源、任务形态、许可结构均不同，各自独立条目。
- cad_geometry 维参照：cadgen（integrated，CadQuery 脚本协议）测「参数化 CAD 脚本」；
  本数据集测「商业 CAD GUI 操作」——不同能力轴，未来若解阻属**新增子轴**而非替代。

## 6. 复现

```bash
# 镜像来源（只读）：
curl -sL https://huggingface.co/api/datasets/Seldon-Technologies/CADBench-Hard/tree/main
# 校验：data/cadbench-seldon/hard/sha256.txt vs 官方 manifest.csv answer 列
```
