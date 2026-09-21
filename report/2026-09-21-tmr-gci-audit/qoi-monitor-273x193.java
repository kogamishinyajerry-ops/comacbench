// qoi273: QoI 平稳性实验 —— 273x193 默认 IC，分块迭代，每 1000 步导出一次壁面 tau
// 目的：湍流残差量级不可靠（按 k 归一化），改用 QoI（壁面 Cf 曲线）判定收敛。
import star.common.*;
import star.base.neo.*;
import star.flow.*;

public class qoi273 extends StarMacro {
    Boundary bz0, binlet, boutlet, bz1, slip;
    Simulation sim;
    Region reg;

    void rep(String tag, String ff, Boundary part) {
        try {
            FieldFunction f = sim.getFieldFunctionManager().getFunction(ff);
            if (f == null) { sim.println("Q-" + tag + " FF-NULL " + ff); return; }
            star.base.report.AreaAverageReport r = sim.getReportManager()
                .createReport(star.base.report.AreaAverageReport.class);
            r.setFieldFunction(f);
            r.getParts().setObjects(part);
            sim.println("Q-" + tag + " = " + r.getReportMonitorValue());
        } catch (Throwable t) { sim.println("Q-" + tag + "-ERR " + t.getMessage()); }
    }

    void exportTau(int it) {
        try {
            FieldFunction tau = sim.getFieldFunctionManager().getFunction("WallShearStress");
            FieldFunction cx = sim.getFieldFunctionManager().getFunction("Centroid").getComponentFunction(0);
            String p = String.format("C:/Users/Kogami/cb_dl/tmr/run2/qoi273/q_%05d.vrt", it);
            sim.getExportManager().export(
                p, java.util.Arrays.asList(reg), java.util.Arrays.asList(bz0),
                java.util.Arrays.asList(), java.util.Arrays.asList(tau, cx), true, false);
            sim.println("Q-EXPORT-OK " + it);
        } catch (Throwable t) { sim.println("Q-EXPORT-ERR " + it + " " + t.getMessage()); }
    }

    public void execute() {
        sim = getActiveSimulation();
        sim.println("Q-START Q273");
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
        try {
            star.common.StepStoppingCriterion msc = (star.common.StepStoppingCriterion)
                sim.getSolverStoppingCriterionManager().getObject("Maximum Steps");
            sim.println("Q-BEFORE-MAXSTEPS " + msc.getMaximumNumberSteps());
            msc.setMaximumNumberSteps(24000);   // 上限留够，实际由分块循环控制
            sim.println("Q-AFTER-MAXSTEPS " + msc.getMaximumNumberSteps());
        } catch (Throwable t) { sim.println("Q-MAXSTEPS-ERR " + t.getMessage()); }
        sim.println("Q-SETUP-DONE");

        sim.initializeSolution();
        sim.println("Q-INIT-IT " + sim.getSimulationIterator().getCurrentIteration());

        for (int chunk = 1; chunk <= 12; chunk++) {
            try {
                sim.getSimulationIterator().step(1000);
                sim.println("Q-CHUNK-OK " + chunk + " it=" + sim.getSimulationIterator().getCurrentIteration());
            } catch (Throwable t) {
                sim.println("Q-CHUNK-ERR " + chunk + " " + t.getMessage());
                break;
            }
            int it = sim.getSimulationIterator().getCurrentIteration();
            rep("K-OUT-" + it, "TurbulentKineticEnergy", boutlet);
            rep("K-PLATE-" + it, "TurbulentKineticEnergy", bz0);
            rep("TVR-OUT-" + it, "TurbulentViscosityRatio", boutlet);
            exportTau(it);
        }
        sim.println("Q-FINAL-IT " + sim.getSimulationIterator().getCurrentIteration());
        rep("K-IN", "TurbulentKineticEnergy", binlet);
        rep("K-SLIP", "TurbulentKineticEnergy", slip);
        rep("YPLUS-PLATE", "WallYplus", bz0);
        sim.saveState("C:/Users/Kogami/cb_dl/tmr/run2/fp3d_Q273.sim");
        sim.println("Q-DONE Q273");
    }
}
