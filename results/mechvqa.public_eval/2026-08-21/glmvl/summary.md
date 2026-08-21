# qa_grounded(free_vqa) 结果汇总（provider=glmvl, model=glm-4v-flash, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 180
- gate 通过（非空作答）: 180
- gate 失败（空答=missing_output）: 0（直接 0 分）
- gate 失败原因分布: 无

## 客观层（requirements = 中文感知 Exact/数值容差/F1）

- 满分（归一化精确或数值全命中）: 37/180（accuracy = 0.2056）
- 含部分分的均值: 0.3504（F1 部分分口径）
- 子分适用性: physics=N/A（无证据/拒答层）；objective=N/A；robustness=N/A（样本=1）

## 分层（capability × difficulty）

| capability | difficulty | n | mean |
| --- | --- | --- | --- |
| Judging | Easy | 13 | 0.3891 |
| Judging | Hard | 8 | 0.1273 |
| Judging | Medium | 19 | 0.2772 |
| Reasoning | Easy | 10 | 0.2190 |
| Reasoning | Hard | 15 | 0.2401 |
| Reasoning | Medium | 17 | 0.2715 |
| Recognition | Easy | 68 | 0.4857 |
| Recognition | Hard | 3 | 0.2322 |
| Recognition | Medium | 27 | 0.2814 |

## 每题明细（前 8 字符级截断）

| task | gate | score | parsed |
| --- | --- | --- | --- |
| mechvqa_q001 | 1 | 0.3692 | Type B uses a lock nut for securing, while Type BR incorpora |
| mechvqa_q002 | 1 | 0.4444 | - Bayonet连接：无螺纹，通过卡口设计实现快速连接和拆卸。
- Thread连接：有螺纹，需要拧紧以实现密封和固定 |
| mechvqa_q003 | 1 | 0.4074 | 主视图中的梯形轮廓代表了一个带有斜面的台阶状结构。 |
| mechvqa_q004 | 1 | 0.1951 | The name of the part is "方螺母" (Square Nut). |
| mechvqa_q005 | 1 | 0.08 | HT200 |
| mechvqa_q006 | 1 | 0.0 | 4 |
| mechvqa_q007 | 1 | 0.1143 | 配气盘与配气盘垫可以采用粘合剂粘接。 |
| mechvqa_q008 | 1 | 1.0 | The surface roughness Ra value for the locating key in the u |
| mechvqa_q009 | 1 | 0.1739 | 0.3 |
| mechvqa_q010 | 1 | 0.1613 | The total thickness of the part is 4 mm. |
| mechvqa_q011 | 1 | 0.0 | 35 |
| mechvqa_q012 | 1 | 1.0 | 0.01 ~ 0.017 |
| mechvqa_q013 | 1 | 0.325 | 产品规格“256”-56中的数字分别对应参数表中的直径(d)和牙数(p)。 |
| mechvqa_q014 | 1 | 0.2917 | 对角宽度理论范围为 31.8 ~ 32.2 mm。与图纸标注的 e_min = 33.6 mm 比较，实际值小于标注的最 |
| mechvqa_q015 | 1 | 0.4706 | 小六角螺母(大对边) |
| mechvqa_q016 | 1 | 1.0 | The specific value of the hexalobular socket nominal diamete |
| mechvqa_q017 | 1 | 1.0 | 6 毫米。 |
| mechvqa_q018 | 1 | 1.0 | The specification parameter for pitch \(P\) in the parameter |
| mechvqa_q019 | 1 | 1.0 | The diagonal width \(e\) labeled in the top view of the cros |
| mechvqa_q020 | 1 | 0.125 | 0.19 ~ 0.25 |
| mechvqa_q021 | 1 | 1.0 | The specification range for the dimension code 'dk' (head di |
| mechvqa_q022 | 1 | 0.1481 | 20000 N |
| mechvqa_q023 | 1 | 0.6275 | The ratio of the minimum length \(L_{\text{min}}\) to the ma |
| mechvqa_q024 | 1 | 0.129 | 80 N。 |
| mechvqa_q025 | 1 | 0.0 | 橡胶。 |
| mechvqa_q026 | 1 | 0.1 | 22。 |
| mechvqa_q027 | 1 | 1.0 | 6.5 |
| mechvqa_q028 | 1 | 0.1538 | 23 |
| mechvqa_q029 | 1 | 0.1333 | 连接件的长度。 |
| mechvqa_q030 | 1 | 0.0 | 350。 |
| mechvqa_q031 | 1 | 0.08 | 17 |
| mechvqa_q032 | 1 | 0.0 | 折叠出 |
| mechvqa_q033 | 1 | 0.1538 | 2.7 |
| mechvqa_q034 | 1 | 0.0455 | 手柄。 |
| mechvqa_q035 | 1 | 1.0 | 1 毫米。 |
| mechvqa_q036 | 1 | 0.2308 | M16 x 1.5 |
| mechvqa_q037 | 1 | 0.2273 | The internal hex feature is located near the bottom of the t |
| mechvqa_q038 | 1 | 0.0 | 6 |
| mechvqa_q039 | 1 | 0.0833 | M6 |
| mechvqa_q040 | 1 | 0.4823 | 根据表格中 Type EH 的 m₁ 和 m₂ 尺寸数据，当 l₁ 标称尺寸为 48 时，m₁ 和 m₂ 尺寸之和的公差 |
| mechvqa_q041 | 1 | 0.2564 | The dimension labeled 'd₁' represents the diameter of the bo |
| mechvqa_q042 | 1 | 0.1481 | 14.5 |
| mechvqa_q043 | 1 | 0.5217 | When \(d_1\) is 6, the specification of \(d_2\) is 23. |
| mechvqa_q044 | 1 | 0.16 | 19.5 |
| mechvqa_q045 | 1 | 0.1739 | 120 kN。 |
| mechvqa_q046 | 1 | 0.1818 | 沉头螺钉。 |
| mechvqa_q047 | 1 | 0.0755 | +0,3/-0,2 |
| mechvqa_q048 | 1 | 1.0 | The maximum rotation angle of the hinge in the "Swiveling ra |
| mechvqa_q049 | 1 | 0.3564 | Type A中，当$d_1$从20增加到28时，$r$值从22增加到32。 |
| mechvqa_q050 | 1 | 0.4918 | The total length from the center of the first bolt hole to t |
| mechvqa_q051 | 1 | 1.0 | GN 2492 |
| mechvqa_q052 | 1 | 0.0 | 10mm |
| mechvqa_q053 | 1 | 0.303 | The dimension \( h_1 \) represents the height of the cylindr |
| mechvqa_q054 | 1 | 0.0741 | 40、15。 |
| mechvqa_q055 | 1 | 0.0606 | 135 |
| mechvqa_q056 | 1 | 1.0 | 200毫米。 |
| mechvqa_q057 | 1 | 1.0 | 65mm |
| mechvqa_q058 | 1 | 0.0 | 20 |
| mechvqa_q059 | 1 | 1.0 | 12-R4、6-R13。 |
| mechvqa_q060 | 1 | 1.0 | 28 |
| mechvqa_q061 | 1 | 0.3333 | The diameter dimension of the central through-hole is Φ28.5. |
| mechvqa_q062 | 1 | 1.0 | 55.5 |
| mechvqa_q063 | 1 | 0.1429 | 20mm, 2个。 |
| mechvqa_q064 | 1 | 1.0 | The diameter annotation value of the outermost cylinder is Φ |
| mechvqa_q065 | 1 | 1.0 | The fillet radius value marked at the end of the left fork a |
| mechvqa_q066 | 1 | 1.0 | 150 |
| mechvqa_q067 | 1 | 1.0 | 75 |
| mechvqa_q068 | 1 | 0.0241 | 25 |
| mechvqa_q069 | 1 | 1.0 | 98mm |
| mechvqa_q070 | 1 | 0.0 | 50mm |
| mechvqa_q071 | 1 | 1.0 | The side length dimension of the diamond-shaped outer frame  |
| mechvqa_q072 | 1 | 0.0 | Ra12.5 |
| mechvqa_q073 | 1 | 0.1569 | The annotation '2-C2' represents a cylindrical feature with  |
| mechvqa_q074 | 1 | 0.0 | 4. 滑阀 (LJT03.04) |
| mechvqa_q075 | 1 | 0.0157 | 第一张2D图属于第一张3D图；
第二张2D图属于第四张3D图；
第三张2D图属于第五张3D图；
第四张2D图属于第六张3 |
| mechvqa_q076 | 1 | 0.4444 | 2D图属于3D图中的第一个零件。 |
| mechvqa_q077 | 1 | 0.4444 | 2D图属于3D图中的第一个零件。 |
| mechvqa_q078 | 1 | 0.8 | This is a part drawing. |
| mechvqa_q079 | 1 | 0.0312 | HT150 |
| mechvqa_q080 | 1 | 0.0674 | 多视图。 |
| mechvqa_q081 | 1 | 0.2 | The sealing components in the assembly drawing are the "密封圈" |
| mechvqa_q082 | 1 | 0.5882 | The special views in this drawing include a top view of the  |
| mechvqa_q083 | 1 | 0.0 | There are three views in this drawing. |
| mechvqa_q084 | 1 | 0.036 | 填料。 |
| mechvqa_q085 | 1 | 0.0 | 3个视图。 |
| mechvqa_q086 | 1 | 0.0 | There are four views in the drawing. |
| mechvqa_q087 | 1 | 1.0 | 2个。 |
| mechvqa_q088 | 1 | 0.2222 | 需要加石棉橡胶垫。 |
| mechvqa_q089 | 1 | 1.0 | GB/T 3077-1999. |
| mechvqa_q090 | 1 | 0.058 | 螺钉 |
| mechvqa_q091 | 1 | 0.12 | 该图纸采用了俯视图、侧视图和局部放大视图。 |
| mechvqa_q092 | 1 | 0.0109 | 3个。 |
| mechvqa_q093 | 1 | 0.1017 | 特殊视图：A-A剖面图。 |
| mechvqa_q094 | 1 | 0.3276 | - 第1张图中的特殊视图：A-A剖面视图、局部放大视图。 |
| mechvqa_q095 | 1 | 0.0893 | 十字连接块、连接块半轴。 |
| mechvqa_q096 | 1 | 0.0645 | 磁力座。 |
| mechvqa_q097 | 1 | 0.0158 | 2个。 |
| mechvqa_q098 | 1 | 1.0 | 65Mn |
| mechvqa_q099 | 1 | 0.4 | 手柄球 |
| mechvqa_q100 | 1 | 1.0 | 右泵盖。 |
| mechvqa_q101 | 1 | 0.0833 | 3张。 |
| mechvqa_q102 | 1 | 0.2353 | 表锁紧手轮、球头外套、夹表块。 |
| mechvqa_q103 | 1 | 0.087 | Top-left: Top view, front view, side view  
Top-right: Secti |
| mechvqa_q104 | 1 | 1.0 | The hardness range after quenching and tempering is 240-260  |
| mechvqa_q105 | 1 | 1.0 | This is an assembly drawing. |
| mechvqa_q106 | 1 | 0.2667 | The drawing uses a top view, front view, side view, and an e |
| mechvqa_q107 | 1 | 0.0 | 120。 |
| mechvqa_q108 | 1 | 0.1091 | 俯视图右上角。 |
| mechvqa_q109 | 1 | 0.0541 | 剖面线。 |
| mechvqa_q110 | 1 | 0.2791 | The auxiliary view labeled "A" is located on the top right o |
| mechvqa_q111 | 1 | 0.3846 | 俯视图右上方。 |
| mechvqa_q112 | 1 | 1.0 | The dimension of the vertical step height on the right side  |
| mechvqa_q113 | 1 | 1.0 | 70±0.06 |
| mechvqa_q114 | 1 | 0.2667 | 右视图的上方。 |
| mechvqa_q115 | 1 | 0.0396 | 左下角。 |
| mechvqa_q116 | 1 | 0.6977 | 基准A所指的基准面位于右下角视图的左上角部位。 |
| mechvqa_q117 | 1 | 0.1739 | The front view is located in the lower left corner of the dr |
| mechvqa_q118 | 1 | 0.0 | 7.5mm |
| mechvqa_q119 | 1 | 0.3429 | 剖切符号是A-A。 |
| mechvqa_q120 | 1 | 0.4211 | 图纸左上角。 |
| mechvqa_q121 | 1 | 0.1017 | 右上方。 |
| mechvqa_q122 | 1 | 1.0 | 50 |
| mechvqa_q123 | 1 | 0.1786 | 压盖的左下角。 |
| mechvqa_q124 | 1 | 0.5946 | The distance from the starting point of the 10° conical surf |
| mechvqa_q125 | 1 | 0.087 | 70 |
| mechvqa_q126 | 1 | 0.04 | 8 |
| mechvqa_q127 | 1 | 0.1622 | 公差带在零线上的偏差为正。 |
| mechvqa_q128 | 1 | 0.1212 | 70±0.025、47J7（-0.011） |
| mechvqa_q129 | 1 | 0.4324 | 齿形外径的尺寸是Φ8.5，公差代号为H11。 |
| mechvqa_q130 | 1 | 0.0 | 15 |
| mechvqa_q131 | 1 | 0.4889 | - 左侧六边形外轮廓的六个面上；
- 内部圆环面的外侧。 |
| mechvqa_q132 | 1 | 0.2308 | The datum symbols included in the drawing are "A," "B," and  |
| mechvqa_q133 | 1 | 0.1176 | 右下角。 |
| mechvqa_q134 | 1 | 0.0377 | 右下角。 |
| mechvqa_q135 | 1 | 0.3673 | 主视图位于图纸的右下角。 |
| mechvqa_q136 | 1 | 0.2143 | 图纸左下角。 |
| mechvqa_q137 | 1 | 0.65 | The parent view that Section E-E cuts through is the top vie |
| mechvqa_q138 | 1 | 0.4848 | The datum C1 annotation is located on the left side of the s |
| mechvqa_q139 | 1 | 1.0 | 粗糙度Ra0.4的标注位于右下角。 |
| mechvqa_q140 | 1 | 0.3579 | 在第三张图中，粗糙度Ra6.3的标注位于齿轮轴M=2Z=15的右侧。 |
| mechvqa_q141 | 1 | 0.1043 | The part has a cylindrical shape with internal threading and |
| mechvqa_q142 | 1 | 0.1842 | Mounting the gray part is done during Step 2: "Mount the bli |
| mechvqa_q143 | 1 | 0.0301 | 存在。 |
| mechvqa_q144 | 1 | 0.0917 | 是的，两个图表示同一个零件。 |
| mechvqa_q145 | 1 | 0.0176 | 一致。 |
| mechvqa_q146 | 1 | 0.0234 | 不符合。 |
| mechvqa_q147 | 1 | 0.0784 | 是的，两个图表示同一个零件。 |
| mechvqa_q148 | 1 | 0.0272 | 一致。 |
| mechvqa_q149 | 1 | 0.3659 | No, there is no logical conflict. The linear dimension of 20 |
| mechvqa_q150 | 1 | 0.0625 | 45-50HRC |
| mechvqa_q151 | 1 | 1.0 | The title of the mechanical drawing is "Design of Chain Bend |
| mechvqa_q152 | 1 | 0.5714 | The parameter name corresponding to the dimension code 'P' i |
| mechvqa_q153 | 1 | 1.0 | 32。 |
| mechvqa_q154 | 1 | 0.0741 | 46。 |
| mechvqa_q155 | 1 | 0.1481 | 16.8 |
| mechvqa_q156 | 1 | 0.2198 | 剖视图中标注的厚度 h 与主视图中的轴孔深度相关联。 |
| mechvqa_q157 | 1 | 1.0 | 外径：0.307 ~ 0.32 英寸  
内径：0.151 ~ 0.164 英寸  
厚度：0.027 ~ 0.048  |
| mechvqa_q158 | 1 | 0.0206 | 是。 |
| mechvqa_q159 | 1 | 0.0227 | 440.0 |
| mechvqa_q160 | 1 | 0.3077 | The name of the part is "螺杆端盖" (screw end cover). |
| mechvqa_q161 | 1 | 0.1515 | A型平垫圈。 |
| mechvqa_q162 | 1 | 0.2581 | 十字槽半沉头自攻螺钉C型。 |
| mechvqa_q163 | 1 | 0.1053 | 2 mm。 |
| mechvqa_q164 | 1 | 0.0923 | 0.3165英寸。 |
| mechvqa_q165 | 1 | 0.0348 | 0.7 毫米。 |
| mechvqa_q166 | 1 | 0.2119 | 随着 \( d_1 \) 从 M12 增至 M36，长度 l 与 \( d_1 \) 的比值逐渐减小。这表明在尺寸增大时 |
| mechvqa_q167 | 1 | 0.6667 | The axial distance from the magnetic surface to the A/F inte |
| mechvqa_q168 | 1 | 0.0058 | 3.5mm |
| mechvqa_q169 | 1 | 0.018 | 10个。 |
| mechvqa_q170 | 1 | 0.0134 | 存在。 |
| mechvqa_q171 | 1 | 0.0385 | 5 |
| mechvqa_q172 | 1 | 0.129 | The wall thickness is 23. |
| mechvqa_q173 | 1 | 1.0 | The (76) dimension is a linear dimension indicating the leng |
| mechvqa_q174 | 1 | 0.0 | 12mm |
| mechvqa_q175 | 1 | 0.0351 | 82.5mm |
| mechvqa_q176 | 1 | 0.1778 | The width of the annular region is 4 units. |
| mechvqa_q177 | 1 | 0.1951 | The width of the central annular region is 50. |
| mechvqa_q178 | 1 | 0.1667 | The inclination angle of the chamfered section is 45 degrees |
| mechvqa_q179 | 1 | 1.0 | 80 mm. |
| mechvqa_q180 | 1 | 0.0667 | 40 |
