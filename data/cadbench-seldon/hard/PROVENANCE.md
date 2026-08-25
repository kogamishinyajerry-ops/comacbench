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

## 3. 为何不能集成（阻塞重评：2026-08-25 Fusion 装机后）

> 2026-08-25 更新：dev 终端装 Autodesk Fusion（webdeploy 生产通道，进程核验）——
> 环境阻塞解除一项，GT 私有格式阻塞有了解法；种子文档阻塞经题面审计精确量化。

1. **任务形态与 adapter 不匹配**（仍阻塞）：题面明令 *"Using only Autodesk Fusion's
   visible user interface... Do not use scripts, add-ins, the Fusion API"*——纯
   GUI/computer-use 操作基准。computer_use 第六类 adapter 未立项。
2. **种子文档缺失**（仍阻塞，已量化）：**38/43 题**（jaw×26 / j4×5 / j5×3 / se×5 中
   的实体建模题）题面为 "Starting from the supplied tapered housing" 等——种子文档
   属 Seldon 沙箱，不随数据集发布。**但 5 道 proc 草图题（connected_lines×1 /
   polygon×1 / spline_profile×3）明确空文档起步**（"contains only the root
   component and Origin"），题面给出全部坐标——**该 5 题不依赖种子，完全可跑**。
3. ~~环境缺失~~ → **已解除**（2026-08-25 Fusion dev 层就位）。
4. ~~f3d 不可解析~~ → **有解法**：判分方不受题面「禁脚本」约束（那约束被测
   agent）；`tools/fusion_export_gt.py`（Fusion 批处理脚本，人在 Fusion 里运行一次）
   把 answer.f3d 去重导出为 step_gt/*.step（实体）+ sketch_gt/*.json（草图几何），
   转为本地可判分 GT——CC-BY-4.0 允许带署名衍生。verifier 仍私有，但几何级自建
   判分（体积/包围盒/草图线段比对，cadgen 同款）从此可行。

**当前状态**：仍为 proposed（computer_use adapter 未立项 + 38/43 题种子私有），
但存在两条可走的窄路（见 §4）。

## 4. 可走的窄路（2026-08-25 重评）

1. **GT 转换（前置，无条件做）**：`tools/fusion_export_gt.py` 在 Fusion 里跑一次，
   得到 43 题 step_gt/sketch_gt——无论走哪条路，开放格式 GT 都是地基；
2. **窄路 A（proc 5 题自建改编，推荐可评估）**：5 道草图题空文档起步且坐标全给——
   按本仓库协议改编（模型输出几何构造，我们草图线段级判分 vs sketch_gt），成为
   cad_geometry 维 2D 草图子轴首批任务（同 cadgen 对 CADGenBench 的改编 DNA，
   CC-BY-4.0 带署名衍生）；
3. **窄路 B（38 题等上游）**：Seldon 公开种子+verifier+沙箱；或上游出脚本/API 版
   变体；或 computer_use adapter 立项（GUI agent 整条链，周级 scope）。

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
