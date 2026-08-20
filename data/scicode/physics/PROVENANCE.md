# SciCode 数据镜像溯源（PROVENANCE）

> assets_revision: `scicode@e3158ea+hf_v1+test_data_h5_20240712`
> 镜像日期: 2026-08-19 · 镜像执行: M2 会话（dev 终端）

## 镜像内容

| 文件 | 来源 | sha256 |
| --- | --- | --- |
| `problems_test.jsonl` | HF `SciCode1/SciCode`（65 主问题/288 子问题） | `38797fef…3a6edf81d` |
| `problems_dev.jsonl` | HF `SciCode1/SciCode`（15 主问题/50 子问题，含公开 gold 解） | `193968af…d2fc4f7b` |
| `test_data.h5` | 官方 Google Drive `test_data.h5`（README 指定，338 步数值期望值，1.05GB） | `48b0272a…41b890` |
| `LICENSE.apache-2.0` | GitHub `scicode-bench/SciCode` @ `e3158ea` LICENSE | 见文件 |
| `subject_map.md` / `subject_map.json` / `m2_subset_ids.json` | 本 harness 生成（AI 辅助标注，待人工复核） | 见文件 |

## 许可证据链（先许可证后镜像，2026-08-19 核验）

1. GitHub 仓库 `scicode-bench/SciCode` @ `e3158ea0`：LICENSE = **Apache License 2.0**；
2. HF 数据集卡片 `SciCode1/SciCode`：`license: apache-2.0`（数据与代码同许可）；
3. 数值期望文件 test_data.h5：仓库 README 官方下载链接（Google Drive），随仓库 Apache-2.0 分发。

结论：`license_status: confirmed-repo`（Apache-2.0）成立，镜像放行。

## 数据校验（镜像时核验）

- 80 主问题 = test 65 + dev 15；341 子问题步 = 288(test) + 50(dev) + 3 特判步
  （13.6/62.1/76.3 官方走 txt 特判，本 harness 不判分）；
- test_data.h5 含 338 个 step 组（每步全部 test case 的期望值），与官方
  `test_generated_code.py` 的取数路径 `process_hdf5_to_tuple(step_id, n)` 一致；
- 判分引用官方语义：模型代码 + h5 targets + 原始 assert 行（np.allclose 等），
  不重写断言。

## 判分管线工程发现（2026-08-19 oracle 自检时定因，影响判分正确性）

1. **case 命名空间语义**：官方把同一步的全部 test case 顺序写进同一脚本文件执行，
   case 之间**变量共享**（如 7.1 case4 引用 case1 的 `image_array`、10.1 case4 引用 `L`）。
   本 harness 最初用每 case 独立命名空间导致 gold 假阴性，已改为官方语义（步内共享）。
2. **官方包引用**：70.6 的 case 显式 `from scicode.compare.cmp import cmp_tuple_or_list`
   （官方环境装 scicode 包）。本 harness vendor 最小 shim（`runners/vendor_shim/scicode/`，
   Apache-2.0 逐行拷贝）。
3. **scipy API 漂移**：数据集 `required_dependencies` 用 `from scipy.integrate import simps`
   （scipy>=1.14 改名 `simpson`，2/52 题受影响）。判分 harness 加可信侧兼容别名。
4. **gold 本身机器计时依赖**（不可修，如实记录）：78.3（混沌摆）gold 用 `time.time()`
   测耗时选最优时间步——不同机器必然复现不出 h5 target（oracle 在本机 0/3）。
5. **退化构型数值漂移**（不可修）：70.8 case4（s13=0）gold 输出与 h5 target 最大差
   1.8e-4（物理一致，超 allclose 默认容差）——target 生成环境的 numpy/scipy 与本机不同。
6. oracle 自检终值：**dev 12 题中 10 满分**；p078/p070 两题为上述 4/5 类环境依赖偏差
   （gold-vs-target，非判分器 bug）。test split 无 gold 源（官方保留），oracle 不可用于
   test 40 题——判分器正确性由 dev 10/12 + stub 全量行为校验背书。

## M2 子集（physics + 数值计算）

- 划定规则与逐题映射：`subject_map.md`（52 题 = Physics 37 + NLA 8 + CompMech 5
  + 量子数值边界对 {15,52} 计 2；test 40 / dev 12；209 步，可判分 207 步）；
- subject 映射为 AI 辅助标注（上游无逐题公开映射），计数校验和除内部拆分项外
  全部对齐论文表 1，待人工复核（复核敏感项：35/39 若改判 Optics 子集 +2）。

## 重取方式

```bash
curl -sL "https://huggingface.co/datasets/SciCode1/SciCode/resolve/main/problems_test.jsonl" -o problems_test.jsonl
curl -sL "https://huggingface.co/datasets/SciCode1/SciCode/resolve/main/problems_dev.jsonl" -o problems_dev.jsonl
# test_data.h5: pip install gdown && gdown 17G_k65N_6yFFZ2O-jQH00Lh6iaw3z-AW -O test_data.h5
shasum -a 256 problems_*.jsonl test_data.h5   # 对照上表，不一致 => 新评测周期
```
