// tmrbc137: 单变量对照 —— 只把 入口/初始 湍流改成 TMR 文档口径，其余与 qoi273 完全一致
//   TMR: k_farfield = 1.125 U^2/ReL = 5.625e-4 ; omega = 125 U/L = 6250 ; mu_t/mu = 0.009
//   等价 INTENSITY_VISCOSITY_RATIO: Ti = sqrt(2k/3)/U = 3.873e-4 ; TVR = 0.009
import star.common.*;
import star.base.neo.*;
import star.flow.*;

public class tmrbc137 extends StarMacro {
    Boundary bz0, binlet, boutlet, bz1, slip;
    Simulation sim;
    Region reg;

    static final double TI   = 3.8730e-4;   // 入口湍流强度 (=TMR k=5.625e-4, U=50)
    static final double TVR  = 0.009;       // 入口 mu_t/mu (=TMR)
    static final double IC_TI = 0.0193649;  // IC: Ti*vscale = 0.0193649 -> k=1.5*(.)^2=5.625e-4

    void rep(String tag, String ff, Boundary part) {
        try {
            FieldFunction f = sim.getFieldFunctionManager().getFunction(ff);
            if (f == null) { sim.println("T-" + tag + " FF-NULL " + ff); return; }
            star.base.report.AreaAverageReport r = sim.getReportManager()
                .createReport(star.base.report.AreaAverageReport.class);
            r.setFieldFunction(f);
            r.getParts().setObjects(part);
            sim.println("T-" + tag + " = " + r.getReportMonitorValue());
        } catch (Throwable t) { sim.println("T-" + tag + "-ERR " + t.getMessage()); }
    }

    void setScalar(star.common.ConditionManager cm, String key, double v, String tag) {
        try {
            Object o = cm.getObject(key);
            ((star.common.ConstantScalarProfileMethod) ((ScalarProfile) o).getMethod())
                .getQuantity().set("Value", v);
            sim.println("T-SET " + tag + " " + key + " = " + v);
        } catch (Throwable t) { sim.println("T-SET-ERR " + tag + " " + key + " " + t.getMessage()); }
    }

    void exportTau(int it) {
        try {
            FieldFunction tau = sim.getFieldFunctionManager().getFunction("WallShearStress");
            FieldFunction cx = sim.getFieldFunctionManager().getFunction("Centroid").getComponentFunction(0);
            String p = String.format("C:/Users/Kogami/cb_dl/tmr/run2/tmrbc137/q_%05d.vrt", it);
            sim.getExportManager().export(
                p, java.util.Arrays.asList(reg), java.util.Arrays.asList(bz0),
                java.util.Arrays.asList(), java.util.Arrays.asList(tau, cx), true, false);
            sim.println("T-EXPORT-OK " + it);
        } catch (Throwable t) { sim.println("T-EXPORT-ERR " + it + " " + t.getMessage()); }
    }

    public void execute() {
        sim = getActiveSimulation();
        sim.println("T-START TMRBC137");
        sim.getImportManager().importMeshFiles(new String[]{"C:/Users/Kogami/cb_dl/tmr/grid_struct_137x97_vol.cgns"});
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
        setScalar(binlet.getValues(), "速度幅值", 50.0, "INLET");
        try {
            Object dir = binlet.getValues().getObject("流向");
            ((ClientServerObject) dir).set("Value", new DoubleVector(new double[]{1.0, 0.0, 0.0}));
        } catch (Throwable t) {}
        try {
            ClientServerObject ss = (ClientServerObject) sim.getSolverManager().getObject("定常");
            ss.set("CourantNumber", 5.0);
        } catch (Throwable t) {}

        // ================= 唯一的改动：TMR 文档入口/初始湍流 =================
        setScalar(binlet.getValues(), "湍流强度", TI, "INLET");
        setScalar(binlet.getValues(), "湍流粘度比", TVR, "INLET");
        star.common.ConditionManager ic = pc.getInitialConditions();
        setScalar(ic, "湍流强度", IC_TI, "IC");
        setScalar(ic, "湍流粘度比", TVR, "IC");
        setScalar(ic, "湍流速度比例", 1.0, "IC");
        try {
            Object iv = ic.getObject("速度");
            ((ClientServerObject) iv).set("Value", new DoubleVector(new double[]{50.0, 0.0, 0.0}));
            sim.println("T-SET IC 速度 = (50,0,0)");
        } catch (Throwable t) { sim.println("T-SET-ERR IC 速度 " + t.getMessage()); }
        // ===================================================================

        try {
            star.common.StepStoppingCriterion msc = (star.common.StepStoppingCriterion)
                sim.getSolverStoppingCriterionManager().getObject("Maximum Steps");
            msc.setMaximumNumberSteps(24000);
        } catch (Throwable t) { sim.println("T-MAXSTEPS-ERR " + t.getMessage()); }
        sim.println("T-SETUP-DONE");

        sim.initializeSolution();
        sim.println("T-INIT-IT " + sim.getSimulationIterator().getCurrentIteration());
        rep("K-IN", "TurbulentKineticEnergy", binlet);
        rep("OMEGA-IN", "SpecificDissipationRate", binlet);
        rep("TVR-IN", "TurbulentViscosityRatio", binlet);

        for (int chunk = 1; chunk <= 12; chunk++) {
            try {
                sim.getSimulationIterator().step(1000);
                sim.println("T-CHUNK-OK " + chunk + " it=" + sim.getSimulationIterator().getCurrentIteration());
            } catch (Throwable t) {
                sim.println("T-CHUNK-ERR " + chunk + " " + t.getMessage());
                break;
            }
            int it = sim.getSimulationIterator().getCurrentIteration();
            rep("K-OUT-" + it, "TurbulentKineticEnergy", boutlet);
            rep("TVR-OUT-" + it, "TurbulentViscosityRatio", boutlet);
            exportTau(it);
        }
        sim.println("T-FINAL-IT " + sim.getSimulationIterator().getCurrentIteration());
        rep("K-PLATE", "TurbulentKineticEnergy", bz0);
        rep("YPLUS-PLATE", "WallYplus", bz0);
        sim.saveState("C:/Users/Kogami/cb_dl/tmr/run2/fp3d_TMRBC137.sim");
        sim.println("T-DONE TMRBC137");
    }
}
