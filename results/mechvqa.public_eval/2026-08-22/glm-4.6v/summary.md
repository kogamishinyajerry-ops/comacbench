# qa_grounded(free_vqa) 结果汇总（provider=glmvl, model=glm-4.6v, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 180
- gate 通过（非空作答）: 180
- gate 失败（空答=missing_output）: 0（直接 0 分）
- gate 失败原因分布: 无

## 客观层（requirements = 中文感知 Exact/数值容差/F1）

- 满分（归一化精确或数值全命中）: 43/180（accuracy = 0.2389）
- 含部分分的均值: 0.4044（F1 部分分口径）
- 子分适用性: physics=N/A（无证据/拒答层）；objective=N/A；robustness=N/A（样本=1）

## 分层（capability × difficulty）

| capability | difficulty | n | mean |
| --- | --- | --- | --- |
| Judging | Easy | 13 | 0.3608 |
| Judging | Hard | 8 | 0.2217 |
| Judging | Medium | 19 | 0.3276 |
| Reasoning | Easy | 10 | 0.2690 |
| Reasoning | Hard | 15 | 0.3338 |
| Reasoning | Medium | 17 | 0.2157 |
| Recognition | Easy | 68 | 0.5493 |
| Recognition | Hard | 3 | 0.3931 |
| Recognition | Medium | 27 | 0.3778 |

## 每题明细（前 8 字符级截断）

| task | gate | score | parsed |
| --- | --- | --- | --- |
| mechvqa_q001 | 1 | 0.386 | Type B lacks a spring element, while Type BR incorporates a  |
| mechvqa_q002 | 1 | 0.4819 | Bayonet连接通过卡口（bayonet）实现，无额外紧固件；Thread连接以螺纹配合，并用6个自攻螺丝固定，且设有 |
| mechvqa_q003 | 1 | 0.4643 | 主视图中梯形轮廓代表立体上前方的倾斜平面（或台阶面）结构。 |
| mechvqa_q004 | 1 | 0.1111 | Square nut |
| mechvqa_q005 | 1 | 0.08 | HT200 |
| mechvqa_q006 | 1 | 0.2353 | 槽的深度是1。 |
| mechvqa_q007 | 1 | 0.1856 | 粘合剂粘接，因为图5-73技术要求明确本件与配气盘用粘合剂粘接。 |
| mechvqa_q008 | 1 | 1.0 | 6.3 |
| mechvqa_q009 | 1 | 0.1739 | 0.3 |
| mechvqa_q010 | 1 | 0.3188 | The total thickness of the part is 4, as indicated by the di |
| mechvqa_q011 | 1 | 1.0 | φ25 |
| mechvqa_q012 | 1 | 1.0 | 0.01～0.017 |
| mechvqa_q013 | 1 | 1.0 | 256对应尺寸代号d（直径），56对应尺寸代号P（牙数）。 |
| mechvqa_q014 | 1 | 0.3796 | 理想正六边形中，对边宽度s=29.67~30 mm时，对角宽度e理论范围为约34.32~34. |
| mechvqa_q015 | 1 | 0.4706 | 小六角螺母(大对边) |
| mechvqa_q016 | 1 | 1.0 | 2.8 |
| mechvqa_q017 | 1 | 1.0 | 6 |
| mechvqa_q018 | 1 | 1.0 | 1.1 |
| mechvqa_q019 | 1 | 1.0 | 2.8 |
| mechvqa_q020 | 1 | 0.125 | 0.19 ~ 0.25 |
| mechvqa_q021 | 1 | 1.0 | 2.3 ~ 2.7 mm |
| mechvqa_q022 | 1 | 0.1481 | 20000 N |
| mechvqa_q023 | 1 | 0.4444 | The ratio of the minimum length Lmin to the maximum diameter |
| mechvqa_q024 | 1 | 0.0667 | 80 |
| mechvqa_q025 | 1 | 0.36 | 零件的外径（或主体直径） |
| mechvqa_q026 | 1 | 0.1 | 22 |
| mechvqa_q027 | 1 | 1.0 | 6.5 |
| mechvqa_q028 | 1 | 0.1538 | 23 |
| mechvqa_q029 | 1 | 0.069 | 连接件 |
| mechvqa_q030 | 1 | 1.0 | 550 |
| mechvqa_q031 | 1 | 0.08 | 17 |
| mechvqa_q032 | 1 | 0.25 | folded out |
| mechvqa_q033 | 1 | 0.1538 | 2.7 |
| mechvqa_q034 | 1 | 0.2913 | 右侧视图中h₅尺寸表示零件手柄的长度。 |
| mechvqa_q035 | 1 | 1.0 | 1 mm |
| mechvqa_q036 | 1 | 0.2308 | M16 x 1.5 |
| mechvqa_q037 | 1 | 0.3256 | The threaded cylindrical portion in the actual part photo co |
| mechvqa_q038 | 1 | 1.0 | 8 |
| mechvqa_q039 | 1 | 0.0833 | M6 |
| mechvqa_q040 | 1 | 0.0385 | ±0.5 |
| mechvqa_q041 | 1 | 0.4 | The dimension labeled 'd₁' represents the diameter of the ci |
| mechvqa_q042 | 1 | 0.1481 | 14.5 |
| mechvqa_q043 | 1 | 0.3158 | M12 x 1.5 |
| mechvqa_q044 | 1 | 0.16 | 19.5 |
| mechvqa_q045 | 1 | 0.0909 | 120 |
| mechvqa_q046 | 1 | 1.0 | 沉头螺钉孔视图中引用的DIN 7991标准对应沉头螺钉。 |
| mechvqa_q047 | 1 | 0.0755 | +0.3/-0.2 |
| mechvqa_q048 | 1 | 1.0 | 180 |
| mechvqa_q049 | 1 | 0.2857 | r值随d₁从20增加到28而增大，从22变为32。 |
| mechvqa_q050 | 1 | 0.0556 | 135 |
| mechvqa_q051 | 1 | 1.0 | GN 2492 |
| mechvqa_q052 | 1 | 0.0 | 10 |
| mechvqa_q053 | 1 | 0.2581 | h₁ represents the height of the lower horizontal plate of th |
| mechvqa_q054 | 1 | 0.4928 | 零件上明确标注的圆孔直径尺寸有Ø40、Ø15。 |
| mechvqa_q055 | 1 | 0.0606 | 165 |
| mechvqa_q056 | 1 | 1.0 | 200 |
| mechvqa_q057 | 1 | 1.0 | Φ65 |
| mechvqa_q058 | 1 | 0.0303 | 15 |
| mechvqa_q059 | 1 | 0.619 | 零件上标注的圆弧半径值有R4、R13。 |
| mechvqa_q060 | 1 | 1.0 | 28 |
| mechvqa_q061 | 1 | 0.0 | 28.5 mm |
| mechvqa_q062 | 1 | 1.0 | Ø55.5 |
| mechvqa_q063 | 1 | 1.0 | 通孔直径为12，数量为2。 |
| mechvqa_q064 | 1 | 1.0 | Φ50 |
| mechvqa_q065 | 1 | 1.0 | R70 |
| mechvqa_q066 | 1 | 1.0 | 150 |
| mechvqa_q067 | 1 | 0.0 | Φ80 |
| mechvqa_q068 | 1 | 0.5254 | 25；依据是局部视图与主视图的投影对应关系，局部视图中叉形端部外形宽度标注为25。 |
| mechvqa_q069 | 1 | 1.0 | 98 |
| mechvqa_q070 | 1 | 0.0 | 38 |
| mechvqa_q071 | 1 | 1.0 | 180 |
| mechvqa_q072 | 1 | 0.0435 | Ra1.6 |
| mechvqa_q073 | 1 | 0.0889 | Two chamfers with a 2mm dimension. |
| mechvqa_q074 | 1 | 0.0 | 右下角零件 |
| mechvqa_q075 | 1 | 0.0 | 10 |
| mechvqa_q076 | 1 | 0.5 | 第8个 |
| mechvqa_q077 | 1 | 0.3636 | 第4个零件（从左往右、从上往下数第4个） |
| mechvqa_q078 | 1 | 0.6667 | This drawing is a part drawing. |
| mechvqa_q079 | 1 | 0.0312 | HT150 |
| mechvqa_q080 | 1 | 0.2083 | 该图纸采用多视图表达。 |
| mechvqa_q081 | 1 | 0.48 | Sealing rings (parts 2 and 7) belong to the sealing componen |
| mechvqa_q082 | 1 | 0.4286 | The special views in this drawing are the top view (showing  |
| mechvqa_q083 | 1 | 0.0 | There are two views in this drawing. |
| mechvqa_q084 | 1 | 0.036 | 填料 |
| mechvqa_q085 | 1 | 0.0 | 该图纸的视图数量为3。 |
| mechvqa_q086 | 1 | 1.0 | There are 4 views in this drawing. |
| mechvqa_q087 | 1 | 1.0 | 2 |
| mechvqa_q088 | 1 | 0.2466 | 需要加石棉橡胶垫（XB350）。 |
| mechvqa_q089 | 1 | 1.0 | GB/T 3077--1999 |
| mechvqa_q090 | 1 | 0.058 | 螺钉 |
| mechvqa_q091 | 1 | 0.127 | 该图纸采用了剖视图（A - A、C - C、D - D）和旋转视图（B）。 |
| mechvqa_q092 | 1 | 0.0 | 0 |
| mechvqa_q093 | 1 | 0.0578 | A-A剖视图 |
| mechvqa_q094 | 1 | 0.1359 | A-A剖视图、A向视图 |
| mechvqa_q095 | 1 | 0.0721 | 连接轴、连接块半轴 |
| mechvqa_q096 | 1 | 0.0645 | 磁力座 |
| mechvqa_q097 | 1 | 0.0079 | 2 |
| mechvqa_q098 | 1 | 1.0 | 65Mn |
| mechvqa_q099 | 1 | 0.4 | 手柄球 |
| mechvqa_q100 | 1 | 1.0 | 右泵盖 |
| mechvqa_q101 | 1 | 0.0833 | 3张 |
| mechvqa_q102 | 1 | 0.2353 | 表锁紧手轮、球头外套、夹表块 |
| mechvqa_q103 | 1 | 0.1176 | A-A section view, detailed view (top right); A-A section vie |
| mechvqa_q104 | 1 | 1.0 | 240-260HBW |
| mechvqa_q105 | 1 | 0.8 | This drawing is an assembly drawing. |
| mechvqa_q106 | 1 | 0.4 | The drawing uses a sectional view (A-A) and a circular view  |
| mechvqa_q107 | 1 | 1.0 | R150 |
| mechvqa_q108 | 1 | 0.2182 | 主视图的上方 |
| mechvqa_q109 | 1 | 0.1316 | 剖视图标注 |
| mechvqa_q110 | 1 | 1.0 | The auxiliary view label 'A' is located above the main view, |
| mechvqa_q111 | 1 | 0.5714 | 向视图C的字母加箭头标注位于A - A剖视图的上方。 |
| mechvqa_q112 | 1 | 1.0 | 20 |
| mechvqa_q113 | 1 | 1.0 | R70 |
| mechvqa_q114 | 1 | 0.8837 | 基准A对应的基准面位于主视图的底部平面。 |
| mechvqa_q115 | 1 | 0.2 | 该图纸中主视图位于左上角。 |
| mechvqa_q116 | 1 | 0.7391 | 基准A所指的基准面位于主视图左侧齿条底部的平面部位。 |
| mechvqa_q117 | 1 | 0.2609 | The front view is located in the upper left area of the draw |
| mechvqa_q118 | 1 | 0.125 | φ9.8 |
| mechvqa_q119 | 1 | 0.069 | A |
| mechvqa_q120 | 1 | 0.7407 | 主视图位于图纸的左上角位置。 |
| mechvqa_q121 | 1 | 0.4054 | 图中剖切标注A - A位于主视图的中间位置。 |
| mechvqa_q122 | 1 | 1.0 | Φ50 |
| mechvqa_q123 | 1 | 0.642 | 第1张图（压盖）中粗糙度Ra0.8的标注位于左下角视图（带有12H9的视图）的上方。 |
| mechvqa_q124 | 1 | 0.1538 | 10 mm |
| mechvqa_q125 | 1 | 0.087 | 70 |
| mechvqa_q126 | 1 | 0.0 | 2XΦ8H7(⁺⁰·⁰⁵) |
| mechvqa_q127 | 1 | 0.3664 | A-A剖视图中标注的Φ30H9(⁺⁰·⁰⁵²₀)属于单向极限尺寸标注形式（上偏差标注，下偏差为0）。 |
| mechvqa_q128 | 1 | 0.1379 | Φ62 J7 |
| mechvqa_q129 | 1 | 0.2308 | Φ8.5 a10(-0.280) |
| mechvqa_q130 | 1 | 0.125 | C0.5 |
| mechvqa_q131 | 1 | 0.5217 | 六角外形视图的外侧六个平面及内侧圆形凹槽表面。 |
| mechvqa_q132 | 1 | 0.125 | A, B, C |
| mechvqa_q133 | 1 | 0.4444 | 图纸右侧 |
| mechvqa_q134 | 1 | 0.3284 | 主视图中左下角带有60°角度的斜面区域 |
| mechvqa_q135 | 1 | 0.1395 | 右下角区域 |
| mechvqa_q136 | 1 | 0.0714 | 左下角区域 |
| mechvqa_q137 | 1 | 0.5789 | The parent view of Section E-E is view A, and the cutting po |
| mechvqa_q138 | 1 | 0.4118 | The datum C1 annotation is located at the bottom left corner |
| mechvqa_q139 | 1 | 0.3 | 右下角技术要求及表格区域 |
| mechvqa_q140 | 1 | 0.3294 | 放油螺栓图纸的右下角（技术要求旁） |
| mechvqa_q141 | 1 | 0.1176 | The part has a circular internal cavity containing two symme |
| mechvqa_q142 | 1 | 0.2133 | The mounting base (gray part) should be installed at the "Mo |
| mechvqa_q143 | 1 | 0.2177 | h₂与d₃在数值上不存在直接对应关系。 |
| mechvqa_q144 | 1 | 0.0097 | 是 |
| mechvqa_q145 | 1 | 0.1992 | 不一致，可能因尺寸标注的公差、加工误差或设计预留余量导致。 |
| mechvqa_q146 | 1 | 0.2876 | 侧视图高度未标注符合机械制图规范，因主视图已标注高度30，侧视图高度可通过投影关系确定，无需重复标注。 |
| mechvqa_q147 | 1 | 0.0068 | 是 |
| mechvqa_q148 | 1 | 0.1975 | 不一致，依据是0.4 N/mm²×1809 mm²=723.6 N≠720 N。 |
| mechvqa_q149 | 1 | 0.25 | No, there is no logical conflict because the diameter 16mm i |
| mechvqa_q150 | 1 | 0.0625 | 45 - 50HRC |
| mechvqa_q151 | 1 | 0.6667 | DESIGN OF CHAIN BENDER |
| mechvqa_q152 | 1 | 0.25 | Thread count |
| mechvqa_q153 | 1 | 1.0 | 32 |
| mechvqa_q154 | 1 | 0.0741 | 46 |
| mechvqa_q155 | 1 | 0.1481 | 16.8 |
| mechvqa_q156 | 1 | 0.2963 | 剖视图中的厚度h与主视图中垫圈的厚度相关联，对应垫圈的厚度尺寸。 |
| mechvqa_q157 | 1 | 1.0 | 外径范围0.307~0.32英寸，内径范围0.151~0.164英寸，厚度范围0.027~0.048英寸。 |
| mechvqa_q158 | 1 | 0.2385 | 该剖面不是垂直于轴线的截面。 |
| mechvqa_q159 | 1 | 1.0 | 280±0.3 |
| mechvqa_q160 | 1 | 1.0 | Worm shaft end cover |
| mechvqa_q161 | 1 | 0.1515 | A型平垫圈 |
| mechvqa_q162 | 1 | 0.3125 | ISO 7051-2011 十字槽半沉头自攻螺钉C型 |
| mechvqa_q163 | 1 | 0.1053 | 9 mm |
| mechvqa_q164 | 1 | 0.0635 | 0.3165 |
| mechvqa_q165 | 1 | 0.0 | 2.0 |
| mechvqa_q166 | 1 | 0.1627 | 比值恒定（均为1.5）；工程意义为保证不同规格钩子的结构比例一致，利于标准化设计与制造。 |
| mechvqa_q167 | 1 | 0.0952 | 18 |
| mechvqa_q168 | 1 | 0.1689 | 差值为15，该差值反映零件外径与内部台阶结构的径向尺寸差异，体现零件的轮廓层次特征。 |
| mechvqa_q169 | 1 | 0.1728 | 10；计算依据是参数表格中l₂=27mm时对应的“Rollers per track”值为10。 |
| mechvqa_q170 | 1 | 0.1415 | d₁=30时h=28.5，d₁=40时h=28，h随d₁增大而减小，两者无近似比例关系。 |
| mechvqa_q171 | 1 | 0.0385 | 15 |
| mechvqa_q172 | 1 | 0.1333 | 11.5 |
| mechvqa_q173 | 1 | 1.0 | The (76) dimension is a reference dimension; it is not used  |
| mechvqa_q174 | 1 | 0.0 | 12mm |
| mechvqa_q175 | 1 | 0.0702 | 82.5 |
| mechvqa_q176 | 1 | 0.0488 | 4 |
| mechvqa_q177 | 1 | 0.0541 | 25 |
| mechvqa_q178 | 1 | 0.0465 | 45° |
| mechvqa_q179 | 1 | 1.0 | 80 |
| mechvqa_q180 | 1 | 0.0667 | 40 |
