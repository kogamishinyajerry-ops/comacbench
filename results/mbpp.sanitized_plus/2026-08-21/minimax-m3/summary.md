# code_exec 结果汇总（provider=minimax, model=MiniMax-M3, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 222
- gate 通过: 222
- gate 失败: 0（直接 0 分）
- 作废: 0
- gate 失败原因分布: 无

## pass@1（全部隐藏测试通过）

- 182/222 = 0.8198（physics=1.0 的任务占比；physics 均值含部分通过分，二者并读）

## physics（隐藏测试/数值） 分布（n=222）

- =1.0: 182
- 0.5-1.0: 37
- 0-0.5: 3
- =0.0: 0

## robustness（确定性） 分布（n=222）

- =1.0: 222
- 0.5-1.0: 0
- 0-0.5: 0
- =0.0: 0

## 每任务明细

| task | gate | physics | robust | score | 关键信息 |
| --- | --- | --- | --- | --- | --- |
| mbpp_plus_011 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_012 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_014 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_016 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_017 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_018 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_019 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_020 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_056 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_057 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_058 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| mbpp_plus_059 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_061 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_062 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_063 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_064 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_065 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_066 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_067 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_068 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_069 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_070 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_071 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_072 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_074 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_075 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_077 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_079 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_080 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_082 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_084 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_085 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_086 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_087 | 1 | 0.5 | 1.0 | 0.75 | cases 2/4 |
| mbpp_plus_088 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_089 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_090 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_091 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_092 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_093 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_094 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_095 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_096 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_097 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_098 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_099 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_100 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_101 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_102 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_103 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_104 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_105 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_106 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_108 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_109 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_111 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_113 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_116 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_118 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_119 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_120 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_123 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_125 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_126 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_127 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_128 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_129 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_130 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_131 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_132 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_133 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_135 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_137 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_138 | 1 | 0.5 | 1.0 | 0.75 | cases 2/4 |
| mbpp_plus_139 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_140 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_141 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_142 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_145 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_160 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_161 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_162 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| mbpp_plus_165 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_166 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_167 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_168 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_170 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_171 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_172 | 1 | 1.0 | 1.0 | 1.0 | cases 6/6 |
| mbpp_plus_222 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_223 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_224 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_226 | 1 | 1.0 | 1.0 | 1.0 | cases 5/5 |
| mbpp_plus_227 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_230 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_232 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_233 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_234 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_235 | 1 | 0.25 | 1.0 | 0.625 | cases 1/4 |
| mbpp_plus_237 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_238 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_239 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_240 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_242 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_244 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_245 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_247 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_250 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_251 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_253 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_255 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_256 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_257 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_259 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_260 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_261 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_262 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_264 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_265 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_266 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_267 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_268 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_269 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_270 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_271 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_272 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_273 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_274 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_276 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_277 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_278 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_279 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_280 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_281 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_282 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_283 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_284 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_285 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_286 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_287 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_290 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_292 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_293 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_294 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_296 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_297 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_299 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_300 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_301 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_305 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_306 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_308 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_309 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_310 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_311 | 1 | 0.5 | 1.0 | 0.75 | cases 2/4 |
| mbpp_plus_312 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_388 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_389 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_390 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_391 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_392 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_394 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_395 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_397 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_398 | 1 | 0.25 | 1.0 | 0.625 | cases 1/4 |
| mbpp_plus_404 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_405 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_406 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_409 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_410 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_412 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_413 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_414 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_415 | 1 | 0.5 | 1.0 | 0.75 | cases 2/4 |
| mbpp_plus_418 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_419 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_420 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_421 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_422 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_424 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_425 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_426 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_427 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_428 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_429 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_430 | 1 | 0.25 | 1.0 | 0.625 | cases 1/4 |
| mbpp_plus_432 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_433 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_435 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_436 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_437 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_439 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_440 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_441 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_445 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_446 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_447 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_448 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_450 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_451 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_453 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_454 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_455 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_456 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_457 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_458 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_459 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_460 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_462 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_463 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_465 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_468 | 1 | 0.75 | 1.0 | 0.875 | cases 3/4 |
| mbpp_plus_470 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_471 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_472 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_473 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_474 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_475 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_476 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_477 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_478 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
| mbpp_plus_479 | 1 | 1.0 | 1.0 | 1.0 | cases 4/4 |
