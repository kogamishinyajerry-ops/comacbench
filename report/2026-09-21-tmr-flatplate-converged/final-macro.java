// v3: physics FIRST, then identify boundaries, then split+types+run (matches solve3d proven order)
import star.common.*;
import star.base.neo.*;
import star.flow.*;

public class allin3 extends StarMacro {
    Boundary bz0, binlet, boutlet, bz1, slip;

    public void execute() {
        Simulation sim = getActiveSimulation();
        sim.println("A3-START");
        // 1. mesh
        sim.getImportManager().importMeshFiles(
            new String[]{"C:/Users/Kogami/cb_dl/tmr/grid_struct_137x97_vol.cgns"});
        Region r0 = sim.getRegionManager().getObjects().iterator().next();
        sim.getMeshManager().splitBoundariesByAngle(45.0, new java.util.ArrayList<Boundary>(
            r0.getBoundaryManager().getObjects()));
        Region r = sim.getRegionManager().getObjects().iterator().next();
        sim.println("A3-1-MESH n=" + r.getBoundaryManager().getObjects().size());
        // 2. physics FIRST (so Centroid components resolve)
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
        sim.println("A3-2-PHYSICS");
        // 3. identify by centroid
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
                sim.println("A3-BND " + b.getPresentationName() + " cx=" + String.format("%.3f", cx) + " cz=" + String.format("%.4f", cz));
                if (Math.abs(cz) < 0.01) bz0 = b;
                else if (Math.abs(cz - 1.0) < 0.01) bz1 = b;
                if (Math.abs(cx + 0.3333) < 0.01) binlet = b;
                if (Math.abs(cx - 2.0) < 0.01) boutlet = b;
            } catch (Throwable t) { sim.println("A3-BND-ERR " + t.getMessage()); }
        }
        sim.println("A3-ID: wall=" + (bz0==null?"?":bz0.getPresentationName())
            + " top=" + (bz1==null?"?":bz1.getPresentationName())
            + " in=" + (binlet==null?"?":binlet.getPresentationName())
            + " out=" + (boutlet==null?"?":boutlet.getPresentationName()));
        // 4. split wall at x=0
        UserFieldFunction splitx = sim.getFieldFunctionManager().createFieldFunction();
        splitx.setPresentationName("splitx");
        splitx.setFunctionName("splitx");
        splitx.setDefinition("$$Centroid[0] > 0.0");
        sim.getMeshManager().splitBoundariesByFunction(splitx, java.util.Arrays.asList(bz0));
        sim.println("A3-3-SPLITX");
        // find slip (x<0 segment, new boundary)
        for (Boundary b : r.getBoundaryManager().getObjects()) {
            if (b == bz0) continue;
            try {
                star.base.report.AreaAverageReport rex = sim.getReportManager().createReport(star.base.report.AreaAverageReport.class);
                rex.setFieldFunction(sim.getFieldFunctionManager().getFunction("Centroid").getComponentFunction(0));
                rex.getParts().setObjects(b);
                if (rex.getReportMonitorValue() < 0.0) slip = b;
            } catch (Throwable t) {}
        }
        sim.println("A3-4-SLIP: " + (slip==null?"?":slip.getPresentationName()));
        // 5. types
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
        sim.println("A3-5-TYPES");
        // 6. inlet: 50 m/s +X via COMPONENTS
        star.flow.FlowDirectionOption fdo = (star.flow.FlowDirectionOption) binlet.getConditions().getObject("流向规范");
        fdo.setSelected(star.flow.FlowDirectionOption.Type.COMPONENTS);
        Object mag = binlet.getValues().getObject("速度幅值");
        Object mm = ((ScalarProfile) mag).getMethod();
        ((star.common.ConstantScalarProfileMethod) mm).getQuantity().set("Value", 50.0);
        try {
            Object dir = binlet.getValues().getObject("流向");
            ((ClientServerObject) dir).set("Value", new DoubleVector(new double[]{1.0, 0.0, 0.0}));
        } catch (Throwable t) { sim.println("A3-DIR-ERR: " + t.getMessage()); }
        Object magv = ((ScalarProfile) binlet.getValues().getObject("速度幅值")).getMethod();
        sim.println("A3-6-VEL: " + ((star.common.ConstantScalarProfileMethod) magv).getQuantity());
        // 7. conservative CFL
        try {
            ClientServerObject ss = (ClientServerObject) sim.getSolverManager().getObject("定常");
            ss.set("CourantNumber", 5.0);
        } catch (Throwable t) { sim.println("A3-CFL-ERR: " + t.getMessage()); }
        // 8. max steps 1500
        try {
            Object msc = sim.getSolverStoppingCriterionManager().getObject("Maximum Steps");
            ((ClientServerObject) msc).set("MaximumSteps", 1500);
        } catch (Throwable t) { sim.println("A3-MAXSTEPS-ERR: " + t.getMessage()); }
        sim.println("A3-7-SETUP");
        // 9. init + run
        sim.initializeSolution();
        try { sim.getSimulationIterator().run(); sim.println("A3-8-RUN-OK"); }
        catch (Throwable t) { sim.println("A3-8-RUN-ERR: " + t.getMessage()); }
        // 10. verify inlet
        try {
            star.base.report.AreaAverageReport rep = sim.getReportManager().createReport(star.base.report.AreaAverageReport.class);
            rep.setFieldFunction(sim.getFieldFunctionManager().getFunction("Velocity").getComponentFunction(0));
            rep.getParts().setObjects(binlet);
            sim.println("A3-9-UINLET: " + rep.getReportMonitorValue());
        } catch (Throwable t) {}
        // 11. export wall tau + x
        try {
            FieldFunction tau = sim.getFieldFunctionManager().getFunction("WallShearStress");
            FieldFunction cx = sim.getFieldFunctionManager().getFunction("Centroid").getComponentFunction(0);
            sim.getExportManager().export(
                "C:/Users/Kogami/cb_dl/tmr/run2/tau_a3.vrt",
                java.util.Arrays.asList(r), java.util.Arrays.asList(bz0),
                java.util.Arrays.asList(), java.util.Arrays.asList(tau, cx), true, false);
            sim.println("A3-10-EXPORT-OK");
        } catch (Throwable t) { sim.println("A3-10-EXPORT-ERR: " + t.getMessage()); }
        sim.saveState("C:/Users/Kogami/cb_dl/tmr/run2/fp3d_A3.sim");
        sim.println("A3-DONE");
    }
}
