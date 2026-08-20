# SciCode subject 映射（M2 子集划定依据）
#
> 性质：**AI 辅助标注（题名+题面描述驱动），待人工复核**。
> 上游未发布逐题 subfield 映射（HF 数据集、论文 LaTeX v1、官网均只有 16 子域计数表），
> registry 风险条目 "子集划定需人工标注 subject 映射" 即指此项工作。
>
> 标注方法：按题名/题面描述归入论文表 1 的 5 学科 16 子域；以论文逐子域计数
> （NLA 8 / CompMech 5 / CompFin 1 / CMP 13 / Optics 10 / QI 6 / CompPhys 5 /
>  Astro 2 / Particle 1 / QC 5 / CompChem 3 / Eco 6 / Biochem 1 / Genetics 1 /
>  Semi 7 / MolMod 6 = 80）做硬校验和；标注置信度逐题标注。
>
> 已知偏差（如实记录，均不影响 M2 子集边界——涉及题目全部在子集内或子集外两侧稳定）：
> 1. Biology 计数只找到 7 道生物题（论文计 8）：Eco/Biochem/Genetics 内部归属
#    存在 1 题不确定（44/76 的三槽两题），但所有候选均在子集外；
# 2. {15 CN-TDSE, 52 Shooting_H_atom} 一题属 CompPhys 一题属 QC 的拆分不可判：
#    按 registry「物理与数值计算相关」口径两题均纳入子集（见 m2_subset 规则）。

```json
{
  "1":  {"subfield": "Numerical linear Algebra", "conf": "firm",   "why": "共轭梯度法"},
  "2":  {"subfield": "Optics", "conf": "firm", "why": "高斯光束聚焦"},
  "3":  {"subfield": "Numerical linear Algebra", "conf": "firm", "why": "Gauss-Seidel 迭代"},
  "4":  {"subfield": "Numerical linear Algebra", "conf": "firm", "why": "不完全 Cholesky 预条件"},
  "5":  {"subfield": "Numerical linear Algebra", "conf": "firm", "why": "Lanczos"},
  "6":  {"subfield": "Optics", "conf": "firm", "why": "激光空间滤波（傅里叶光学）I"},
  "7":  {"subfield": "Optics", "conf": "firm", "why": "激光空间滤波 II"},
  "8":  {"subfield": "Optics", "conf": "firm", "why": "激光空间滤波 III"},
  "9":  {"subfield": "Numerical linear Algebra", "conf": "firm", "why": "加权 Jacobi"},
  "10": {"subfield": "Condensed Matter Physics", "conf": "firm", "why": "Ewald 求和（周期库仑）"},
  "11": {"subfield": "Quantum Information/Computing", "conf": "firm", "why": "GADC 纠缠"},
  "12": {"subfield": "Quantum Chemistry", "conf": "medium", "why": "SCF 自洽场 DFT（QC 方法簇；亦可视作 CMP 电子结构）"},
  "13": {"subfield": "Computational Physics", "conf": "medium", "why": "3+1 分解 Maxwell 数值求解"},
  "14": {"subfield": "Optics", "conf": "firm", "why": "光镊布朗运动"},
  "15": {"subfield": "Computational Physics", "conf": "boundary", "why": "TDSE Crank-Nicolson（量子数值；与 52 二选一归 QC，按口径两题均入子集）"},
  "16": {"subfield": "Numerical linear Algebra", "conf": "medium", "why": "Davidson 特征值方法（源自 QC 但题目为纯对称矩阵特征值）"},
  "17": {"subfield": "Computational Mechanics", "conf": "firm", "why": "线性四面体有限元"},
  "18": {"subfield": "Computational Mechanics", "conf": "firm", "why": "NURBS（等几何分析几何）"},
  "19": {"subfield": "Quantum Information/Computing", "conf": "firm", "why": "n-tangle 纠缠度量"},
  "20": {"subfield": "Condensed Matter Physics", "conf": "firm", "why": "声子角动量"},
  "21": {"subfield": "Semiconductor Materials", "conf": "firm", "why": "GaAlAs 带隙/吸收系数"},
  "22": {"subfield": "Optics", "conf": "firm", "why": "光束平移重展开"},
  "23": {"subfield": "Quantum Information/Computing", "conf": "medium", "why": "Blahut-Arimoto 信道容量（经典信道 vs 量子，归 QI 信息论簇）"},
  "24": {"subfield": "Computational Mechanics", "conf": "firm", "why": "Burgers 方程"},
  "25": {"subfield": "Ecology", "conf": "firm", "why": "恒温器消费者-资源模型"},
  "26": {"subfield": "Ecology", "conf": "firm", "why": "连续稀释 CRM"},
  "27": {"subfield": "Semiconductor Materials", "conf": "firm", "why": "高速光电探测器设计权衡"},
  "28": {"subfield": "Optics", "conf": "firm", "why": "高斯光束强度"},
  "29": {"subfield": "Numerical linear Algebra", "conf": "firm", "why": "Gram-Schmidt 正交化"},
  "30": {"subfield": "Quantum Chemistry", "conf": "firm", "why": "氦 Slater-Jastrow 试探波函数"},
  "31": {"subfield": "Numerical linear Algebra", "conf": "medium", "why": "独立成分分析（矩阵分离方法）"},
  "32": {"subfield": "Optics", "conf": "firm", "why": "光镊阵列多粒子动力学"},
  "33": {"subfield": "Condensed Matter Physics", "conf": "firm", "why": "Chern-Haldane 模型相图"},
  "34": {"subfield": "Semiconductor Materials", "conf": "firm", "why": "PN 结能带图"},
  "35": {"subfield": "Semiconductor Materials", "conf": "medium", "why": "量子点吸收谱（半导体纳米结构；亦可视作 Optics）"},
  "36": {"subfield": "Semiconductor Materials", "conf": "firm", "why": "光敏电阻准费米能级"},
  "37": {"subfield": "Optics", "conf": "firm", "why": "球差光线光学"},
  "38": {"subfield": "Condensed Matter Physics", "conf": "firm", "why": "倒格矢"},
  "39": {"subfield": "Semiconductor Materials", "conf": "medium", "why": "DBR 反射谱（半导体微腔镜；亦可视作 Optics）"},
  "40": {"subfield": "Computational Physics", "conf": "firm", "why": "分步算符法 TDSE"},
  "41": {"subfield": "Ecology", "conf": "firm", "why": "连续稀释结构稳定性"},
  "42": {"subfield": "Semiconductor Materials", "conf": "firm", "why": "多量子阱激光器阈值电流"},
  "43": {"subfield": "Optics", "conf": "firm", "why": "双端光纤激光器"},
  "44": {"subfield": "Biochemistry", "conf": "low", "why": "异聚物模板连接/Watson-Crick（预生物化学；Eco/Biochem/Genetics 三槽两题，见偏差 1）"},
  "45": {"subfield": "Computational Mechanics", "conf": "firm", "why": "热传导有限差分"},
  "46": {"subfield": "Quantum Chemistry", "conf": "firm", "why": "氦原子 VMC"},
  "47": {"subfield": "Molecular Modeling", "conf": "medium", "why": "LJ 体系内能（分子模拟簇）"},
  "48": {"subfield": "Semiconductor Materials", "conf": "low", "why": "MEELS 转换（材料表征；亦可视作 MolMod）"},
  "49": {"subfield": "Astrophysics", "conf": "firm", "why": "N 体"},
  "50": {"subfield": "Condensed Matter Physics", "conf": "firm", "why": "复本对称破缺（自旋玻璃）"},
  "51": {"subfield": "Molecular Modeling", "conf": "medium", "why": "LJ 分子动力学示例"},
  "52": {"subfield": "Computational Physics", "conf": "boundary", "why": "氢原子打靶法（量子数值；与 15 二选一归 QC，按口径两题均入子集）"},
  "53": {"subfield": "Ecology", "conf": "firm", "why": "随机 Lotka-Volterra"},
  "54": {"subfield": "Computational Mechanics", "conf": "firm", "why": "SUPG 稳定有限元"},
  "55": {"subfield": "Condensed Matter Physics", "conf": "firm", "why": "Swift-Hohenberg 图样形成"},
  "56": {"subfield": "Ecology", "conf": "firm", "why": "时间生态位"},
  "57": {"subfield": "Computational Physics", "conf": "firm", "why": "谐振子 Numerov 打靶"},
  "58": {"subfield": "Astrophysics", "conf": "firm", "why": "TOV 星"},
  "59": {"subfield": "Quantum Information/Computing", "conf": "firm", "why": "VQE"},
  "60": {"subfield": "Computational Chemistry", "conf": "firm", "why": "Widom 插入化学势"},
  "61": {"subfield": "Condensed Matter Physics", "conf": "medium", "why": "XRD Bragg 峰标定 I（晶体学）"},
  "62": {"subfield": "Condensed Matter Physics", "conf": "firm", "why": "DMRG"},
  "63": {"subfield": "Computational Finance", "conf": "firm", "why": "股票期权定价"},
  "64": {"subfield": "Molecular Modeling", "conf": "firm", "why": "巨正则 Monte Carlo"},
  "65": {"subfield": "Quantum Information/Computing", "conf": "firm", "why": "GHZ 协议保真度"},
  "66": {"subfield": "Computational Chemistry", "conf": "medium", "why": "Kolmogorov-Crespi 层间势"},
  "67": {"subfield": "Condensed Matter Physics", "conf": "firm", "why": "层状电子气 RPA Dyson（体）"},
  "68": {"subfield": "Quantum Chemistry", "conf": "firm", "why": "氦原子 DMC"},
  "69": {"subfield": "Condensed Matter Physics", "conf": "firm", "why": "层状电子气 RPA Dyson（半无限）"},
  "70": {"subfield": "Particle Physics", "conf": "firm", "why": "中微子振荡"},
  "71": {"subfield": "Quantum Information/Computing", "conf": "firm", "why": "GADC 相干信息"},
  "72": {"subfield": "Condensed Matter Physics", "conf": "firm", "why": "Ising 模型"},
  "73": {"subfield": "Condensed Matter Physics", "conf": "medium", "why": "XRD Bragg 峰标定 II"},
  "74": {"subfield": "Numerical linear Algebra", "conf": "firm", "why": "Householder QR"},
  "75": {"subfield": "Condensed Matter Physics", "conf": "firm", "why": "石墨烯紧束缚"},
  "76": {"subfield": "Genetics", "conf": "low", "why": "蛋白-DNA PWM 结合（Genetics/Biochem 二选一，见偏差 1）"},
  "77": {"subfield": "Molecular Modeling", "conf": "firm", "why": "Berendsen 恒温器 MD"},
  "78": {"subfield": "Computational Physics", "conf": "firm", "why": "混沌摆动力学"},
  "79": {"subfield": "Molecular Modeling", "conf": "firm", "why": "Nosé-Hoover 链恒温器"},
  "80": {"subfield": "Molecular Modeling", "conf": "firm", "why": "Anderson 恒温器 MD"}
}
```

## 计数校验（与论文表 1 对照）

| 子域 | 论文 | 本映射 | 差异 |
| --- | --- | --- | --- |
| Numerical linear Algebra | 8 | 9 | +1（16 Davidson 与 31 ICA 二选一未定；两题均在子集内，不影响边界） |
| Computational Mechanics | 5 | 5 | ✓ |
| Computational Finance | 1 | 1 | ✓ |
| Condensed Matter Physics | 13 | 13 | ✓ |
| Optics | 10 | 10 | ✓ |
| Quantum Information/Computing | 6 | 6 | ✓ |
| Computational Physics | 5 | 6 | +1（15/52 边界对全归此，见偏差 2） |
| Astrophysics | 2 | 2 | ✓ |
| Particle Physics | 1 | 1 | ✓ |
| Quantum Chemistry | 5 | 4 | −1（对应上两行 +1 的镜像差） |
| Computational Chemistry | 3 | 2 | −1（66 与 47/51 内部拆分未定） |
| Ecology | 6 | 5 | −1（见偏差 1：生物学科总数 7 vs 论文 8） |
| Biochemistry | 1 | 1 | ✓（44，low 置信） |
| Genetics | 1 | 1 | ✓（76，low 置信） |
| Semiconductor Materials | 7 | 7 | ✓（35/39/48 为 medium/low） |
| Molecular Modeling | 6 | 7 | +1（内部拆分未定） |

> 所有计数偏差均由「二选一/三选二」内部拆分引起，合计恒等（+1+1−1−1−1+1 = 0）。
> **M2 子集边界不受任何偏差影响**：候选题的归属摇摆都发生在「子集内↔子集内」
> （NLA↔CompPhys↔QC 的 12/15/16/31/52 量子数值簇，已按 registry 口径全纳入）
> 或「子集外↔子集外」（Eco↔Biochem↔Genetics、Semi↔Optics 的 35/39、MolMod↔CompChem）。
> 35 QD 吸收谱/39 DBR 若人工复核改判 Optics，会使子集 +2 题（记录为复核敏感项）。

## M2 子集规则（m2_subset）

`discipline == Physics` ∪ `subfield ∈ {Numerical linear Algebra, Computational Mechanics}` ∪ `{15, 52}`（量子数值边界对，15 已在 Physics 计数内、52 追加）

= **52 道主问题**（test 40 + dev 12），子问题 209 步（其中 13.6 / 62.1 两步无 h5 数值目标，
官方走 eval/data/*.txt 特判路径，本 harness 排除这两步的判分——有效判分 207 步）。
机器可读版：`subject_map.json`（逐题标注）+ `m2_subset_ids.json`（子集题号）。
