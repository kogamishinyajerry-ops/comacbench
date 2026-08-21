# code_exec 结果汇总（provider=glm, model=glm-4.6, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 164
- gate 通过: 164
- gate 失败: 0（直接 0 分）
- 作废: 0
- gate 失败原因分布: 无

## pass@1（全部隐藏测试通过）

- 151/164 = 0.9207（physics=1.0 的任务占比；physics 均值含部分通过分，二者并读）

## physics（隐藏测试/数值） 分布（n=164）

- =1.0: 151
- 0.5-1.0: 12
- 0-0.5: 1
- =0.0: 0

## robustness（确定性） 分布（n=164）

- =1.0: 164
- 0.5-1.0: 0
- 0-0.5: 0
- =0.0: 0

## 每任务明细

| task | gate | physics | robust | score | 关键信息 |
| --- | --- | --- | --- | --- | --- |
| humaneval_plus_000 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_plus_001 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_plus_002 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_plus_003 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_plus_004 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_plus_005 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_plus_006 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_plus_007 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_plus_008 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_plus_009 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_plus_010 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_plus_011 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_plus_012 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_plus_013 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_plus_014 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_plus_015 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_plus_016 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_plus_017 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_plus_018 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_plus_019 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_plus_020 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_plus_021 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_plus_022 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_plus_023 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_plus_024 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_plus_025 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_plus_026 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_plus_027 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_plus_028 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_plus_029 | 1 | 1.0 | 1.0 | 1.0 | cases 3/3 |
| humaneval_plus_030 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_plus_031 | 1 | 1.0 | 1.0 | 1.0 | cases 14/14 |
| humaneval_plus_032 | 1 | 0.5 | 1.0 | 0.75 | cases 1/2 |
| humaneval_plus_033 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_plus_034 | 1 | 1.0 | 1.0 | 1.0 | cases 2/2 |
| humaneval_plus_035 | 1 | 1.0 | 1.0 | 1.0 | cases 3/3 |
| humaneval_plus_036 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_plus_037 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_plus_038 | 1 | 1.0 | 1.0 | 1.0 | cases 2/2 |
| humaneval_plus_039 | 1 | 1.0 | 1.0 | 1.0 | cases 11/11 |
| humaneval_plus_040 | 1 | 1.0 | 1.0 | 1.0 | cases 10/10 |
| humaneval_plus_041 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_plus_042 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_plus_043 | 1 | 1.0 | 1.0 | 1.0 | cases 10/10 |
| humaneval_plus_044 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_plus_045 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_plus_046 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_plus_047 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_plus_048 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_plus_049 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_plus_050 | 1 | 0.5 | 1.0 | 0.75 | cases 1/2 |
| humaneval_plus_051 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_plus_052 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_plus_053 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_plus_054 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_plus_055 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_plus_056 | 1 | 1.0 | 1.0 | 1.0 | cases 13/13 |
| humaneval_plus_057 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_plus_058 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_plus_059 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_plus_060 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_plus_061 | 1 | 1.0 | 1.0 | 1.0 | cases 13/13 |
| humaneval_plus_062 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_plus_063 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_plus_064 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_plus_065 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_plus_066 | 1 | 1.0 | 1.0 | 1.0 | cases 11/11 |
| humaneval_plus_067 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_plus_068 | 1 | 1.0 | 1.0 | 1.0 | cases 11/11 |
| humaneval_plus_069 | 1 | 1.0 | 1.0 | 1.0 | cases 26/26 |
| humaneval_plus_070 | 1 | 1.0 | 1.0 | 1.0 | cases 11/11 |
| humaneval_plus_071 | 1 | 1.0 | 1.0 | 1.0 | cases 10/10 |
| humaneval_plus_072 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_plus_073 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_plus_074 | 1 | 1.0 | 1.0 | 1.0 | cases 12/12 |
| humaneval_plus_075 | 1 | 1.0 | 1.0 | 1.0 | cases 11/11 |
| humaneval_plus_076 | 1 | 0.9091 | 1.0 | 0.95455 | cases 10/11 |
| humaneval_plus_077 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_plus_078 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_plus_079 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_plus_080 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_plus_081 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_plus_082 | 1 | 1.0 | 1.0 | 1.0 | cases 17/17 |
| humaneval_plus_083 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_plus_084 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_plus_085 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_plus_086 | 1 | 0.8889 | 1.0 | 0.94445 | cases 8/9 |
| humaneval_plus_087 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_plus_088 | 1 | 1.0 | 1.0 | 1.0 | cases 10/10 |
| humaneval_plus_089 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_plus_090 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_plus_091 | 1 | 0.875 | 1.0 | 0.9375 | cases 7/8 |
| humaneval_plus_092 | 1 | 1.0 | 1.0 | 1.0 | cases 11/11 |
| humaneval_plus_093 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_plus_094 | 1 | 1.0 | 1.0 | 1.0 | cases 10/10 |
| humaneval_plus_095 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_plus_096 | 1 | 1.0 | 1.0 | 1.0 | cases 11/11 |
| humaneval_plus_097 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_plus_098 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_plus_099 | 1 | 0.8333 | 1.0 | 0.91665 | cases 5/6 |
| humaneval_plus_100 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_plus_101 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_plus_102 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_plus_103 | 1 | 1.0 | 1.0 | 1.0 | cases 13/13 |
| humaneval_plus_104 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_plus_105 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_plus_106 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_plus_107 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_plus_108 | 1 | 1.0 | 1.0 | 1.0 | cases 10/10 |
| humaneval_plus_109 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_plus_110 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_plus_111 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_plus_112 | 1 | 1.0 | 1.0 | 1.0 | cases 10/10 |
| humaneval_plus_113 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_plus_114 | 1 | 1.0 | 1.0 | 1.0 | cases 13/13 |
| humaneval_plus_115 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_plus_116 | 1 | 0.4545 | 1.0 | 0.72725 | cases 5/11 |
| humaneval_plus_117 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_plus_118 | 1 | 1.0 | 1.0 | 1.0 | cases 15/15 |
| humaneval_plus_119 | 1 | 1.0 | 1.0 | 1.0 | cases 13/13 |
| humaneval_plus_120 | 1 | 1.0 | 1.0 | 1.0 | cases 12/12 |
| humaneval_plus_121 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_plus_122 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_plus_123 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_plus_124 | 1 | 0.9412 | 1.0 | 0.9706 | cases 16/17 |
| humaneval_plus_125 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_plus_126 | 1 | 1.0 | 1.0 | 1.0 | cases 14/14 |
| humaneval_plus_127 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_plus_128 | 1 | 1.0 | 1.0 | 1.0 | cases 11/11 |
| humaneval_plus_129 | 1 | 1.0 | 1.0 | 1.0 | cases 12/12 |
| humaneval_plus_130 | 1 | 1.0 | 1.0 | 1.0 | cases 11/11 |
| humaneval_plus_131 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_plus_132 | 1 | 0.7333 | 1.0 | 0.86665 | cases 11/15 |
| humaneval_plus_133 | 1 | 1.0 | 1.0 | 1.0 | cases 13/13 |
| humaneval_plus_134 | 1 | 0.8333 | 1.0 | 0.91665 | cases 10/12 |
| humaneval_plus_135 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_plus_136 | 1 | 1.0 | 1.0 | 1.0 | cases 13/13 |
| humaneval_plus_137 | 1 | 1.0 | 1.0 | 1.0 | cases 10/10 |
| humaneval_plus_138 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_plus_139 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_plus_140 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_plus_141 | 1 | 0.963 | 1.0 | 0.9815 | cases 26/27 |
| humaneval_plus_142 | 1 | 1.0 | 1.0 | 1.0 | cases 12/12 |
| humaneval_plus_143 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_plus_144 | 1 | 1.0 | 1.0 | 1.0 | cases 14/14 |
| humaneval_plus_145 | 1 | 0.5 | 1.0 | 0.75 | cases 4/8 |
| humaneval_plus_146 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_plus_147 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_plus_148 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_plus_149 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_plus_150 | 1 | 1.0 | 1.0 | 1.0 | cases 11/11 |
| humaneval_plus_151 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_plus_152 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_plus_153 | 1 | 1.0 | 1.0 | 1.0 | cases 10/10 |
| humaneval_plus_154 | 1 | 0.8571 | 1.0 | 0.92855 | cases 6/7 |
| humaneval_plus_155 | 1 | 1.0 | 1.0 | 1.0 | cases 10/10 |
| humaneval_plus_156 | 1 | 1.0 | 1.0 | 1.0 | cases 16/16 |
| humaneval_plus_157 | 1 | 1.0 | 1.0 | 1.0 | cases 12/12 |
| humaneval_plus_158 | 1 | 1.0 | 1.0 | 1.0 | cases 11/11 |
| humaneval_plus_159 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_plus_160 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_plus_161 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_plus_162 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_plus_163 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
