# Structures 维解零：calculix.fea_basic 集成报告（2026-08-24）

> 背景：九维中 structures 是唯一零覆盖轴（simjeb 卡 ANSYS MAPDL 商业栈，engdesign 卡
> 官方判分脚本）。本报告记录以开源 **CalculiX ccx 2.23**（brew，GPL-2.0）自建
> `calculix.fea_basic` 并当日完成全链（任务生成 → gold 锁定 → oracle/stub 自检 →
> 固定对双基线）的过程与读数。registry 19→**20 integrated**，任务 2403→**2424**。

## 1. 接入概览

| 项 | 值 |
| --- | --- |
| registry_id | calculix.fea_basic（order 12b，batch-3，confirmed-selfbuilt） |
| 协议 | ccx_fea：模型写 make_case.py 生成 `model.inp`（不执行求解器）→ runner 跑 `ccx -i model` → 解析 `.dat` 数值判分 |
| 执行后端 | `runners/solvers/calculix.py`（CCX_BIN 可覆写，进程组超时杀） |
| 任务集 | 5 族 21 题（生成器 `runners/gen_tasks_ccxfea.py`，幂等确定性） |
| 容差 | 静力/L 支架 5%、模态 3%、屈曲 5%（题面钉死 C3D20 + 最小网格 16/4/2，离散化差进容差带） |
| 判分 | `grader.extract` 四类抽值（max_abs_udof / sum_rf / eigen_freq / buckle_factor）对 gold 相对误差 |

## 2. 任务族与 gold 交叉验证

| 族 | 题数 | 分析 | 解析互证（gold vs 解析） |
| --- | --- | --- | --- |
| cb 悬臂静力 | 5 | *STATIC | δ=PL³/3EI 偏差 0.03%~0.79%；ΣRF2=-P 偏差 0.00% |
| ssb 简支中载 | 4 | *STATIC | δ=PL³/48EI 偏差 0.62%~2.16%（剪切效应，方向符合理论）；支反力 P/2 偏差 0.00% |
| modal 悬臂模态 | 4 | *FREQUENCY | EB 弱轴 f1 偏差 0.33%~0.51%、强轴 f2 0.01%~0.29% |
| bkl 悬臂屈曲 | 4 | *BUCKLE | 欧拉 Pcr=π²EI/4L² 弱轴 0.31%~0.51%、强轴 0.00%~0.35% |
| lb L 支架 | 4 | *STATIC | 无解析参照（静不定）；gold=ccx 参考网格自洽；呼应 simjeb 支架域/cadgen L 族 |

## 3. 自检与基线

| provider | 均分 | 满分 | gate | 失败模式分布 |
| --- | --- | --- | --- | --- |
| stub | 0.0 | — | 0/21 | missing_output×21（地板） |
| oracle | **1.0000** | 21/21 | 21/21 | max_rel_err=0.00e+00（gold 逐字节复现，判分管线双向验证） |
| minimax-m3 | **0.2381** | 3/21 | 7/21 | simulation_failed×7, code_not_executable×6, timeout×1 |
| glm-5.3 | **0.3810** | 5/21 | 11/21 | simulation_failed×6, code_not_executable×3, timeout×1 |

族级画像：

| 族 | M3 | GLM-5.3 | 读数 |
| --- | --- | --- | --- |
| modal | **0.750** | 0.625 | 两家最强族——*FREQUENCY 无载荷施加语义，只剩网格+密度纪律 |
| lb | 0.125 | **0.500** | GLM 的 L 域网格生成显著更强 |
| cb | 0.100 | 0.300 | 载荷均布施加（ΣFy 契约）是主要失分点 |
| ssb | 0.250 | 0.250 | knife-edge RBC 语义两家同弱 |
| bk | 0.000 | 0.250 | *BUCKLE + 单位参考载荷契约最难 |

## 4. 读数（structures 维首次能力画像）

1. **正落区分带**：0.24/0.38——无饱和锚（gtm-v1 教训）也无全灭（foam/pycycle 模式），
   两模型差异来自 deck 可写率（gate 11 vs 7）而非过 gate 后精度；
2. **「写得完 INP」≠「写得对物理」**：过 gate 但 physics=0 的题全部为真实语义错误——
   M3 ssb_01 支反力 411 vs 500 N（-17.8%，端面全固支吞掉弯矩，knife-edge 语义错）、
   GLM cb_05 反力 1220 vs 1500 N（载荷施加偏差）、GLM md_02 f1=f2=0 Hz（约束缺失
   刚体模态）、GLM bk_04 因子高 21.9%（BC 偏刚）——**反力校验键独立捕获载荷路径
   错误**，与位移键互为正交证据；
3. **16 项/行纪律是真实的语料外陷阱**：屈曲族 M3 首败即 `*ERROR in splitline`
   （id+16 节点写满一行，超限 1 项）——题面明示仍违反，与 foam 的 `source` bashism
   同类的「文档纪律遵循力」信号；
4. **对 harness（H2 脚手架）的预期**：pycycle 式「知识注入 0→1」机会明确——
   CalculiX 方言在两家语料中均属稀缺（对照 pycycle 双模型全灭），蒸馏
   scaffold（INP 骨架 + 折行纪律 + 集合名契约）是下一个高价值臂。

## 5. 工程记录（当日踩坑，全数入 PROVENANCE/题面纪律）

- C3D20 节点序 13-16/17-20 两组中点易颠倒 → `nonpositive jacobian`；
- 连接表/NSET 行 16 项/行上限 → `*ERROR in splitline`；
- `.dat` 位移/反力块标题后有空行；模态表第 4 列才是 Hz（第 5 列虚部）；
  屈曲表头跨两行（`MODE NO BUCKLING`/`FACTOR`）；
- 解析互证修正过一次列位 bug（eigen parts[4]→parts[3]），gold 全零暴露——
  交叉验证表本身就是判分器的判分器。

## 6. 产物清单

```
runners/solvers/calculix.py            执行后端 + .dat 解析（四类抽值）
runners/simulation_agent.py            ccx_fea 分支（gtm 同构判分 + foam 同构两段执行）
runners/gen_tasks_ccxfea.py            任务/gold 生成器（幂等）
tasks/calculix.fea_basic/              21 yaml + 21 md
data/calculix/fea_basic/               gold/ 21 脚本 + PROVENANCE.md
results/calculix.fea_basic/2026-08-24/ {stub, oracle, minimax-m3, glm-5.3}
registry/registry.yaml                 entries 40，calculix.fea_basic integrated
env-matrix.md                          calculix_native 环境类
```
