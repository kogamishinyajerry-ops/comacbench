# code_exec 结果汇总（provider=glm, model=glm-4.6, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 164
- gate 通过: 163
- gate 失败: 1（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'code_not_executable': 1}

## pass@1（全部隐藏测试通过）

- 160/163 = 0.9816（physics=1.0 的任务占比；physics 均值含部分通过分，二者并读）

## physics（隐藏测试/数值） 分布（n=164）

- =1.0: 160
- 0.5-1.0: 1
- 0-0.5: 1
- =0.0: 2

## robustness（确定性） 分布（n=164）

- =1.0: 163
- 0.5-1.0: 0
- 0-0.5: 0
- =0.0: 1

## 每任务明细

| task | gate | physics | robust | score | 关键信息 |
| --- | --- | --- | --- | --- | --- |
| humaneval_000 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_001 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_002 | 1 | 1.0 | 1.0 | 1.0 | cases 3/3 |
| humaneval_003 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_004 | 1 | 1.0 | 1.0 | 1.0 | cases 3/3 |
| humaneval_005 | 1 | 1.0 | 1.0 | 1.0 | cases 3/3 |
| humaneval_006 | 1 | 1.0 | 1.0 | 1.0 | cases 3/3 |
| humaneval_007 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_008 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_009 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_010 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_011 | 1 | 1.0 | 1.0 | 1.0 | cases 3/3 |
| humaneval_012 | 1 | 1.0 | 1.0 | 1.0 | cases 3/3 |
| humaneval_013 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_014 | 1 | 1.0 | 1.0 | 1.0 | cases 3/3 |
| humaneval_015 | 1 | 1.0 | 1.0 | 1.0 | cases 3/3 |
| humaneval_016 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_017 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_018 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_019 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_020 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_021 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_022 | 1 | 1.0 | 1.0 | 1.0 | cases 3/3 |
| humaneval_023 | 1 | 1.0 | 1.0 | 1.0 | cases 3/3 |
| humaneval_024 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_025 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_026 | 1 | 1.0 | 1.0 | 1.0 | cases 3/3 |
| humaneval_027 | 1 | 1.0 | 1.0 | 1.0 | cases 3/3 |
| humaneval_028 | 1 | 1.0 | 1.0 | 1.0 | cases 3/3 |
| humaneval_029 | 1 | 1.0 | 1.0 | 1.0 | cases 2/2 |
| humaneval_030 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_031 | 1 | 1.0 | 1.0 | 1.0 | cases 13/13 |
| humaneval_032 | 0 | 0.0 | 0.0 | 0.0 |  |
| humaneval_033 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_034 | 1 | 1.0 | 1.0 | 1.0 | cases 1/1 |
| humaneval_035 | 1 | 1.0 | 1.0 | 1.0 | cases 2/2 |
| humaneval_036 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_037 | 1 | 1.0 | 1.0 | 1.0 | cases 3/3 |
| humaneval_038 | 1 | 1.0 | 1.0 | 1.0 | cases 1/1 |
| humaneval_039 | 1 | 1.0 | 1.0 | 1.0 | cases 10/10 |
| humaneval_040 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_041 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_042 | 1 | 1.0 | 1.0 | 1.0 | cases 3/3 |
| humaneval_043 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_044 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_045 | 1 | 1.0 | 1.0 | 1.0 | cases 3/3 |
| humaneval_046 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_047 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_048 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_049 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_050 | 1 | 0.0 | 1.0 | 0.5 | cases 0/1 |
| humaneval_051 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_052 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_053 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_054 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_055 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_056 | 1 | 1.0 | 1.0 | 1.0 | cases 12/12 |
| humaneval_057 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_058 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_059 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_060 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_061 | 1 | 1.0 | 1.0 | 1.0 | cases 12/12 |
| humaneval_062 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_063 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_064 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_065 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_066 | 1 | 1.0 | 1.0 | 1.0 | cases 10/10 |
| humaneval_067 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_068 | 1 | 1.0 | 1.0 | 1.0 | cases 10/10 |
| humaneval_069 | 1 | 1.0 | 1.0 | 1.0 | cases 25/25 |
| humaneval_070 | 1 | 1.0 | 1.0 | 1.0 | cases 10/10 |
| humaneval_071 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_072 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_073 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_074 | 1 | 1.0 | 1.0 | 1.0 | cases 11/11 |
| humaneval_075 | 1 | 1.0 | 1.0 | 1.0 | cases 10/10 |
| humaneval_076 | 1 | 1.0 | 1.0 | 1.0 | cases 10/10 |
| humaneval_077 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_078 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_079 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_080 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_081 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_082 | 1 | 1.0 | 1.0 | 1.0 | cases 16/16 |
| humaneval_083 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_084 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_085 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_086 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_087 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_088 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_089 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_090 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_091 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_092 | 1 | 1.0 | 1.0 | 1.0 | cases 10/10 |
| humaneval_093 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_094 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_095 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_096 | 1 | 1.0 | 1.0 | 1.0 | cases 10/10 |
| humaneval_097 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_098 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_099 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_100 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_101 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_102 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_103 | 1 | 1.0 | 1.0 | 1.0 | cases 12/12 |
| humaneval_104 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_105 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_106 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_107 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_108 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_109 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_110 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_111 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_112 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_113 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_114 | 1 | 1.0 | 1.0 | 1.0 | cases 12/12 |
| humaneval_115 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_116 | 1 | 1.0 | 1.0 | 1.0 | cases 10/10 |
| humaneval_117 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_118 | 1 | 1.0 | 1.0 | 1.0 | cases 14/14 |
| humaneval_119 | 1 | 1.0 | 1.0 | 1.0 | cases 12/12 |
| humaneval_120 | 1 | 1.0 | 1.0 | 1.0 | cases 11/11 |
| humaneval_121 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_122 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_123 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_124 | 1 | 1.0 | 1.0 | 1.0 | cases 16/16 |
| humaneval_125 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_126 | 1 | 1.0 | 1.0 | 1.0 | cases 13/13 |
| humaneval_127 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_128 | 1 | 1.0 | 1.0 | 1.0 | cases 10/10 |
| humaneval_129 | 1 | 1.0 | 1.0 | 1.0 | cases 11/11 |
| humaneval_130 | 1 | 1.0 | 1.0 | 1.0 | cases 10/10 |
| humaneval_131 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_132 | 1 | 0.7857 | 1.0 | 0.89285 | cases 11/14 |
| humaneval_133 | 1 | 1.0 | 1.0 | 1.0 | cases 12/12 |
| humaneval_134 | 1 | 1.0 | 1.0 | 1.0 | cases 11/11 |
| humaneval_135 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_136 | 1 | 1.0 | 1.0 | 1.0 | cases 12/12 |
| humaneval_137 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_138 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_139 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_140 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_141 | 1 | 1.0 | 1.0 | 1.0 | cases 26/26 |
| humaneval_142 | 1 | 1.0 | 1.0 | 1.0 | cases 11/11 |
| humaneval_143 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_144 | 1 | 1.0 | 1.0 | 1.0 | cases 13/13 |
| humaneval_145 | 1 | 0.2857 | 1.0 | 0.64285 | cases 2/7 |
| humaneval_146 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_147 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_148 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_149 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_150 | 1 | 1.0 | 1.0 | 1.0 | cases 10/10 |
| humaneval_151 | 1 | 1.0 | 1.0 | 1.0 | cases 7/7 |
| humaneval_152 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_153 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_154 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| humaneval_155 | 1 | 1.0 | 1.0 | 1.0 | cases 9/9 |
| humaneval_156 | 1 | 1.0 | 1.0 | 1.0 | cases 15/15 |
| humaneval_157 | 1 | 1.0 | 1.0 | 1.0 | cases 11/11 |
| humaneval_158 | 1 | 1.0 | 1.0 | 1.0 | cases 10/10 |
| humaneval_159 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_160 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| humaneval_161 | 1 | 1.0 | 1.0 | 1.0 | cases 8/8 |
| humaneval_162 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| humaneval_163 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
