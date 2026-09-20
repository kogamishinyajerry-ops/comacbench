# 工程知识本体：对象、关系和来源（虚构企业记录）

实现 Python 函数 `build_graph(entities, assertions)`，返回 {"edges": [...], "issues": [...]}。
entities 是唯一非空字符串 id 与 type 对象列表；type 属于 Part/Material/Analysis/Requirement。
assertions 是 subject/relation/object/source_id 对象列表，可能缺字段。
合法关系及首尾类型：made_of: Part→Material；verified_by: Part→Analysis；satisfies: Analysis→Requirement。

每条 assertion 按以下优先顺序校验，首个失败原因写入 issues：
1. source_id 不是非空字符串：missing_source（source_id 输出空字符串）。
2. relation 不在三个合法关系中：unknown_relation。
3. subject 或 object 未在 entities 声明：missing_entity，禁止自行补造实体。
4. 首尾类型与上述签名不符：type_mismatch。
合法边按 (subject,relation,object) 去重；证据 source_id 精确保留、去重并排序。
每条边只含 subject/relation/object/evidence；边按 (subject,relation,object) 排序。
每条 issue 只含 source_id/reason，按 (source_id,reason) 排序；重复问题全部保留。
不能臆造关系，不能忽略缺失证据。ID 区分大小写，保留前导零。输入不得被修改。
空输入返回两个空列表。返回完整 Python 源码，可使用标准库。
