// geo273: 只读几何/边界真值 —— 从已解的 fp3d_Q273.sim 取每个边界的类型、质心、面场量。
// 用法：starccm+.bat -batch geo273.java fp3d_Q273.sim
// 目的：钉死 (1) 导出件 "default" 是哪张面；(2) 上游条带的真实类型；(3) 入口剖面是否均匀。
import star.common.*;
import star.base.neo.*;

public class geo273 extends StarMacro {
    Simulation sim;

    double areaAvg(Boundary b, FieldFunction f) {
        try {
            star.base.report.AreaAverageReport r = sim.getReportManager()
                .createReport(star.base.report.AreaAverageReport.class);
            r.setFieldFunction(f);
            r.getParts().setObjects(b);
            return r.getReportMonitorValue();
        } catch (Throwable t) { return Double.NaN; }
    }

    FieldFunction ff(String n) {
        try { return sim.getFieldFunctionManager().getFunction(n); }
        catch (Throwable t) { sim.println("  FF-ERR " + n); return null; }
    }

    FieldFunction comp(String n, int i) {
        try { return ff(n).getComponentFunction(i); }
        catch (Throwable t) { sim.println("  FF-COMP-ERR " + n + "[" + i + "]"); return null; }
    }

    void probe(String cls) {
        try { Class.forName(cls); sim.println("  CLS-OK  " + cls); }
        catch (Throwable t) { sim.println("  CLS-NO  " + cls); }
    }

    public void execute() {
        sim = getActiveSimulation();
        sim.println("G-START sim=" + sim.getPresentationName());

        sim.println("--- 报表类可用性探测 ---");
        probe("star.base.report.AreaAverageReport");
        probe("star.base.report.SurfaceAreaReport");
        probe("star.base.report.SurfaceAreaAverageReport");
        probe("star.base.report.ExpressionReport");
        probe("star.base.report.MassFlowReport");
        probe("star.base.report.MinimumReport");
        probe("star.base.report.MaximumReport");

        Region r = sim.getRegionManager().getObjects().iterator().next();
        sim.println("--- region=" + r.getPresentationName()
            + "  nBounds=" + r.getBoundaryManager().getObjects().size());

        FieldFunction cx = comp("Centroid", 0);
        FieldFunction cy = comp("Centroid", 1);
        FieldFunction cz = comp("Centroid", 2);
        FieldFunction vi = comp("Velocity", 0);
        FieldFunction tke = ff("TurbulentKineticEnergy");
        FieldFunction tvr = ff("TurbulentViscosityRatio");
        FieldFunction sdr = ff("SpecificDissipationRate");
        FieldFunction p = comp("Pressure", 0);

        for (Boundary b : r.getBoundaryManager().getObjects()) {
            String nm = b.getPresentationName();
            String ty = "?";
            try { ty = b.getBoundaryType().getPresentationName(); } catch (Throwable t) {}
            sim.println("GB " + nm + " | type=" + ty
                + " | cx=" + String.format("%.5f", areaAvg(b, cx))
                + " cy=" + String.format("%.5f", areaAvg(b, cy))
                + " cz=" + String.format("%.5f", areaAvg(b, cz))
                + " | u=" + String.format("%.5f", areaAvg(b, vi))
                + " | k=" + String.format("%.5e", areaAvg(b, tke))
                + " | tvr=" + String.format("%.5e", areaAvg(b, tvr))
                + " | om=" + String.format("%.5e", areaAvg(b, sdr))
                + " | p=" + String.format("%.6f", areaAvg(b, p)));
        }

        sim.println("G-DONE");
    }
}
