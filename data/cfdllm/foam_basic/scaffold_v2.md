# cfdllm.foam_basic — H2/H3 脚手架 v2（结构层 + 物理层）

> 用途：harness 臂 H2v2/H3v2 prompt 注入件（`--scaffold data/cfdllm/foam_basic/scaffold_v2.md`）。
> v1（scaffold.md）只解「算例能跑」（结构层）；对实测失分的物理层（U 不相关 /
> p 场尺度爆炸）v2 补齐。蒸馏来源：v0.3 矩阵 H3 臂 NMSE 逐场审计 + GT 参考算例
> 结构审计（初始化约定/网格/时间推进——均为算例配置知识，不含任何任务的
> 参考输出值）。
> 防泄漏：worked example 参数（6×1×2 m、302/300 K、endTime 800）与全部 110 题
> 参数组合不同；判分仍要求模型按题面正确组装。

## 契约回顾

1. 输出**一个 python 脚本**（仅 os/math/builtins），在 cwd 写文件，不执行 OpenFOAM；
2. 齐备 `system/{controlDict,fvSchemes,fvSolution,blockMeshDict}`、`constant/…`、
   `0/…`、`Allrun`；controlDict 的 application 与 Allrun 一致；
3. **endTime / deltaT / writeInterval 按题面全量执行**（见陷阱 3——这是 v2 与
   v1 的关键差异）。

## 物理层纪律（v2 新增——每条都是实测失分根因）

1. **p 与 p_rgh 一律 gauge 0 初值**。buoyantFoam 在此约定下输出 O(0) 量级压力；
   写 1e5（绝对压）会让 p 场对参考的 NMSE 爆到 1e9 级（v1 实测失分形态）。
2. **U 初始场给微小扰动** `(1e-4 0 0)`。自然对流（Bernard cell 类）从对称初态
   出发永不失稳——U 保持零解 → U 场与参考完全不相关（NMSE≈1.0）。一个
   O(1e-4) 扰动就是触发对流胞发展的全部所需。
3. **endTime 用题面的物理时间，不要缩短**。对流胞需要时间生长到稳态；判分
   比对的是末态场。deltaT 取题面值（通常 1 s 已稳定），writeInterval 取题面值。
4. **网格：2D 为主**——frontAndBack 用 empty patch 时第三方向**恒为 1 段**
   （判分参考算例即 2D，如 90×10×1）；水平两向 ~10 cells/单位。**总格子数
   ≤5000**：墙钟限额 900s，qemu 模拟 docker 下粗于超时（粗网格可收敛，超时
   直接 0 分）。
5. **laminar 足够**（参考算例即层流设定）；不需要 k/epsilon/nut 文件，不需要 pRef。

## 最小可运行模式（buoyantFoam 热对流；数值按题面替换）

```python
import os

def w(path, text):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w") as f:
        f.write(text)

# 以 6 x 1 x 2 m 长方体、floor 302 K / ceiling 300 K、层流为例（# SUB = 按题面替换）
LX, LY, LZ = 6.0, 1.0, 2.0          # SUB: 域尺寸
T_HOT, T_COLD = 302.0, 300.0        # SUB: 壁温
DT, END, WRITE = 1.0, 800.0, 100.0  # SUB: 按题面全量（勿缩短 END——见纪律 3）
NX, NY, NZ = 60, 10, 1              # SUB: 网格（2D：Z 向恒 1 段；总格 ≤5000，见纪律 4）

w("system/controlDict", f"""FoamFile {{ format ascii; class dictionary; object controlDict; location "system/controlDict"; }}
application     buoyantFoam;
startFrom       latestTime;
startTime       0;
stopAt          endTime;
endTime         {END};
deltaT          {DT};
writeControl    runTime;
writeInterval   {WRITE};
purgeWrite      0;
writeFormat     ascii;
writePrecision  6;
timeFormat      general;
runTimeModifiable true;
""")

w("system/fvSchemes", """FoamFile { format ascii; class dictionary; object fvSchemes; location "system/fvSchemes"; }
ddtSchemes { default Euler; }
gradSchemes { default Gauss linear; }
divSchemes
{
    default none;
    div(phi,U)  bounded Gauss limitedLinear 0.2;
    div(phi,K)  bounded Gauss limitedLinear 0.2;
    div(phi,h)  bounded Gauss limitedLinear 0.2;
    div(phi,T)  bounded Gauss limitedLinear 0.2;
    div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes { default Gauss linear corrected; }
interpolationSchemes { default linear; }
snGradSchemes { default corrected; }
""")

w("system/fvSolution", """FoamFile { format ascii; class dictionary; object fvSolution; location "system/fvSolution"; }
solvers
{
    p_rgh { solver GAMG; tolerance 1e-7; relTol 0.01; smoother DICGaussSeidel; }
    p_rghFinal { solver GAMG; tolerance 1e-7; relTol 0; smoother DICGaussSeidel; }
    "(U|h|k|epsilon|omega)"
    {
        solver PBiCGStab; preconditioner DILU; tolerance 1e-8; relTol 0.1;
    }
    "(U|h|k|epsilon|omega)Final"
    {
        solver PBiCGStab; preconditioner DILU; tolerance 1e-8; relTol 0;
    }
    "(rho|rhoFinal)"
    {
        solver PBiCGStab; preconditioner DILU; tolerance 1e-8; relTol 0;
    }
}
PIMPLE
{
    momentumPredictor no;
    nNonOrthogonalCorrectors 0;
    pRefCell 0;
    pRefValue 0;
}
relaxationFactors { equations { ".*" 1; } }
""")

w("system/blockMeshDict", f"""FoamFile {{ format ascii; class dictionary; object blockMeshDict; location "system/blockMeshDict"; }}
convertToMeters 1;
vertices (
    (0 0 0) ({LX} 0 0) ({LX} {LY} 0) (0 {LY} 0)
    (0 0 {LZ}) ({LX} 0 {LZ}) ({LX} {LY} {LZ}) (0 {LY} {LZ})
);
blocks ( hex (0 1 2 3 4 5 6 7) ({NX} {NY} {NZ}) simpleGrading (1 1 1) );
boundary (
    bottom {{ type wall; faces ((0 1 5 4)); }}
    top    {{ type wall; faces ((3 2 6 7)); }}
    frontAndBack {{ type empty; faces ((0 1 2 3) (4 5 6 7)); }}
    inlet  {{ type patch; faces ((0 3 7 4)); }}
    outlet {{ type patch; faces ((1 2 6 5)); }}
);
""")

# OF10 buoyantFoam 读 constant/physicalProperties（含 thermoType，与官方 buoyantCavity 同构）
w("constant/physicalProperties", """FoamFile { format ascii; class dictionary; object physicalProperties; location "constant/physicalProperties"; }
thermoType
{
    type            heRhoThermo;
    mixture         pureMixture;
    transport       const;
    thermo          hConst;
    equationOfState perfectGas;
    specie          specie;
    energy          sensibleEnthalpy;
}
mixture
{
    specie { molWeight 28.96; }
    thermodynamics { Cp 1004.4; Hf 0; }
    transport { mu 1.831e-05; Pr 0.705; }
}
""")

w("constant/momentumTransport", """FoamFile { format ascii; class dictionary; object momentumTransport; location "constant/momentumTransport"; }
simulationType laminar;
""")

w("constant/turbulenceProperties", """FoamFile { format ascii; class dictionary; object turbulenceProperties; location "constant/turbulenceProperties"; }
simulationType laminar;
""")

w("constant/g", """FoamFile { format ascii; class uniformDimensionedVectorField; object g; location "constant/g"; }
dimensions [0 1 -2 0 0 0 0];
value (0 -9.81 0);
""")

# 字段头用字符串拼接（嵌套 f-string 三引号极易抄错——实证陷阱 8）
def field(name, cls, dims, internal, bd):
    head = ('FoamFile { format ascii; class ' + cls + '; object ' + name
            + '; location "0/' + name + '"; }')
    return (head + '\ndimensions ' + str(dims) + ';'
            + '\ninternalField uniform ' + str(internal) + ';'
            + '\nboundaryField\n{\n' + bd + '\n}\n')

hot = f"type fixedValue; value uniform {T_HOT};"
cold = f"type fixedValue; value uniform {T_COLD};"

w("0/T", field("T", "volScalarField", "[0 0 0 1 0 0 0]", T_COLD, f"""
    bottom {{ {hot} }}
    top {{ {cold} }}
    frontAndBack {{ type empty; }}
    inlet {{ {cold} }}
    outlet {{ type inletOutlet; inletValue uniform {T_COLD}; value uniform {T_COLD}; }}
"""))

# 纪律 1/2：gauge 压力 + 微扰初速
w("0/U", field("U", "volVectorField", "[0 1 -1 0 0 0 0]", "(1e-4 0 0)", """
    bottom { type noSlip; }
    top { type noSlip; }
    frontAndBack { type empty; }
    inlet { type fixedValue; value uniform (1e-4 0 0); }
    outlet { type pressureInletOutletVelocity; value uniform (1e-4 0 0); }
"""))

w("0/p_rgh", field("p_rgh", "volScalarField", "[1 -1 -2 0 0 0 0]", "0", """
    bottom { type fixedFluxPressure; value uniform 0; }
    top { type fixedFluxPressure; value uniform 0; }
    frontAndBack { type empty; }
    inlet { type fixedFluxPressure; value uniform 0; }
    outlet { type fixedValue; value uniform 0; }
"""))

w("0/p", field("p", "volScalarField", "[1 -1 -2 0 0 0 0]", "0", """
    bottom { type calculated; value uniform 0; }
    top { type calculated; value uniform 0; }
    frontAndBack { type empty; }
    inlet { type calculated; value uniform 0; }
    outlet { type calculated; value uniform 0; }
"""))

w("0/alphat", field("alphat", "volScalarField", "[1 -1 -1 0 0 0 0]", "0", """
    bottom { type alphatWallFunction; Prt 0.85; value uniform 0; }
    top { type alphatWallFunction; Prt 0.85; value uniform 0; }
    frontAndBack { type empty; }
    inlet { type calculated; value uniform 0; }
    outlet { type calculated; value uniform 0; }
"""))

w("Allrun", """#!/bin/sh
. $WM_PROJECT_DIR/bin/tools/RunFunctions
runApplication blockMesh
runApplication buoyantFoam
""")

os.chmod("Allrun", 0o755)
```

## 陷阱清单（v1 全部保留 + v2 物理层）

1. FoamFile 头必须含 `object <名>;`（OF10 严格校验）。
2. `#` 在 OF 字典里不是注释（functionEntry 语法）——注释用 `//`。
3. blockMeshDict 边界名与 0/ 场 boundaryField 逐名一致。
4. frontAndBack `empty` 类型时所有场都要有该 patch 的 `type empty;` 条目。
5. buoyantFoam 压力场是 `p_rgh`；thermoType 用上面 heRhoThermo 完整形态
   （`specie specie;` 是必需条目）。
6. **v2-物理**：p/p_rgh gauge 0；U 微扰 (1e-4 0 0)；endTime 全量；网格
   ~10 cells/单位——四条任缺其一都会「跑到 End 但场不相关」。
7. 只用 os/math/builtins；脚本不 import openfoam、不 subprocess（写了判
   sandbox_escape_attempt）。
8. **别用嵌套 f-string 三引号写字典**（FoamFile 头 + 多插值点极易抄错——
   v2 实测 M3 三连语法错误全在此）：字段文件一律用上面的字符串拼接 helper。
