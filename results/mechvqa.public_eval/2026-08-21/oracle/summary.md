# qa_grounded(free_vqa) 结果汇总（provider=oracle, model=n/a, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 180
- gate 通过（非空作答）: 180
- gate 失败（空答=missing_output）: 0（直接 0 分）
- gate 失败原因分布: 无

## 客观层（requirements = 中文感知 Exact/数值容差/F1）

- 满分（归一化精确或数值全命中）: 180/180（accuracy = 1.0000）
- 含部分分的均值: 1.0000（F1 部分分口径）
- 子分适用性: physics=N/A（无证据/拒答层）；objective=N/A；robustness=N/A（样本=1）

## 分层（capability × difficulty）

| capability | difficulty | n | mean |
| --- | --- | --- | --- |
| Judging | Easy | 13 | 1.0000 |
| Judging | Hard | 8 | 1.0000 |
| Judging | Medium | 19 | 1.0000 |
| Reasoning | Easy | 10 | 1.0000 |
| Reasoning | Hard | 15 | 1.0000 |
| Reasoning | Medium | 17 | 1.0000 |
| Recognition | Easy | 68 | 1.0000 |
| Recognition | Hard | 3 | 1.0000 |
| Recognition | Medium | 27 | 1.0000 |

## 每题明细（前 8 字符级截断）

| task | gate | score | parsed |
| --- | --- | --- | --- |
| mechvqa_q001 | 1 | 1.0 | Type BR, compared to Type B, incorporates a spring element i |
| mechvqa_q002 | 1 | 1.0 | Bayonet 通过卡口快速旋转锁定、无螺钉和独立密封件；Thread 采用 G 1 1/4 螺纹，需要 6 颗自攻螺钉 |
| mechvqa_q003 | 1 | 1.0 | 梯形轮廓是两块对称倾斜平面的正投影，对应中间的斜面（楔形）过渡结构。 |
| mechvqa_q004 | 1 | 1.0 | The name of this part is **square nut**. The title block in  |
| mechvqa_q005 | 1 | 1.0 | 图5-229顶尖套零件图的材料栏明确标注的材料代号为 HT200。 |
| mechvqa_q006 | 1 | 1.0 | 零件上槽的深度为 **3 mm**（依据图5‑73的A‑A剖视图中标注的尺寸“3”）。 |
| mechvqa_q007 | 1 | 1.0 | 图5-72（配气盘）和图5-73（配气盘垫）在装配时应采用**粘合剂粘接**的方式。理由如下：
1. **技术要求明确* |
| mechvqa_q008 | 1 | 1.0 | The surface roughness Ra value in the upper left corner loca |
| mechvqa_q009 | 1 | 1.0 | 图5-269弹簧的技术要求中，线径d的数值为0.3 mm。 |
| mechvqa_q010 | 1 | 1.0 | The total thickness of the part can be directly read from th |
| mechvqa_q011 | 1 | 1.0 | 左上角图纸中，压盖零件 A‑A 剖视图标注的直径尺寸为 φ25。 |
| mechvqa_q012 | 1 | 1.0 | 圆柱端长度z的公差范围是 **0.01 ~ 0.017 英寸**。 |
| mechvqa_q013 | 1 | 1.0 | 根据机械图纸及参数表的对应关系，产品规格“256‑56”中的数字含义如下：
- “256”对应尺寸代号 **d**（通常 |
| mechvqa_q014 | 1 | 1.0 | 理想正六边形中，对边宽度 s=a√3、对角宽度 e=2a，因此 e=(2/√3)s≈1.1547s。代入 s=29.67 |
| mechvqa_q015 | 1 | 1.0 | 根据图纸标题栏信息，该零件的标准名称为“小六角螺母（大对边）”。 |
| mechvqa_q016 | 1 | 1.0 | The hexalobular socket nominal diameter e marked in the left |
| mechvqa_q017 | 1 | 1.0 | 该螺柱的螺距P为6毫米。依据图纸中的“尺寸代号‑规格参数”表格以及图形标注“P=6”，均明确指示螺距为6 mm。 |
| mechvqa_q018 | 1 | 1.0 | The specification parameter for pitch P in the parameter tab |
| mechvqa_q019 | 1 | 1.0 | The diagonal width e labeled in the top view of the cross re |
| mechvqa_q020 | 1 | 1.0 | d0的尺寸范围是0.19 ~ 0.25英寸（inch）。依据图纸中的“尺寸代号‑规格参数”表格以及右侧视图的标注（d0  |
| mechvqa_q021 | 1 | 1.0 | According to the parameter table in the drawing, the specifi |
| mechvqa_q022 | 1 | 1.0 | 在技术参数表格中，当d₁为160时，对应的静态载荷（Static load）为 **20000 N**。 |
| mechvqa_q023 | 1 | 1.0 | The minimum length Lmin of the cylindrical pin as annotated  |
| mechvqa_q024 | 1 | 1.0 | 在规格参数表格中，当d₁为42时，名义磁力（与保持盘组合）的数值为80 N。 |
| mechvqa_q025 | 1 | 1.0 | 在中间剖视图中，尺寸标注 d₁ 指的是零件的外圆直径，亦即下部垫圈（或整体外圆柱面）的最大直径。 |
| mechvqa_q026 | 1 | 1.0 | 根据机械图纸参数表，当 l₁=95 时，b₁ 的尺寸为 22。 |
| mechvqa_q027 | 1 | 1.0 | Type A端盖剖视图中标注的“d”尺寸对应参数表中的数值为 **6.5**。 |
| mechvqa_q028 | 1 | 1.0 | According to the technical parameter table at the bottom of  |
| mechvqa_q029 | 1 | 1.0 | 在中间下方的连接件与安装导轨装配视图中，l₅尺寸标注的是左侧端部带螺钉孔的安装导轨/端块的局部水平长度，即从该端块外侧边 |
| mechvqa_q030 | 1 | 1.0 | 根据机械图纸中的参数表格，当 l₁ = 550 时，行程 l₂ 的数值为 **550**。 |
| mechvqa_q031 | 1 | 1.0 | 根据机械图纸底部的参数表，当d₁为40时，d₃的尺寸值为17。 |
| mechvqa_q032 | 1 | 1.0 | 侧视图中标注的英文短语是 “folded out”。 |
| mechvqa_q033 | 1 | 1.0 | 根据机械图纸参数表，M6规格对应的 d₂ 基本尺寸为 **2.7 mm**。 |
| mechvqa_q034 | 1 | 1.0 | 右侧视图中标注的h₅尺寸表示手柄相对主体/铰接座的水平外伸长度，即从手柄座右侧参考线到虚线所示水平手柄末端的距离。该尺寸 |
| mechvqa_q035 | 1 | 1.0 | 右侧主视图中，零件的厚度标注值为**1毫米**。 |
| mechvqa_q036 | 1 | 1.0 | In the parameter table, when d1 is 8, the corresponding thre |
| mechvqa_q037 | 1 | 1.0 | The "Internal hex" labeled in the cross-sectional view corre |
| mechvqa_q038 | 1 | 1.0 | 根据图纸底部的参数表格，当 d₁ 尺寸为 8 mm 时，对应的 l₂ 数值为 8 mm。 |
| mechvqa_q039 | 1 | 1.0 | 根据图纸中的参数表格，当 d₁ 为 B15 时，d₄（Clamping thread）的尺寸为 **M6**。 |
| mechvqa_q040 | 1 | 1.0 | 在参数表中，当 l₁ 的标称尺寸为 48 时，Type EH 的 m₁ 为 31 ± 0.25，m₂ 为 30.5 ±  |
| mechvqa_q041 | 1 | 1.0 | In the middle-lower circular bottom view, the dimension labe |
| mechvqa_q042 | 1 | 1.0 | 在规格尺寸表格中，当 d₁ 为 36 且 d₂ 为 M8 时，对应的 h 值为 **14.5**。 |
| mechvqa_q043 | 1 | 1.0 | In the parameter table, when d₁ is 6, the specification of d |
| mechvqa_q044 | 1 | 1.0 | According to the table in the mechanical drawing, when d₁ is |
| mechvqa_q045 | 1 | 1.0 | 当 d1 尺寸为 45+0.3/-0.5 时，对应的静态载荷为 **120 kN**。 |
| mechvqa_q046 | 1 | 1.0 | DIN 7991 标准对应的螺钉类型为**内六角沉头螺钉**（Countersunk Head Socket Screw |
| mechvqa_q047 | 1 | 1.0 | 根据机械图纸表格，当 d₁ 为 25 ± 0.1 且 Magnet HF 为 M4 时，h 尺寸标注为 7 +0.3/‑ |
| mechvqa_q048 | 1 | 1.0 | In the view labeled 'Swiveling range', the maximum rotation  |
| mechvqa_q049 | 1 | 1.0 | 根据机械图纸的 U 形 2D 视图数据，Type A（d₁=20）对应的 r 值为 22，Type B（d₁=28）对应 |
| mechvqa_q050 | 1 | 1.0 | The total length from the center of the first bolt hole to t |
| mechvqa_q051 | 1 | 1.0 | 图中凸轮滚子线性导轨的型号是 GN 2492。 |
| mechvqa_q052 | 1 | 1.0 | A-A剖视图中显示的零件厚度为 **8 mm**。 |
| mechvqa_q053 | 1 | 1.0 | In the main view, the labeled dimension h₁ refers to the thi |
| mechvqa_q054 | 1 | 1.0 | 零件上明确标注的圆孔直径尺寸为 Ø40 和 Ø15。（图纸中以 “Ø” 符号标注的圆孔直径仅有这两个尺寸，其他如 R27 |
| mechvqa_q055 | 1 | 1.0 | 根据图纸标注，顶部视图中零件的总宽度（包含两侧凸台）为 **165 mm**（15 mm + 135 mm + 15 m |
| mechvqa_q056 | 1 | 1.0 | 根据机械图纸，左下侧视图中标注的X形支撑结构的总长度尺寸为 **200**（单位按图纸标注，一般为毫米）。 |
| mechvqa_q057 | 1 | 1.0 | 零件左端圆柱体的外径尺寸为Φ65。 |
| mechvqa_q058 | 1 | 1.0 | 根据图纸，零件右侧同心圆结构的外圆直径为 Ø70，内圆直径为 Ø40。壁厚计算公式为 (外圆直径 - 内圆直径) / 2 |
| mechvqa_q059 | 1 | 1.0 | 零件上标注的圆弧半径值为 **R4** 和 **R13**（图纸中分别标记为 “12‑R4” 与 “6‑R13”）。 |
| mechvqa_q060 | 1 | 1.0 | 主视图中标注的零件总高度尺寸为28。 |
| mechvqa_q061 | 1 | 1.0 | The diameter dimension of the central through-hole in the fi |
| mechvqa_q062 | 1 | 1.0 | The outer diameter dimension of the circular region on the l |
| mechvqa_q063 | 1 | 1.0 | 零件上标注的通孔直径为Φ12，数量为2个（图纸中标注为“2‑Φ12”）。 |
| mechvqa_q064 | 1 | 1.0 | The diameter annotation value of the outermost cylinder in t |
| mechvqa_q065 | 1 | 1.0 | The fillet radius value marked at the end of the left fork a |
| mechvqa_q066 | 1 | 1.0 | 图中中心圆环的直径标注尺寸为 Ø150。 |
| mechvqa_q067 | 1 | 1.0 | 图中中心孔的直径尺寸标注值为 **Ø75**（单位默认为毫米）。 |
| mechvqa_q068 | 1 | 1.0 | 右端叉形端部的外形宽度为25 mm。依据是下方局部/俯视图在该端部上下方向直接标注了25，该尺寸对应主视图右端叉形结构的 |
| mechvqa_q069 | 1 | 1.0 | 左下角俯视图中标注的螺栓孔分布圆直径为∅98 mm。 |
| mechvqa_q070 | 1 | 1.0 | 根据主视图的尺寸标注，两个Φ24通孔的中心距为 **63 mm**。主视图中标注的水平尺寸63 mm即为两孔中心之间的直 |
| mechvqa_q071 | 1 | 1.0 | The side length of the diamond-shaped outer frame in the fig |
| mechvqa_q072 | 1 | 1.0 | 根据机械图纸，在A‑A剖视图的顶部平面上，表面粗糙度的要求为 Ra 1.6。该数值在图纸的剖视图标注处以“Ra1.6”形 |
| mechvqa_q073 | 1 | 1.0 | The annotation "2-C2" in the front view indicates that this  |
| mechvqa_q074 | 1 | 1.0 | 第1个 |
| mechvqa_q075 | 1 | 1.0 | 第12个零件 |
| mechvqa_q076 | 1 | 1.0 | 第4个零件 |
| mechvqa_q077 | 1 | 1.0 | 第10个零件 |
| mechvqa_q078 | 1 | 1.0 | Part drawing |
| mechvqa_q079 | 1 | 1.0 | 要确定装配图中序号11零件的材料，需查看图纸右侧的明细栏。在明细栏中找到序号为11的行，对应“材料”列的信息显示为HT1 |
| mechvqa_q080 | 1 | 1.0 | 观察该图纸，图中包含多个不同方向和形式的视图（如主视图、B向视图、A向视图等），各视图从不同角度展示了支架的结构特征。由 |
| mechvqa_q081 | 1 | 1.0 | Item numbers 2 (seal ring), 4 (gasket), 6 (gasket), and 7 (s |
| mechvqa_q082 | 1 | 1.0 | The special views in the drawing include a section view and  |
| mechvqa_q083 | 1 | 1.0 | 2 |
| mechvqa_q084 | 1 | 1.0 | 在该偏心柱塞泵（ZPT19）的装配图中，需通过明细栏确认零件名称。首先定位图纸右下角的明细表，查找序号“8”对应的行。结 |
| mechvqa_q085 | 1 | 1.0 | 4 |
| mechvqa_q086 | 1 | 1.0 | 4 |
| mechvqa_q087 | 1 | 1.0 | 要确定图纸中剖视图的数量，需识别带有剖切符号（如“×-×”形式）的视图。观察图纸：  
- 存在标注为“A-A”的剖视图 |
| mechvqa_q088 | 1 | 1.0 | 在查看该回油阀（ZPT21）的图纸技术要求后，发现其中第4条明确说明：“安全阀与管道连接处需加石棉橡胶垫（XB350）” |
| mechvqa_q089 | 1 | 1.0 | GB/T 3077-1999 |
| mechvqa_q090 | 1 | 1.0 | 要确定该装配图中序号10零件的名称，需查看图纸右侧的**明细栏**。在明细栏中找到序号为“10”的行，其对应的“名称”列 |
| mechvqa_q091 | 1 | 1.0 | 要确定该图纸采用的特殊视图，需结合机械制图中特殊视图的定义逐一分析：  

1. **剖视图**：图纸中存在标注为“A  |
| mechvqa_q092 | 1 | 1.0 | 首先，确定子图的排列顺序：从左至右、从上至下。组合图中第一行有1张图（阀杆），第二行有2张图（从左至右依次为定位片、上盖 |
| mechvqa_q093 | 1 | 1.0 | 首先观察第1张图（图5-10 十字连接块）的视图组成。从图中可以看到：  
- 上方标注有“A-A”的视图，采用剖面线填 |
| mechvqa_q094 | 1 | 1.0 | 第1张图（十字连接块）中，按照从左至右、从上至下的顺序，其特殊视图包括：  
1. 剖视图（主视图部分，带有剖面线和A- |
| mechvqa_q095 | 1 | 1.0 | 根据图中零件的布局，按照从左至右、从上至下的顺序观察：

1. **左上角（图5-10）**：标注为“十字连接块”，零件 |
| mechvqa_q096 | 1 | 1.0 | 该组合图中子图按从左至右、从上至下的顺序排列，第1张为左上方的“手轮”图，第2张为右上方的“中间垫片”图，第3张是下方的 |
| mechvqa_q097 | 1 | 1.0 | 要判断图纸中向视图的数量，需明确向视图的定义：向视图是**按投射方向自由配置**的视图，需用箭头指明投射方向，并标注相同 |
| mechvqa_q098 | 1 | 1.0 | 65Mn |
| mechvqa_q099 | 1 | 1.0 | 序号1的零件名称是手柄球。 |
| mechvqa_q100 | 1 | 1.0 | 右泵盖 |
| mechvqa_q101 | 1 | 1.0 | 该组合图中包含3张子图，分别是标注为“图5-90 宝塔弹簧”“图5-91 橡胶密封圈”“图5-92 连接接头”的三幅独立 |
| mechvqa_q102 | 1 | 1.0 | 该组合图中，按从左至右、从上至下的顺序，各子图对应的零件分别为：  
- 第一行左侧子图（图5 - 255）：表锁紧手轮 |
| mechvqa_q103 | 1 | 1.0 | Axonometric view |
| mechvqa_q104 | 1 | 1.0 | 240-260HBW |
| mechvqa_q105 | 1 | 1.0 | Assembly drawing |
| mechvqa_q106 | 1 | 1.0 | Sectional view and axonometric view |
| mechvqa_q107 | 1 | 1.0 | 视图主视图中，阀体底部圆角的半径标注为R150。 |
| mechvqa_q108 | 1 | 1.0 | 向视图‘零件11 A’的观察位置标注在主视图（左侧的全剖视图）顶部，即主视图中零件11（手轮）正上方的带字母‘A’的箭头 |
| mechvqa_q109 | 1 | 1.0 | 图中 C--C 表示**剖视图的标注**，用于指示在该位置进行剖切，并在对应的剖视图上方标明剖切平面，以便展示零件内部结 |
| mechvqa_q110 | 1 | 1.0 | In the drawing, the auxiliary view label A is located above  |
| mechvqa_q111 | 1 | 1.0 | 位于上方A-A剖视图的顶部，紧邻A-A标注右侧。 |
| mechvqa_q112 | 1 | 1.0 | According to the mechanical drawing, the height dimension of |
| mechvqa_q113 | 1 | 1.0 | 在该机械图纸的主视图中，顶部大圆弧的半径标注为 **R70**，即半径为 **70**。 |
| mechvqa_q114 | 1 | 1.0 | 基准A对应的基准面位于主视图下方的底部水平安装面。 |
| mechvqa_q115 | 1 | 1.0 | 该图纸的主视图位于左上角（左上区域）。该视图完整展示了蜗轮壳的主体轮廓及关键尺寸（如Φ110通孔、R55圆弧、总高95、 |
| mechvqa_q116 | 1 | 1.0 | 基准A所指的基准面位于 B‑B 剖视图的左侧端面。 |
| mechvqa_q117 | 1 | 1.0 | The front view of this drawing is located in the upper (uppe |
| mechvqa_q118 | 1 | 1.0 | 该组合图中的第2张图（即图5-125 旋塞轴）左侧轴段的直径尺寸为 **φ9.8 mm**。 |
| mechvqa_q119 | 1 | 1.0 | 根据机械图纸，第2张图（图5-125 旋塞轴）主视图中的剖切符号为 **A‑A**。 |
| mechvqa_q120 | 1 | 1.0 | 该图纸的主视图位于左上方区域。 |
| mechvqa_q121 | 1 | 1.0 | 剖切标注A-A位于主视图（图纸上方的视图）的右侧区域，标注的剖切线指向右侧，表示沿该位置从左向右剖切后得到右侧的A-A剖 |
| mechvqa_q122 | 1 | 1.0 | The diameter dimension marked on the dial indicator face is  |
| mechvqa_q123 | 1 | 1.0 | 在第1张图（图5-109 压盖）中，粗糙度Ra0.8的标注位于左下方外形视图的上方圆弧轮廓处，引线指向压盖的外侧顶面（上 |
| mechvqa_q124 | 1 | 1.0 | In the main view of the 2nd figure, the distance from the st |
| mechvqa_q125 | 1 | 1.0 | 第2张子图的主视图中，零件总长度的尺寸标注为70。 |
| mechvqa_q126 | 1 | 1.0 | 右上视图中顶部两个定位孔的标注尺寸为 **2×Φ8 H7（上偏差+0.015 mm，下偏差0 mm）**，即两个直径8  |
| mechvqa_q127 | 1 | 1.0 | 在A‑A剖视图中，Φ30H9(⁺0.052₀)采用的是**公差带代号与极限偏差同时标注**的形式。这里“Φ30”是孔的公 |
| mechvqa_q128 | 1 | 1.0 | 该图纸中左侧轴承安装孔尺寸为Φ62 J7，图中标注公差为+0.018/-0.012。 |
| mechvqa_q129 | 1 | 1.0 | 第2张图的4:1放大图中，齿形外径标注为Φ8.5 a10。 |
| mechvqa_q130 | 1 | 1.0 | 左端面倒角的尺寸为 **C0.5**（其中 C 表示 45°倒角，0.5 为倒角宽度，单位为 mm）。 |
| mechvqa_q131 | 1 | 1.0 | Ra0.4主要标注在六角手柄的外六角侧面（六个外侧平面）上。 |
| mechvqa_q132 | 1 | 1.0 | The explicitly defined datum symbol in the drawing is **A**. |
| mechvqa_q133 | 1 | 1.0 | 剖视图A‑A位于图纸的右侧区域。 |
| mechvqa_q134 | 1 | 1.0 | 向视图A的观察位置对应主视图左下部的倾斜端面/斜杆底部斜面，即图中A箭头所指、标注有60°和Ra3.2附近的倾斜长面。 |
| mechvqa_q135 | 1 | 1.0 | 该图纸的主视图位于图纸上方偏右的区域，是带有大圆孔轮廓、A/D等向视箭头的外形视图。 |
| mechvqa_q136 | 1 | 1.0 | 向视图A₁和A₂位于图纸左侧中部偏上的小圆形视图处。 |
| mechvqa_q137 | 1 | 1.0 | The parent view that Section E-E cuts through is the B-B sec |
| mechvqa_q138 | 1 | 1.0 | In the first image (Fig. 5-16 Threaded Insert), the datum C1 |
| mechvqa_q139 | 1 | 1.0 | 粗糙度Ra0.4的标注位于图纸右下角的技术要求区域，具体在标题栏上方的说明栏内，与其他技术要求文字一起标注。 |
| mechvqa_q140 | 1 | 1.0 | 第3张图（即右下角的“图5-205 放油螺栓”）中，粗糙度Ra6.3的标注位于图纸右下角的技术要求区域，具体在技术要求文 |
| mechvqa_q141 | 1 | 1.0 | Based on SECTION A-A and VIEW A, it can be confirmed that th |
| mechvqa_q142 | 1 | 1.0 | Based on the step sequence of the assembly instruction diagr |
| mechvqa_q143 | 1 | 1.0 | 根据机械图纸及参数表格的对比，h₂ 是剖视图中的垂直高度尺寸，d₃ 是底视图中的水平直径尺寸。它们描述的是不同方向、不同 |
| mechvqa_q144 | 1 | 1.0 | 首先观察左侧2D机械图纸，其为“连杆（LJT05.07）”，整体呈细长杆状结构，一端有连接头，中间存在特定轮廓过渡，标注 |
| mechvqa_q145 | 1 | 1.0 | **判断**：主视图中分段尺寸60 + 60=120 与总长标注125 不一致，存在5 mm 的差异。 

**可能原因 |
| mechvqa_q146 | 1 | 1.0 | 判断：侧视图中高度尺寸未标注不属于尺寸遗漏，符合机械制图规范。理由如下：
1. **尺寸标注原则**：同一方向的尺寸只需 |
| mechvqa_q147 | 1 | 1.0 | 要判断这两个图是否表示同一个零件，需对比结构特征、尺寸标注及工艺信息：  

1. **结构特征**：  
   - 左 |
| mechvqa_q148 | 1 | 1.0 | 根据图纸参数表，d1=50 时的压缩应力为 0.4 N/mm²，阻尼元件面积为 1809 mm²。按照应力×面积的公式计 |
| mechvqa_q149 | 1 | 1.0 | There is no logical conflict. φ16 mm indicates the diameter  |
| mechvqa_q150 | 1 | 1.0 | 图5-126压紧弹簧的技术要求中明确标注的热处理后硬度范围为45‑50 HRC。 |
| mechvqa_q151 | 1 | 1.0 | The title of this mechanical drawing is "DESIGN OF CHAIN BEN |
| mechvqa_q152 | 1 | 1.0 | In the parameter table, the parameter name corresponding to  |
| mechvqa_q153 | 1 | 1.0 | 螺钉的牙数P在参数表格中的具体数值是 **32**。 |
| mechvqa_q154 | 1 | 1.0 | 在图纸底部的规格参数表格中，M16×1.5规格对应的d₂尺寸为46。 |
| mechvqa_q155 | 1 | 1.0 | 根据图纸中的参数表格，当 d₁ 为 25 时，对应的 d 规格值为 **16.8**。 |
| mechvqa_q156 | 1 | 1.0 | 剖视图标注的厚度 h = 0.38 mm 与主视图中所示的单耳止动垫圈整体结构的轴向厚度相对应。主视图只展示了零件的平面 |
| mechvqa_q157 | 1 | 1.0 | 外径 dc 为 0.307~0.320 in，内径 d 为 0.151~0.164 in，厚度 h 为 0.027~0. |
| mechvqa_q158 | 1 | 1.0 | 根据剖面视图标注的截面宽度为 12，而轴测图中圆柱体的直径为 Ø32。若截面垂直于圆柱体轴线，截面应为直径 32 的圆形 |
| mechvqa_q159 | 1 | 1.0 | 依据图纸右侧的全剖视图，轴向方向标注为 **280 mm ±0.3 mm**，该尺寸直接对应内齿圈的顶部端面到底部端面的 |
| mechvqa_q160 | 1 | 1.0 | Worm shaft end cover |
| mechvqa_q161 | 1 | 1.0 | 该零件的名称是A型平垫圈（N）。依据图纸标题栏中标注的“ASME/ANSI B18.22.1-1975 A型平垫圈(N) |
| mechvqa_q162 | 1 | 1.0 | 该机械零件的完整名称为 **ISO 7051-2011 十字槽半沉头自攻螺钉C型**。图纸标题栏及产品参数表均标注了标准 |
| mechvqa_q163 | 1 | 1.0 | 四周边框宽度按 (外轮廓边长 - 内孔边长) ÷ 2 计算，即 (46 mm - 28 mm) ÷ 2 = 9 mm。因 |
| mechvqa_q164 | 1 | 1.0 | 内径 d 的平均尺寸值为 **0.3165 inch**。计算过程如下：

平均尺寸 = (d_min + d_max) |
| mechvqa_q165 | 1 | 1.0 | 根据主视图中的尺寸范围，平垫圈的内径 d 为 1.70 mm~1.84 mm，外径 dc 为 3.70 mm~4.00  |
| mechvqa_q166 | 1 | 1.0 | ### 比值变化趋势
当 d₁ 从 M12 增至 M36 时，**l/d₁ 的比值始终为 1.5**，即长度 l 与公称 |
| mechvqa_q167 | 1 | 1.0 | According to the mechanical drawing, when d1 = 16 mm, the ax |
| mechvqa_q168 | 1 | 1.0 | 当 d1 = 52 mm 时，图纸对应的 d4 为 37 mm，二者的尺寸差值为 **15 mm**（直径差），相当于  |
| mechvqa_q169 | 1 | 1.0 | 根据机械图纸的中间侧视图以及图纸下方的参数表格，当 l₁=270 mm、l₂=27 mm 时，链条总长度中包含 **10 |
| mechvqa_q170 | 1 | 1.0 | 根据图纸参数表的数据，d₁ 与 h 并不存在近似的比例关系。具体分析如下：

1. **关键数据计算**
   - 当  |
| mechvqa_q171 | 1 | 1.0 | 两孔之间的最小水平间距为 **15 mm**。计算方法：中心距28 mm减去左孔半径6.5 mm和右孔半径6.5 mm， |
| mechvqa_q172 | 1 | 1.0 | According to the drawing, the outer circle diameter is Φ123, |
| mechvqa_q173 | 1 | 1.0 | The (76) dimension annotated in the drawing belongs to a **R |
| mechvqa_q174 | 1 | 1.0 | 根据图纸标注，总高度为 18 mm，基座高度为 6 mm。立柱的有效高度 = 总高度 - 基座高度 = 18 mm -  |
| mechvqa_q175 | 1 | 1.0 | 根据图纸标注：总长度为135 mm，Ø15孔中心到右侧端点的水平距离为82.5 mm。于是左侧端点到Ø15孔中心的水平距 |
| mechvqa_q176 | 1 | 1.0 | According to the mechanical drawing, φ24 and φ16 are the dia |
| mechvqa_q177 | 1 | 1.0 | According to the drawing, the outer diameter of the central  |
| mechvqa_q178 | 1 | 1.0 | According to the mechanical drawing, the horizontal dimensio |
| mechvqa_q179 | 1 | 1.0 | According to the mechanical drawing, the horizontal distance |
| mechvqa_q180 | 1 | 1.0 | 根据图纸的尺寸标注，螺纹孔（M10）中心到其右侧端面的轴向距离为40 mm。 |
