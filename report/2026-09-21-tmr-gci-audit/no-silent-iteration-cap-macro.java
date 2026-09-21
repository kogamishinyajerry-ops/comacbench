// long137: 长迭代（真的设上上限）对照 —— 求解 + 场诊断 + Cf 导出
import star.common.*;
import star.base.neo.*;
import star.flow.*;

public class long137 extends StarMacro {
    Boundary bz0, binlet, boutlet, bz1, slip;
    Simulation sim;

    void rep(String tag, String ff, Boundary part) {
        try {
            FieldFunction f = sim.getFieldFunctionManager().getFunction(ff);
            if (f == null) { sim.println("LR-" + tag + " FF-NULL " + ff); return; }
            star.base.report.AreaAverageReport r = sim.getReportManager()
                .createReport(star.base.report.AreaAverageReport.class);
            r.setFieldFunction(f);
            r.getParts().setObjects(part);
            sim.println("LR-" + tag + " = " + r.getReportMonitorValue());
        } catch (Throwable t) { sim.println("LR-" + tag + "-ERR " + t.getMessage()); }
    }

    public void execute() {
        sim = getActiveSimulation();
        sim.println("LR-START L137");
        sim.getImportManager().importMeshFiles(new String[]{"C:/Users/Kogami/cb_dl/tmr/grid_struct_137x97_vol.cgns"});
        Region r0 = sim.getRegionManager().getObjects().iterator().next();
        sim.getMeshManager().splitBoundariesByAngle(45.0, new java.util.ArrayList<Boundary>(
            r0.getBoundaryManager().getObjects()));
        Region r = sim.getRegionManager().getObjects().iterator().next();
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
        Object mag = binlet.getValues().getObject("速度幅值");
        ((star.common.ConstantScalarProfileMethod) ((ScalarProfile) mag).getMethod()).getQuantity().set("Value", 50.0);
        try {
            Object dir = binlet.getValues().getObject("流向");
            ((ClientServerObject) dir).set("Value", new DoubleVector(new double[]{1.0, 0.0, 0.0}));
        } catch (Throwable t) {}
        try {
            ClientServerObject ss = (ClientServerObject) sim.getSolverManager().getObject("定常");
            ss.set("CourantNumber", 5.0);
        } catch (Throwable t) {}

        // ---- 正确的迭代上限设置（typed setter）----
        try {
            star.common.StepStoppingCriterion msc = (star.common.StepStoppingCriterion)
                sim.getSolverStoppingCriterionManager().getObject("Maximum Steps");
            sim.println("LR-BEFORE-MAXSTEPS " + msc.getMaximumNumberSteps());
            msc.setMaximumNumberSteps(6000);
            sim.println("LR-AFTER-MAXSTEPS " + msc.getMaximumNumberSteps());
        } catch (Throwable t) { sim.println("LR-MAXSTEPS-ERR " + t.getMessage()); }
        sim.println("LR-SETUP-DONE");

        sim.initializeSolution();
        sim.println("LR-INIT-IT " + sim.getSimulationIterator().getCurrentIteration());
        try { sim.getSimulationIterator().run(); sim.println("LR-RUN-OK"); }
        catch (Throwable t) { sim.println("LR-RUN-ERR " + t.getMessage()); }
        sim.println("LR-FINAL-IT " + sim.getSimulationIterator().getCurrentIteration());

        rep("K-IN", "TurbulentKineticEnergy", binlet);
        rep("K-SLIP", "TurbulentKineticEnergy", slip);
        rep("K-PLATE", "TurbulentKineticEnergy", bz0);
        rep("K-OUT", "TurbulentKineticEnergy", boutlet);
        rep("TVR-PLATE", "TurbulentViscosityRatio", bz0);
        rep("TVR-OUT", "TurbulentViscosityRatio", boutlet);
        rep("YPLUS-PLATE", "WallYplus", bz0);
        try {
            FieldFunction tau = sim.getFieldFunctionManager().getFunction("WallShearStress");
            FieldFunction cx = sim.getFieldFunctionManager().getFunction("Centroid").getComponentFunction(0);
            sim.getExportManager().export(
                "C:/Users/Kogami/cb_dl/tmr/run2/tau_l137.vrt",
                java.util.Arrays.asList(r), java.util.Arrays.asList(bz0),
                java.util.Arrays.asList(), java.util.Arrays.asList(tau, cx), true, false);
            sim.println("LR-EXPORT-OK");
        } catch (Throwable t) { sim.println("LR-EXPORT-ERR " + t.getMessage()); }
        sim.saveState("C:/Users/Kogami/cb_dl/tmr/run2/fp3d_L137.sim");
        sim.println("LR-DONE L137");
    }
}
