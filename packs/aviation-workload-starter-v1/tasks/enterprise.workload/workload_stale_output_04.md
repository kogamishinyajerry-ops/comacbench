# workload stale output 04：工况输入到受约束文件与对账

## 场景

陈旧混入变体：输入带旧修订的 P0 结果。P0 不得进入 normalized/manifest，必须列入 exceptions。

输入文件：`assets/workload_stale_output_04_case.json`（JSON，含 case_id/version/rows；本包为合成数据）。
## 交付物（artifacts.v1）

读取输入工况 JSON，交付以下文件并写 manifest.json 声明：

1. `outputs/normalized.json` — 规范化记录：{"case_id": ..., "rows": [...]}；
   每行含 point、altitude_m（数值，米）、mass_flow_kg_s（数值，kg/s）、source_version。
2. `outputs/run_manifest.csv` — 运行清单：表头 point,case_id,version；仅含**被接受**的工况。
3. `outputs/exceptions.csv` — 异常清单：表头 point,reason,detail；被拒收/需澄清/陈旧的
   每一项都要有一行，理由具体到字段。

manifest.json 格式：
{"protocol": "comacbench.artifacts.v1", "deliverables": [
  {"path": "outputs/normalized.json", "kind": "normalized"},
  {"path": "outputs/run_manifest.csv", "kind": "run_manifest"},
  {"path": "outputs/exceptions.csv", "kind": "exceptions"}]}

## 判分边界

- 判分程序独立从文件内容复算；manifest 自评不影响分数。
- 单位缺失时猜测补全、矛盾重复时任选其一、陈旧结果混入清单，都是关键错误。
- 合法的等价表达（列序、小数位数）不受影响。
