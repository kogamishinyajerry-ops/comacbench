# 工程数据清洗与单位归一（虚构企业数据）

实现 Python 函数 `normalize_records(records)`，不要进行文件或网络操作。
输入为记录对象列表，包含 record_id、part_id、source_id、length、unit。
输出为 {"accepted": [...], "rejected": [...]}，输入不得被修改。

逐条按以下优先顺序判定（一次只给首个原因）：
1. record_id 不是非空字符串：拒绝 missing_id，输出 record_id=""。
2. 非空 record_id 在整个输入重复：所有同 ID 行拒绝 duplicate_id，禁止只保留一条。
3. part_id 或 source_id 不是非空字符串：拒绝 missing_lineage。
4. unit 不为精确小写 mm 或 m：拒绝 unknown_unit，禁止猜测单位。
5. length 不是有限正数或是布尔值：拒绝 invalid_length。
其余接受，m 乘以 1000 转成 length_mm；mm 原值。ID 是标识符，保留大小写及前导零。
accepted 行只含 record_id/part_id/source_id/length_mm；按 record_id 字典序排序。
rejected 行只含 record_id/reason；按 (record_id, reason) 排序，重复拒绝行全部保留。
空输入返回两个空列表。

例如长度 0.25 m 应变为 250 mm，source_id 原样保留。返回完整 Python 源码，可使用标准库。
