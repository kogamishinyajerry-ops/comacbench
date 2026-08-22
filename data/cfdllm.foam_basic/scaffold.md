# cfdllm.foam_basic — H2/H3 脚手架（蒸馏工作流资产 v1）

> 用途：harness 臂 H2/H3 prompt 注入件（`--scaffold data/cfdllm.foam_basic/scaffold.md`）。
> 蒸馏来源：本 harness 审计的失败模式（脚本级崩溃 87/110 + 求解未完成 23/110）+
> 判分器事实：docker OpenFOAM 10 (Foundation) 内 `bash -c "./Allrun"`，成功判据 =
> `log.<solver>` 倒数第二行 == `End` 且至少写出一个时间目录。
> 防泄漏：给的是最小可收敛模式（以 Bernard cell / buoyantFoam 为形），不含任何
> 考题的边界数值答案；考题仍要求按题面正确组装物理与参数。

## 契约回顾（先做对这三件事）

1. 输出**一个 python 脚本**（仅 os/math/builtins），在 cwd **写文件**，不执行任何
   OpenFOAM 命令；
2. 必须齐备：`system/{controlDict,fvSchemes,fvSolution,blockMeshDict}`、
   `constant/...`、`0/...`、`Allrun`；
3. `controlDict` 的 `application` 必须与 Allrun 里 `runApplication <solver>` 一致。

## 最小可运行模式（buoyantFoam 热对流；数值按题面替换）

```python
import os

def w(path, text):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w") as f:
        f.write(text)

# 以 9 x 1 x 2 m 长方体、上下壁 300/301 K、层流为例（题面数值替换处标 # SUB）
LX, LY, LZ = 9.0, 1.0, 2.0          # SUB: 域尺寸
T_HOT, T_COLD = 301.0, 300.0        # SUB: 壁温
DT, END, WRITE = 1.0, 50.0, 10.0    # SUB: 判分只要求快速跑完+写出时间目录

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
blocks ( hex (0 1 2 3 4 5 6 7) ({int(LX*4)} {int(LY*2)} {int(LZ*4)}) simpleGrading (1 1 1) );
boundary (
    bottom {{ type wall; faces ((0 1 5 4)); }}
    top    {{ type wall; faces ((3 2 6 7)); }}
    frontAndBack {{ type empty; faces ((0 1 2 3) (4 5 6 7)); }}
    inlet  {{ type patch; faces ((0 3 7 4)); }}
    outlet {{ type patch; faces ((1 2 6 5)); }}
);
""")

# OF10 buoyantFoam 读 constant/physicalProperties（含 thermoType，官方 buoyantCavity 同构）
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

w("constant/pRef", """FoamFile { format ascii; class uniformDimensionedScalarField; object pRef; location "constant/pRef"; }
dimensions [1 -1 -2 0 0 0 0];
value 1e5;
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

def field(name, cls, dims, internal, bd):
    return f"""FoamFile {{ format ascii; class {cls}; object {name}; location "0/{name}"; }}
dimensions {dims};
internalField uniform {internal};
boundaryField {{ {bd} }}"""

hot = f"type fixedValue; value uniform {T_HOT};"
cold = f"type fixedValue; value uniform {T_COLD};"

w("0/T", field("T", "volScalarField", "[0 0 0 1 0 0 0]", T_COLD, f"""
    bottom {{ {hot} }}
    top {{ {cold} }}
    frontAndBack {{ type empty; }}
    inlet {{ {cold} }}
    outlet {{ type inletOutlet; inletValue uniform {T_COLD}; value uniform {T_COLD}; }}
"""))

w("0/U", field("U", "volVectorField", "[0 1 -1 0 0 0 0]", "(0 0 0)", """
    bottom { type noSlip; }
    top { type noSlip; }
    frontAndBack { type empty; }
    inlet { type fixedValue; value uniform (0 0 0); }
    outlet { type pressureInletOutletVelocity; value uniform (0 0 0); }
"""))

w("0/p_rgh", field("p_rgh", "volScalarField", "[1 -1 -2 0 0 0 0]", "1e5", """
    bottom { type fixedFluxPressure; value uniform 1e5; }
    top { type fixedFluxPressure; value uniform 1e5; }
    frontAndBack { type empty; }
    inlet { type fixedFluxPressure; value uniform 1e5; }
    outlet { type fixedValue; value uniform 1e5; }
"""))

w("0/p", field("p", "volScalarField", "[1 -1 -2 0 0 0 0]", "1e5", """
    bottom { type calculated; value uniform 1e5; }
    top { type calculated; value uniform 1e5; }
    frontAndBack { type empty; }
    inlet { type calculated; value uniform 1e5; }
    outlet { type calculated; value uniform 1e5; }
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

## 已知陷阱（本 harness 审计实证的失败点）

1. **blockMeshDict 边界名与 0/ 场 boundaryField 逐名一致**——多一个少一个都直接崩。
2. **frontAndBack 用 `empty` 类型**（2D 效果）时 blockMesh 该方向分段数 ≥1 且所有场
   都要有该 patch 的 `type empty;` 条目。
3. **buoyantFoam 压力场是 `p_rgh` 不是 `p`**；湍流关闭时 `alphat` 仍需要（层流给 0）。
4. **controlDict endTime 先小后大**：判分只要求「跑完 + 至少一个时间目录」，把 endTime
   收到能快速完成的值（题面允许），不要真跑题面物理时间。
5. Allrun 用 `. $WM_PROJECT_DIR/bin/tools/RunFunctions`（POSIX 句点；判分器虽用 bash，
   `.` 两边都成立）；`runApplication` 会自动写 `log.<solver>`。
6. **FoamFile 头必须含 `object <名>;`**（OF10 严格校验，缺失即 FATAL IO ERROR）；
7. 只用 os/math/builtins；**脚本里不 import openfoam、不 subprocess**——写了直接
   判 sandbox_escape_attempt。
