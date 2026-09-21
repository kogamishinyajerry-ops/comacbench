// topvar: 单变量对照 —— 只把顶面 BC 从「对称平面」改成「压力出口」(TMR 官方为 farfield Riemann BC)
//   其余与 tmrbc273 完全一致（273x193 / U=50 / TMR 入口湍流 / 3000 步）
// 用法：starccm+.bat -new -batch topvar.java
import star.common.*;
import star.base.neo.*;
import star.flow.*;

public class topvar extends StarMacro {
    Boundary binlet, boutlet, bz0, btop, bside1, bside2, bstrip;
    Region reg;
    Simulation sim;

    static final double TI  = 3.8730e-4;
    static final double TVR = 0.009;
    static final double IC_TI = 0.0193649;
    static final boolean TOP_IS_OUTLET = true;
    static final String SIMTAG = "topvar";

    void rep(String tag, String ff, Boundary b) {
        try {
            FieldFunction f = sim.getFieldFunctionManager().getFunction(ff);
            star.base.report.AreaAverageReport r = sim.getReportManager()
                .createReport(star.base.report.AreaAverageReport.class);
            r.setFieldFunction(f);
            r.getParts().setObjects(b);
            sim.println("V-" + tag + " = " + r.getReportMonitorValue());
        } catch (Throwable t) { sim.println("V-" + tag + "-ERR " + t.getMessage()); }
    }

    double avg(Boundary b, int comp) {
        try {
            star.base.report.AreaAverageReport r = sim.getReportManager()
                .createReport(star.base.report.AreaAverageReport.class);
            r.setFieldFunction(sim.getFieldFunctionManager().getFunction("Centroid").getComponentFunction(comp));
            r.getParts().setObjects(b);
            return r.getReportMonitorValue();
        } catch (Throwable t) { return Double.NaN; }
    }

    void setScalar(ConditionManager cm, String key, double v, String tag) {
        try {
            Object o = cm.getObject(key);
            ((star.common.ConstantScalarProfileMethod) ((ScalarProfile) o).getMethod())
                .getQuantity().set("Value", v);
            sim.println("V-SET " + tag + " " + key + " = " + v);
        } catch (Throwable t) { sim.println("V-SET-ERR " + tag + " " + key + " " + t.getMessage()); }
    }

    void dumpKeys(Boundary b, String tag) {
        try {
            for (Object o : b.getValues().getObjects()) {
                String nm = o.getClass().getName();
                try { nm = (String) o.getClass().getMethod("getPresentationName").invoke(o); } catch (Throwable ig) {}
                sim.println("V-KEY " + tag + " " + nm);
            }
        } catch (Throwable t) { sim.println("V-KEY-ERR " + tag); }
    }

    void repFF(String tag, FieldFunction f, Boundary b) {
        if (f == null) { sim.println("V-" + tag + "-NULL"); return; }
        try {
            star.base.report.AreaAverageReport r = sim.getReportManager()
                .createReport(star.base.report.AreaAverageReport.class);
            r.setFieldFunction(f);
            r.getParts().setObjects(b);
            sim.println("V-" + tag + " = " + r.getReportMonitorValue());
        } catch (Throwable t) { sim.println("V-" + tag + "-ERR " + t.getMessage()); }
    }

    FieldFunction comp(String n, int i) {
        try { return sim.getFieldFunctionManager().getFunction(n).getComponentFunction(i); }
        catch (Throwable t) { sim.println("V-FF-COMP-ERR " + n + "[" + i + "]"); return null; }
    }

    void exportSlice() {
        try {
            java.util.ArrayList<FieldFunction> f = new java.util.ArrayList<>();
            for (FieldFunction x : new FieldFunction[]{
                    comp("Velocity", 0), comp("Velocity", 2),
                    sim.getFieldFunctionManager().getFunction("TurbulentKineticEnergy"),
                    sim.getFieldFunctionManager().getFunction("TurbulentViscosityRatio"),
                    sim.getFieldFunctionManager().getFunction("SpecificDissipationRate"),
                    comp("Centroid", 0), comp("Centroid", 2)}) {
                if (x != null) f.add(x);
            }
            String out = "C:/Users/Kogami/cb_dl/tmr/run2/slice_" + SIMTAG + ".vrt";
            sim.getExportManager().export(out, java.util.Arrays.asList(reg),
                java.util.Arrays.asList(bside1), java.util.Arrays.asList(), f, true, false);
            sim.println("V-EXPORT-OK " + out + " nfields=" + f.size());
        } catch (Throwable t) { sim.println("V-EXPORT-ERR " + t.getMessage()); }
    }

    void diag(int it) {
        repFF("STRIP-U-" + it, comp("Velocity", 0), bstrip);
        repFF("STRIP-W-" + it, comp("Velocity", 2), bstrip);
        repFF("STRIP-K-" + it,
              sim.getFieldFunctionManager().getFunction("TurbulentKineticEnergy"), bstrip);
        repFF("TOP-K-" + it,
              sim.getFieldFunctionManager().getFunction("TurbulentKineticEnergy"), btop);
        repFF("OUT-K-" + it,
              sim.getFieldFunctionManager().getFunction("TurbulentKineticEnergy"), boutlet);
        repFF("PLATE-YPLUS-" + it,
              sim.getFieldFunctionManager().getFunction("WallYplus"), bz0);
        repFF("PLATE-U-" + it, comp("Velocity", 0), bz0);
    }

    public void execute() {
        sim = getActiveSimulation();
        sim.println("V-START TOP_IS_OUTLET=" + TOP_IS_OUTLET);
        sim.getImportManager().importMeshFiles(new String[]{"C:/Users/Kogami/cb_dl/tmr/grid_struct_273x193_vol.cgns"});
        Region r0 = sim.getRegionManager().getObjects().iterator().next();
        sim.getMeshManager().splitBoundariesByAngle(45.0,
            new java.util.ArrayList<Boundary>(r0.getBoundaryManager().getObjects()));
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
            double cx = avg(b, 0), cy = avg(b, 1), cz = avg(b, 2);
            sim.println("V-BND " + b.getPresentationName() + " cx=" + String.format("%.5f", cx)
                + " cy=" + String.format("%.5f", cy) + " cz=" + String.format("%.5f", cz));
            if (Math.abs(cz) < 0.01) bz0 = b;          // 分割前底面是整块，质心 cx=0.8333
            else if (Math.abs(cz - 1.0) < 0.01) btop = b;
            if (Math.abs(cx + 0.3333) < 0.01) binlet = b;
            if (Math.abs(cx - 2.0) < 0.01) boutlet = b;
            if (Math.abs(cy) < 0.01 && Math.abs(cz - 0.5) < 0.05) bside1 = b;
            if (Math.abs(cy + 1.0) < 0.01 && Math.abs(cz - 0.5) < 0.05) bside2 = b;
        }
        UserFieldFunction splitx = sim.getFieldFunctionManager().createFieldFunction();
        splitx.setPresentationName("splitx");
        splitx.setFunctionName("splitx");
        splitx.setDefinition("$$Centroid[0] > 0.0");
        sim.getMeshManager().splitBoundariesByFunction(splitx, java.util.Arrays.asList(bz0));
        for (Boundary b : r.getBoundaryManager().getObjects()) {
            double cx = avg(b, 0), cz = avg(b, 2);
            if (Math.abs(cz) < 0.01 && cx < -0.05) bstrip = b;
        }
        sim.println("V-PICK inlet=" + (binlet == null ? "NULL" : binlet.getPresentationName())
            + " outlet=" + (boutlet == null ? "NULL" : boutlet.getPresentationName())
            + " plate=" + (bz0 == null ? "NULL" : bz0.getPresentationName())
            + " strip=" + (bstrip == null ? "NULL" : bstrip.getPresentationName())
            + " top=" + (btop == null ? "NULL" : btop.getPresentationName()));

        binlet.setBoundaryType(InletBoundary.class);
        boutlet.setBoundaryType(OutletBoundary.class);
        bz0.setBoundaryType(WallBoundary.class);
        bstrip.setBoundaryType(SymmetryBoundary.class);
        bside1.setBoundaryType(SymmetryBoundary.class);
        bside2.setBoundaryType(SymmetryBoundary.class);
        if (TOP_IS_OUTLET) {
            btop.setBoundaryType(OutletBoundary.class);
            sim.println("V-TOP set to OutletBoundary");
        } else {
            btop.setBoundaryType(SymmetryBoundary.class);
            sim.println("V-TOP set to SymmetryBoundary");
        }
        sim.println("V-TYPES");
        for (Boundary b : r.getBoundaryManager().getObjects()) {
            String ty = "?";
            try { ty = b.getBoundaryType().getPresentationName(); } catch (Throwable t) {}
            sim.println("V-TYPE " + b.getPresentationName() + " | " + ty);
        }
        dumpKeys(btop, "TOP");
        dumpKeys(boutlet, "OUT");

        FlowDirectionOption fdo = (FlowDirectionOption) binlet.getConditions().getObject("流向规范");
        fdo.setSelected(FlowDirectionOption.Type.COMPONENTS);
        setScalar(binlet.getValues(), "速度幅值", 50.0, "INLET");
        try {
            Object dir = binlet.getValues().getObject("流向");
            ((ClientServerObject) dir).set("Value", new DoubleVector(new double[]{1.0, 0.0, 0.0}));
        } catch (Throwable t) {}

        setScalar(binlet.getValues(), "湍流强度", TI, "INLET");
        setScalar(binlet.getValues(), "湍流粘度比", TVR, "INLET");
        ConditionManager ic = pc.getInitialConditions();
        setScalar(ic, "湍流强度", IC_TI, "IC");
        setScalar(ic, "湍流粘度比", TVR, "IC");
        setScalar(ic, "湍流速度比例", 1.0, "IC");
        try {
            Object iv = ic.getObject("速度");
            ((ClientServerObject) iv).set("Value", new DoubleVector(new double[]{50.0, 0.0, 0.0}));
        } catch (Throwable t) {}

        for (String k : new String[]{"压力", "静态压力", "Pressure"}) {
            try {
                Object o = btop.getValues().getObject(k);
                ((star.common.ConstantScalarProfileMethod) ((ScalarProfile) o).getMethod())
                    .getQuantity().set("Value", 0.0);
                sim.println("V-TOP-PRESS-SET " + k + " = 0");
                break;
            } catch (Throwable t) {}
        }

        SimulationIterator it = sim.getSimulationIterator();
        diag(0);
        for (int c = 1; c <= 3; c++) {
            it.step(1000);
            sim.println("V-CHUNK-OK " + c);
            diag(c * 1000);
        }
        exportSlice();
        sim.println("V-DONE");
    }
}
