# cadgen.local_validity — H2/H3 脚手架（蒸馏工作流资产 v1）

> 用途：harness 臂 H2/H3 的 prompt 注入件（目标参数 `--scaffold data/cadgen/local_validity/scaffold.md`）。
> 蒸馏来源：`runners/gen_tasks_cadgen.py` 参数化族 + 本 harness 审计的模型失败模式（M3/GLM-4.6
> 在 **lbracket 族 0.25**、plate/shaft/bossplate 边倒圆与通孔序上也翻车）+ gold 脚本的
> 可靠构造序列（构造序列是公开几何常识，不复制任何 gold 的判分参考值）。
> 防泄漏纪律：worked example 尺寸全部自造（74/52/9/31/11/14 等），经 grep 验证不与 22 题
> 任何 reference.values（体积/包围盒三边）重合；本文件不含任何任务的判分参考数值。
> 资产自检：三族骨架代码从本文件原样提取，在 `.venv-cad` 裸跑导出合法 STEP（BRepCheck
> 通过、体积>0、两次执行体积/包围盒 1e-6 一致）后才定稿。

## 你要做的事

任务全部是：用已装好的 `cadquery`（`import cadquery as cq`）构造一个**单一实体**，在 cwd
导出 `part.step`（`cq.exporters.export(shape, "part.step")`）。判分是纯本地客观测量：
STEP 可解析 + B-Rep 有效 + 体积>0 → **重复执行两次要复现同一制品（体积/包围盒 1e-6 相对
一致）** → 体积 + 包围盒三边对 gold 预计算参考的 1% 相对误差（各占 1/4）→ 接口检查
（圆柱面数/半径 ±1%、总面数精确）。失败几乎都出在：**多特征定位顺序、圆角/孔的先后、
实体布尔退化（共面切割）**。按下面的骨架写就能避开。

## 可运行的完整骨架（示例参数与任何考题不同）

### A. L 角支架（内圆角 + 两腿孔）—— 主靶，失败率最高

可靠序列：**单 sketch（XZ 工作平面）画含内圆角的 L 形截面 → extrude 出宽度 → 圆角直接
画进截面（用 `threePointArc`，不用事后 fillet）→ 两腿孔用略超长的圆柱 cut（避免共面退化）**。

```python
import cadquery as cq

LEG_X = 74.0      # 水平腿沿 +X
H = 52.0          # 竖直腿沿 +Z
T = 9.0           # 腿厚
WID = 31.0        # 两腿共享宽度沿 +Y
FILLET_R = 11.0   # 内凹圆角
HOLE_D = 14.0     # 腿孔直径
HX = T + (LEG_X - T) / 2.0     # 水平腿孔 X 中心
VZ = T + (H - T) / 2.0         # 竖直腿孔 Z 中心
OVER = 1.0                    # 切割圆柱超出材料量，防共面布尔退化

profile = (cq.Workplane("XZ")
           .moveTo(0.0, 0.0).lineTo(LEG_X, 0.0).lineTo(LEG_X, T)
           .lineTo(T + FILLET_R, T)
           .threePointArc((T + FILLET_R - FILLET_R / (2.0 ** 0.5),
                           T + FILLET_R - FILLET_R / (2.0 ** 0.5)),
                          (T, T + FILLET_R))
           .lineTo(T, H).lineTo(0.0, H).close().extrude(WID))
solid = profile.val()
if solid.Center().y < 0.0:                      # 若截面让实体落在 -Y，移到正侧
    solid = solid.translate(cq.Vector(0.0, WID, 0.0))
hole_h = cq.Solid.makeCylinder(HOLE_D / 2.0, T + 2.0 * OVER,
                               cq.Vector(HX, WID / 2.0, -OVER), cq.Vector(0.0, 0.0, 1.0))
hole_v = cq.Solid.makeCylinder(HOLE_D / 2.0, T + 2.0 * OVER,
                               cq.Vector(-OVER, WID / 2.0, VZ), cq.Vector(1.0, 0.0, 0.0))
solid = solid.cut(hole_h).cut(hole_v)
cq.exporters.export(solid, "part.step")
```

要点：`threePointArc` 的两端分别是内角两条边的终点；圆角**画进截面**就计为 1 个圆柱面，
不碰 fillet 选边。孔轴方向：水平腿孔沿 Z（`Vector(0,0,1)`），竖直腿孔沿 X（`Vector(1,0,0)`）。

### B. 阶梯轴 + 中心通孔

取舍：**逐段圆柱 `union`（每段在自身 offset 工作平面起草图）比单 sketch 多台阶 extrude
更不易错**；通孔统一从顶面 `faces(">Z")` 起 `cutThruAll()`（方向单一，无歧义）。

```python
import cadquery as cq

SEGMENTS = [(38.0, 22.0), (30.0, 18.0), (22.0, 14.0)]  # (直径, 长度)，沿 +Z 堆叠
BORE_D = 10.0

part = cq.Workplane("XY")
_z = 0.0
for _d, _l in SEGMENTS:
    _seg = cq.Workplane("XY").workplane(offset=_z).circle(_d / 2.0).extrude(_l)
    part = _seg if _z == 0.0 else part.union(_seg)
    _z += _l
part = part.faces(">Z").workplane().circle(BORE_D / 2.0).cutThruAll()
cq.exporters.export(part.val(), "part.step")
```

### C. 带凸台底板

可靠序列：**先底板 `rect().extrude` → 后凸台 `faces(">Z").circle().extrude` → 最后
`faces(">Z").pushPoints([...]).circle().cutThruAll()` 打四孔**。凸台必须先于打孔（孔通
不过凸台之外），孔贯穿 `cutThruAll`（只穿底板厚度，底板比凸台薄所以天然不切凸台）。

```python
import cadquery as cq

L = 88.0; W = 58.0; T = 11.0
BOSS_D = 26.0; BOSS_H = 14.0; HOLE_D = 12.0; INSET = 13.0

part = (cq.Workplane("XY").rect(L, W).extrude(T)
        .faces(">Z").workplane().circle(BOSS_D / 2.0).extrude(BOSS_H)
        .faces(">Z").workplane()
        .pushPoints([(-L / 2.0 + INSET, -W / 2.0 + INSET),
                     (L / 2.0 - INSET, -W / 2.0 + INSET),
                     (-L / 2.0 + INSET, W / 2.0 - INSET),
                     (L / 2.0 - INSET, W / 2.0 - INSET)])
        .circle(HOLE_D / 2.0).cutThruAll())
cq.exporters.export(part.val(), "part.step")
```

### 附：其余三族的可靠序列（各一句）

- **套筒/环形件**：`Workplane("XY").circle(OD/2).circle(ID/2).extrude(h)` —— 内外圆同 sketch 一次 extrude。
- **圆法兰+螺栓孔环**：`circle().extrude` 后 `faces(">Z").polarArray(PCD/2, 0, 360, n).circle(hole_d/2).cutThruAll()`，首孔 +X。
- **矩形板+四角孔+边倒圆**：`rect().extrude` → **先 `.edges("|Z").fillet(r)` 倒竖边圆角 → 再 `.faces(">Z").pushPoints(四角).circle().cutThruAll()` 打孔**（圆角先于孔，孔后于圆角）。

## 已知陷阱（本 harness 审计实证的失败点）

1. **双执行一致性是硬 gate**：禁 `random`/`time` 函数。本机 `time.time_ns()` 低三位恒为 0
   （毫秒粒度）——用它做「随机」实为确定，但依赖 pid/时间做随机尺寸会直接判
   **nondeterministic_artifact**（gate 第 5 级，0 分）。所有参数写死。
2. **导出格式**：必须 `cq.exporters.export(shape, "part.step")`（不是 `exportStep`，
   不是 `write`），文件名严格 `part.step`，导出在 cwd。传 `solid`/`part.val()` 都行，
   但必须是单一实体（`val()` 取 Solid，别传 Workplane）。
3. **体积由 gold 锁定 1% 判分**：physics 四分量（体积+三边）各 1/4，任何一边差超 1%
   就丢分。**几何尺寸必须逐字照题面**——含薄板厚度、孔心坐标（`+/-` 值）、PCD、
   圆角半径；估算「差不多」的体积必偏，宁可把题面数字原样写成常量。
4. **共面布尔退化**：切割圆柱与材料等长时，圆柱端面与实体表面共面可能产生退化/失效
   B-Rep。孔类切割让圆柱**略超出**材料（如 `T + 2*OVER`）而非精确齐平。
5. **圆角/孔顺序**（lbracket、plate 翻车主因）：圆角与孔的顺序必须匹配 gold 的面数预期
   —— 竖边圆角先于孔（plate）；L 支架内圆角直接画进截面不用事后 fillet（lbracket）。
   乱序会改 `n_faces_total` 或圆柱面数，接口检查精确判 0。
6. **面/圆柱面精确匹配**：接口检查 `n_faces_total` 是**精确**相等，圆柱面半径 ±1%。多做
   一个倒角/圆角、少画一个孔、把通孔做成沉头，都会改面数而整条 requirements 判 0。
7. **单一实体、单一 ```python 块**：只输出一个 fenced `python` 代码块，别加解释文字、别
   拆多块、别 import 任务外的库（判分沙箱只有 `cadquery`/`math`）。
