// qoi78: Re 修正版 QoI 平稳性实验 —— 273x193, U=78.33, 12 x 1000 步分块导出壁面 tau
//
// 依据（见 report/2026-09-21-tmr-gci-audit §11）：从 field_side273.daten 反推
//   nu = k/(omega*TVR) = 1.56659e-5  （52224 样本, 离散度 0.01%）
//   = STAR-CCM+ 默认空气 mu/rho = 1.85508e-5/1.18415
// 因此 U=50 时 Re_unit = 50/1.56659e-5 = 3.1917e6，而 TMR 参考要求 5e6。
//   => U = 5e6 * 1.56659e-5 = 78.33
//
// 湍流口径取 TMR：
//   k_inf = 1.125 U^2 / Re_L = 1.3806e-3   <=> Ti = sqrt(2k/3)/U = 3.873e-4
//   omega = 125 U / L        = 9791.83     <=> mu_t/mu = 0.009   (自洽校验)
import star.common.*;
import star.base.neo.*;
import star.flow.*;

public class qoi78 extends StarMacro {
    Boundary bz0, binlet, boutlet, bz1, slip;
    Simulation sim;
    Region reg;

    static final double U     = 78.33;      // 5e6 * nu
    static final double TI    = 3.8730e-4;  // = sqrt(2k/3)/U, k=1.3806e-3
    static final double TVR   = 0.009;
    static final double IC_TI = 0.0303379;  // = sqrt(k/1.5), k=1.3806e-3

    void rep(String tag, String ff, Boundary part) {
        try {
            FieldFunction f = sim.getFieldFunctionManager().getFunction(ff);
            if (f == null) { sim.println("Q78-" + tag + " FF-NULL " + ff); return; }
            star.base.report.AreaAverageReport r = sim.getReportManager()
                .createReport(star.base.report.AreaAverageReport.class);
            r.setFieldFunction(f);
            r.getParts().setObjects(part);
            sim.println("Q78-" + tag + " = " + r.getReportMonitorValue());
        } catch (Throwable t) { sim.println("Q78-" + tag + "-ERR " + t.getMessage()); }
    }

    void setScalar(star.common.ConditionManager cm, String key, double v, String tag) {
        try {
            Object o = cm.getObject(key);
            ((star.common.ConstantScalarProfileMethod) ((ScalarProfile) o).getMethod())
                .getQuantity().set("Value", v);
            sim.println("Q78-SET " + tag + " " + key + " = " + v);
        } catch (Throwable t) { sim.println("Q78-SET-ERR " + tag + " " + key + " " + t.getMessage()); }
    }

    void exportTau(int it) {
        try {
            FieldFunction tau = sim.getFieldFunctionManager().getFunction("WallShearStress");
            FieldFunction cx = sim.getFieldFunctionManager().getFunction("Centroid").getComponentFunction(0);
            String p = String.format("C:/Users/Kogami/cb_dl/tmr/run2/qoi78/q_%05d.vrt", it);
            sim.getExportManager().export(
                p, java.util.Arrays.asList(reg), java.util.Arrays.asList(bz0),
                java.util.Arrays.asList(), java.util.Arrays.asList(tau, cx), true, false);
            sim.println("Q78-EXPORT-OK " + it);
        } catch (Throwable t) { sim.println("Q78-EXPORT-ERR " + it + " " + t.getMessage()); }
    }

    public void execute() {
        sim = getActiveSimulation();
        sim.println("Q78-START U=" + U);
        sim.getImportManager().importMeshFiles(new String[]{"C:/Users/Kogami/cb_dl/tmr/grid_struct_273x193_vol.cgns"});
        Region r0 = sim.getRegionManager().getObjects().iterator().next();
        sim.getMeshManager().splitBoundariesByAngle(45.0, new java.util.ArrayList<Boundary>(
            r0.getBoundaryManager().getObjects()));
        Region r = sim.getRegionManager().getObjects().iterator().next();
        reg = r;
        PhysicsContinuum pc = sim.getContinuumManager().createContinuum(PhysicsContinuum.class);
        pc.enable(star.metrics.ThreeDimensionalModel.class);
        pc.enable(star.material.SingleComponentGasModel.class);
        pc.enable(star.segregatedflow.SegregatedFlowModel.class);
        pc.enable(star.common.SteadyModel.class);
        pc.enable(star.flow.ConstantDensityModel.class);
        pc.enable(star.segregatedenergy.SegregatedFluidIsothermalModel.class);
        pc.enable(star.turbulence.TurbulentModel.class);
        pc.enable(star.turbulence.RansTurbulenceModel.class);
        pc.enable(star.kwturb.KOmegaTurbulence.class);
        pc.enable(star.kwturb.SstKwTurbModel.class);
        pc.enable(star.kwturb.KwAllYplusWallTreatment.class);
        java.util.List<Region> rl = new java.util.ArrayList<>();
        rl.add(r);
        sim.getContinuumManager().setContinuum(rl, pc);

        for (Boundary b : r.getBoundaryManager().getObjects()) {
            try {
                star.base.report.AreaAverageReport rep = sim.getReportManager().createReport(star.base.report.AreaAverageReport.class);
                rep.setFieldFunction(sim.getFieldFunctionManager().getFunction("Centroid").getComponentFunction(2));
                rep.getParts().setObjects(b);
                double cz = rep.getReportMonitorValue();
                star.base.report.AreaAverageReport rex = sim.getReportManager().createReport(star.base.report.AreaAverageReport.class);
                rex.setFieldFunction(sim.getFieldFunctionManager().getFunction("Centroid").getComponentFunction(0));
                rex.getParts().setObjects(b);
                double cx = rex.getReportMonitorValue();
                if (Math.abs(cz) < 0.01) bz0 = b;
                else if (Math.abs(cz - 1.0) < 0.01) bz1 = b;
                if (Math.abs(cx + 0.3333) < 0.01) binlet = b;
                if (Math.abs(cx - 2.0) < 0.01) boutlet = b;
            } catch (Throwable t) {}
        }
        UserFieldFunction splitx = sim.getFieldFunctionManager().createFieldFunction();
        splitx.setPresentationName("splitx");
        splitx.setFunctionName("splitx");
        splitx.setDefinition("$$Centroid[0] > 0.0");
        sim.getMeshManager().splitBoundariesByFunction(splitx, java.util.Arrays.asList(bz0));
        for (Boundary b : r.getBoundaryManager().getObjects()) {
            if (b == bz0) continue;
            try {
                star.base.report.AreaAverageReport rex = sim.getReportManager().createReport(star.base.report.AreaAverageReport.class);
                rex.setFieldFunction(sim.getFieldFunctionManager().getFunction("Centroid").getComponentFunction(0));
                rex.getParts().setObjects(b);
                if (rex.getReportMonitorValue() < 0.0) slip = b;
            } catch (Throwable t) {}
        }
        binlet.setBoundaryType(InletBoundary.class);
        boutlet.setBoundaryType(OutletBoundary.class);
        bz1.setBoundaryType(SymmetryBoundary.class);
        bz0.setBoundaryType(WallBoundary.class);
        if (slip != null) slip.setBoundaryType(SymmetryBoundary.class);
        for (Boundary b : r.getBoundaryManager().getObjects()) {
            if (b != binlet && b != boutlet && b != bz1 && b != bz0 && b != slip) {
                b.setBoundaryType(SymmetryBoundary.class);
            }
        }
        star.flow.FlowDirectionOption fdo = (star.flow.FlowDirectionOption) binlet.getConditions().getObject("流向规范");
        fdo.setSelected(star.flow.FlowDirectionOption.Type.COMPONENTS);
        setScalar(binlet.getValues(), "速度幅值", U, "INLET");
        try {
            Object dir = binlet.getValues().getObject("流向");
            ((ClientServerObject) dir).set("Value", new DoubleVector(new double[]{1.0, 0.0, 0.0}));
        } catch (Throwable t) {}
        try {
            ClientServerObject ss = (ClientServerObject) sim.getSolverManager().getObject("定常");
            ss.set("CourantNumber", 5.0);
        } catch (Throwable t) {}

        setScalar(binlet.getValues(), "湍流强度", TI, "INLET");
        setScalar(binlet.getValues(), "湍流粘度比", TVR, "INLET");
        star.common.ConditionManager ic = pc.getInitialConditions();
        setScalar(ic, "湍流强度", IC_TI, "IC");
        setScalar(ic, "湍流粘度比", TVR, "IC");
        setScalar(ic, "湍流速度比例", 1.0, "IC");
        try {
            Object iv = ic.getObject("速度");
            ((ClientServerObject) iv).set("Value", new DoubleVector(new double[]{U, 0.0, 0.0}));
            sim.println("Q78-SET IC 速度 = (" + U + ",0,0)");
        } catch (Throwable t) { sim.println("Q78-SET-ERR IC 速度 " + t.getMessage()); }

        try {
            star.common.StepStoppingCriterion msc = (star.common.StepStoppingCriterion)
                sim.getSolverStoppingCriterionManager().getObject("Maximum Steps");
            msc.setMaximumNumberSteps(24000);
        } catch (Throwable t) { sim.println("Q78-MAXSTEPS-ERR " + t.getMessage()); }
        sim.println("Q78-SETUP-DONE");

        sim.initializeSolution();
        sim.println("Q78-INIT-IT " + sim.getSimulationIterator().getCurrentIteration());
        rep("K-IN", "TurbulentKineticEnergy", binlet);
        rep("OMEGA-IN", "SpecificDissipationRate", binlet);
        rep("TVR-IN", "TurbulentViscosityRatio", binlet);

        for (int chunk = 1; chunk <= 12; chunk++) {
            try {
                sim.getSimulationIterator().step(1000);
                sim.println("Q78-CHUNK-OK " + chunk + " it=" + sim.getSimulationIterator().getCurrentIteration());
            } catch (Throwable t) {
                sim.println("Q78-CHUNK-ERR " + chunk + " " + t.getMessage());
                break;
            }
            int it = sim.getSimulationIterator().getCurrentIteration();
            rep("K-OUT-" + it, "TurbulentKineticEnergy", boutlet);
            rep("TVR-OUT-" + it, "TurbulentViscosityRatio", boutlet);
            exportTau(it);
        }
        sim.println("Q78-FINAL-IT " + sim.getSimulationIterator().getCurrentIteration());
        rep("K-PLATE", "TurbulentKineticEnergy", bz0);
        rep("YPLUS-PLATE", "WallYplus", bz0);
        if (slip != null) rep("K-SLIP", "TurbulentKineticEnergy", slip);
        sim.saveState("C:/Users/Kogami/cb_dl/tmr/run2/fp3d_Q78.sim");
        sim.println("Q78-DONE");
    }
}
