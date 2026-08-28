# cfdb validation — Dam Break (Martin & Moyce 1952, interFoam VOF)

Classic 2D dam-break multiphase benchmark, OpenFOAM interFoam (VOF). A water column of base width a = 0.146 m and height 2a = 0.292 m (the Martin & Moyce n^2 = 2 configuration) collapses under gravity in a plain 4a x 4a tank with a dry bed. Reference: Martin & Moyce (1952), Phil. Trans. R. Soc. Lond. A 244(882), 312-324, digitized surge-front curve (a = 2.25 in series) cross-checked point-by-point between two independent digitizations (OpenMPS benchmark CSV and the Lethe dam-break example; max deviation 0.013 in Z/a). Dimensionless convention used here (stated explicitly because both appear in the literature): tau = t*sqrt(2*g/a) and Z/a, where Z is the surge-front position along the floor measured from the column back wall — i.e. Z/a = 1 at tau = 0. QoIs are Z/a at tau = 1.0, 1.5, 2.0, 2.5, 2.8, obtained by linear interpolation of the frozen CSV (see reference/interpolate_qoi.py). Simulation-side extraction: at the write time nearest to t = tau/sqrt(2*g/a), Z = max{x : alpha.water >= 0.5}. NO gate-release time shift is applied to the simulation (Martin & Moyce could not record the exact onset of motion; some studies shift simulation time by +0.175 in tau — we deliberately do not, and the tolerance absorbs it). Uniform 15% relative tolerance is a documented domain decision: it covers the moderate 96x96 demo mesh (cell size a/24; published VOF studies use a/32..a/128), the un-shifted early-time gate-release effect, and digitization scatter. Mesh, interface compression (vanLeer + interfaceCompression, cAlpha = 1, MULES) and BCs follow the ESI v2312 interFoam/laminar/damBreak tutorial, with the tutorial's downstream obstacle removed to match the plain Martin & Moyce tank.

## 要求
- 求解器族: OpenFOAM（上游基准使用 ESI v2312 语义）；从零搭建完整可运行案例（0/ constant/ system/ + Allrun），真实求解到 case 指定的终止时刻。
- 物理设定: flow=incompressible, turbulence=none, dim=2d, steady=False
- 工况: 
- 输出 QoI: front_z_tau_1_0, front_z_tau_1_5, front_z_tau_2_0, front_z_tau_2_5, front_z_tau_2_8
- 参考类型: experimental（容差见任务 YAML reference.tolerances；判分用冻结 QoI 脚本）

## 交付
写 result.json，字段为上述 QoI 名（数值，与 QoI 定义单位一致）。
