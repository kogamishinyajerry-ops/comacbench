// diag273b: 读取 "湍流指定" 选择器实际取值 + 各 profile 数值 + 场函数真实名
import star.common.*;
import star.base.neo.*;
import star.flow.*;

public class diag273b extends StarMacro {
    Boundary bz0, binlet, boutlet, bz1, slip;
    Simulation sim;

    void dumpSelected(String tag, Object o) {
        if (o == null) { sim.println("DIAG-" + tag + " NULL"); return; }
        sim.println("DIAG-" + tag + "-CLASS " + o.getClass().getName());
        try {
            java.lang.reflect.Method m = o.getClass().getMethod("getSelected");
            sim.println("DIAG-" + tag + "-SEL " + m.invoke(o));
        } catch (Throwable t) { sim.println("DIAG-" + tag + "-SEL-ERR " + t); }
    }

    void dumpEnum(String tag, String cls) {
        try {
            Class<?> c = Class.forName(cls);
            Object[] ks = c.getEnumConstants();
            if (ks == null) { sim.println("DIAG-" + tag + " not-enum"); return; }
            for (Object k : ks) sim.println("DIAG-" + tag + "-OPT " + k);
        } catch (Throwable t) { sim.println("DIAG-" + tag + "-ERR " + t); }
    }

    void dumpVal(String tag, Object o) {
        if (o == null) { sim.println("DIAG-" + tag + " null-obj"); return; }
        try {
            Object meth = ((ScalarProfile) o).getMethod();
            sim.println("DIAG-" + tag + " = " + ((star.common.ConstantScalarProfileMethod) meth).getQuantity());
        } catch (Throwable t) { sim.println("DIAG-" + tag + "-ERR " + t); }
    }

    public void execute() {
        sim = getActiveSimulation();
        sim.println("DB-START");
        sim.getImportManager().importMeshFiles(
            new String[]{"C:/Users/Kogami/cb_dl/tmr/grid_struct_273x193_vol.cgns"});
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
        sim.println("DB-TYPES in=" + binlet.getPresentationName() + " out=" + boutlet.getPresentationName());

        try { dumpSelected("INLET-TSPEC", binlet.getConditions().getObject("湍流指定")); }
        catch (Throwable t) { sim.println("DIAG-INLET-TSPEC-LOOKUP-ERR " + t.getMessage()); }
        dumpEnum("KWSPEC-OPT", "star.kwturb.KwTurbSpecOption$Type");
        try { dumpSelected("IC-TSPEC", pc.getInitialConditions().getObject("湍流指定")); }
        catch (Throwable t) { sim.println("DIAG-IC-TSPEC-LOOKUP-ERR " + t.getMessage()); }
        try { dumpVal("INLET-TI", binlet.getValues().getObject("湍流强度")); }
        catch (Throwable t) { sim.println("DIAG-INLET-TI-ERR " + t.getMessage()); }
        try { dumpVal("INLET-TVR", binlet.getValues().getObject("湍流粘度比")); }
        catch (Throwable t) { sim.println("DIAG-INLET-TVR-ERR " + t.getMessage()); }
        try { dumpVal("IC-TI", pc.getInitialConditions().getObject("湍流强度")); }
        catch (Throwable t) { sim.println("DIAG-IC-TI-ERR " + t.getMessage()); }
        try { dumpVal("IC-TVR", pc.getInitialConditions().getObject("湍流粘度比")); }
        catch (Throwable t) { sim.println("DIAG-IC-TVR-ERR " + t.getMessage()); }
        try { dumpVal("IC-VSCALE", pc.getInitialConditions().getObject("湍流速度比例")); }
        catch (Throwable t) { sim.println("DIAG-IC-VSCALE-ERR " + t.getMessage()); }

        try {
            java.util.Collection<FieldFunction> ffs = sim.getFieldFunctionManager().getObjects();
            java.util.TreeSet<String> names = new java.util.TreeSet<>();
            for (FieldFunction f : ffs) {
                String n = f.getPresentationName();
                if (n.contains("Turbul") || n.contains("湍") || n.contains("Dissipation")
                        || n.contains("Kinetic") || n.contains("Omega") || n.contains("omega")
                        || n.contains("Viscosity")) {
                    names.add(n + " | " + f.getFunctionName());
                }
            }
            for (String s : names) sim.println("DIAG-FF " + s);
            sim.println("DIAG-FF-COUNT " + ffs.size());
        } catch (Throwable t) { sim.println("DIAG-FF-ERR " + t); }
        sim.println("DB-DONE");
    }
}
