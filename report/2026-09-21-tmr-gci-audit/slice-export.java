// slice_export: 通用 Y=0 侧平面（X×Z 切片）导出器 —— 按质心自动识别，输出名带 sim 名。
// 用法：starccm+.bat -batch slice_export.java <sim>
import star.common.*;
import star.base.neo.*;

public class slice_export extends StarMacro {
    Simulation sim;

    double avg(Boundary b, int comp) {
        try {
            star.base.report.AreaAverageReport r = sim.getReportManager()
                .createReport(star.base.report.AreaAverageReport.class);
            r.setFieldFunction(sim.getFieldFunctionManager().getFunction("Centroid").getComponentFunction(comp));
            r.getParts().setObjects(b);
            return r.getReportMonitorValue();
        } catch (Throwable t) { return Double.NaN; }
    }

    FieldFunction ff(String n) {
        try { return sim.getFieldFunctionManager().getFunction(n); } catch (Throwable t) { return null; }
    }

    FieldFunction comp(String n, int i) {
        try { return ff(n).getComponentFunction(i); } catch (Throwable t) { return null; }
    }

    public void execute() {
        sim = getActiveSimulation();
        String simName = sim.getPresentationName();
        sim.println("SE-START sim=" + simName);
        Region r = sim.getRegionManager().getObjects().iterator().next();

        Boundary side = null;
        for (Boundary b : r.getBoundaryManager().getObjects()) {
            double cx = avg(b, 0), cy = avg(b, 1), cz = avg(b, 2);
            String ty = "?";
            try { ty = b.getBoundaryType().getPresentationName(); } catch (Throwable t) {}
            sim.println("SE-BND " + b.getPresentationName() + " | type=" + ty
                + " cx=" + String.format("%.5f", cx) + " cy=" + String.format("%.5f", cy)
                + " cz=" + String.format("%.5f", cz));
            if (Math.abs(cy) < 0.01 && Math.abs(cz - 0.5) < 0.05 && Math.abs(cx - 0.8333) < 0.05) side = b;
        }
        if (side == null) { sim.println("SE-ERR 未找到 Y=0 侧平面"); return; }
        sim.println("SE-PICK " + side.getPresentationName());

        java.util.ArrayList<FieldFunction> f = new java.util.ArrayList<>();
        for (FieldFunction x : new FieldFunction[]{
                comp("Velocity", 0), comp("Velocity", 2),
                ff("TurbulentKineticEnergy"), ff("TurbulentViscosityRatio"),
                ff("SpecificDissipationRate"), comp("Pressure", 0),
                comp("Centroid", 0), comp("Centroid", 2)}) {
            if (x != null) f.add(x);
        }
        String out = "C:/Users/Kogami/cb_dl/tmr/run2/slice_" + simName + ".vrt";
        try {
            sim.getExportManager().export(out, java.util.Arrays.asList(r),
                java.util.Arrays.asList(side), java.util.Arrays.asList(), f, true, false);
            sim.println("SE-OK " + out + " nfields=" + f.size());
        } catch (Throwable t) { sim.println("SE-ERR " + t); }
        sim.println("SE-DONE");
    }
}
