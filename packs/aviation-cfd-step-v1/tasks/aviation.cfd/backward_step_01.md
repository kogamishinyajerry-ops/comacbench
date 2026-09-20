# 后向台阶：交付一个可复现的原生 CFD 算例

你是仿真 agent。输出一份 Python 脚本，只在当前工作目录生成 case/ 下的八份原生 OpenFOAM 输入文件。平台执行你的脚本一次，然后依次执行 blockMesh、checkMesh、simpleFoam，保管原始日志和场并计算分数。无需你安装、调用或模拟求解器。

工况：二维不可压、定常层流，h=0.01 m，入口平均速度 1 m/s，nu=2e-4 m²/s；Re=Um*(2h)/nu=100。上游 x=-5h..0、y=h..2h，下游 x=0..30h、y=0..2h，z=0..h 单层空边界。入口为充分发展抛物线 u=6η(1-η)，η=(y-h)/h；v=w=0。出口零压力，固壁无滑移。

平台采用 OpenFOAM Foundation 10。随题交付 templates/ 八份可运行输入，它们同时定义本版支持的有限输入方言：注释、空白及可解析数值表示可变化；可以调整三个 hex 块的单元数量（每块 nx≤400、ny≤100、nz=1）并相应更新入口面速度；endTime 在 1..3000。其他几何、拓扑、grading、物理参数、边界类型、离散和求解设置须保持模板语义。fvSchemes 除注释和空白外保持原样。不得加入新字典关键字、include、宏替换、动态代码、库加载或 function objects。平台会独立注入壁面剪切场输出。模板既是公开材料，也是可选起点；本题评测的是该受限工程流程，不是任意 CFD 建模。

网格至少 6100 个单元；下游 0..6h 的底壁面长≤0.101h，底壁第一层单元高度≤0.03h。入口非均匀速度必须按实际生成网格的面顺序填写。固定每 100 次迭代保存；若有收敛退出，末时刻场也需可读。

工程门槛：原生求解正常退出，p 初始残差≤1e-5、Ux/Uy≤1e-6，且各自较最初十次中的最大值下降至少四个数量级；需要 SIMPLE 收敛声明。最终 phi 的边界相对净通量误差≤1e-4，壁面无泄漏，入口流量对应 Um。平台从下游底壁（排除竖直台阶）原生 wallShearStress 的 -x 分量寻找首次负到正零点并线性插值；末两保存场的再附着长度相对变化≤1%。参考 2.922h，相对容差 10%，任何工程门槛或参考带失败总分为 0。

仅交付 case/0/U、case/0/p、case/constant/transportProperties、case/constant/turbulenceProperties、case/system/blockMeshDict、case/system/controlDict、case/system/fvSchemes、case/system/fvSolution。不能交付自报 QoI、预制时间目录、polyMesh、日志、Allrun 或符号链接。不要在求解后重新组装证据。受测脚本在本地受信环境执行，不是操作系统级隔离。

参考及边界：Erturk 2008 DOI 10.1016/j.compfluid.2007.09.003，表 5 Re=100 的 X1/h=2.922；论文域和网格更精细。本包是短域、基础网格的受限验证，尚未完成网格/域长度收敛研究，不代表飞机级工程接受。
