// api_probe: 枚举 SimulationIterator 与停止准则的真实 API + 迭代上限回读
import star.common.*;
import star.base.neo.*;

public class api_probe extends StarMacro {
    Simulation sim;

    void methods(String tag, Object o) {
        if (o == null) { sim.println("API-" + tag + " NULL"); return; }
        sim.println("API-" + tag + "-CLASS " + o.getClass().getName());
        for (java.lang.reflect.Method m : o.getClass().getMethods()) {
            String n = m.getName();
            if (n.startsWith("get") || n.startsWith("set") || n.startsWith("run")
                    || n.startsWith("step") || n.startsWith("is")) {
                sim.println("API-" + tag + " " + m);
            }
        }
    }

    public void execute() {
        sim = getActiveSimulation();
        sim.println("AP-START");
        sim.getImportManager().importMeshFiles(
            new String[]{"C:/Users/Kogami/cb_dl/tmr/grid_struct_35x25_vol.cgns"});
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
        sim.println("AP-PHYSICS");

        methods("IT", sim.getSimulationIterator());

        Object msc = sim.getSolverStoppingCriterionManager().getObject("Maximum Steps");
        methods("MSC", msc);
        try {
            java.lang.reflect.Method g = msc.getClass().getMethod("get", String.class);
            sim.println("API-MSC-READBACK-before " + g.invoke(msc, "MaximumSteps"));
        } catch (Throwable t) { sim.println("API-MSC-READ-ERR " + t); }
        try {
            java.lang.reflect.Method s = msc.getClass().getMethod("set", String.class, int.class);
            s.invoke(msc, "MaximumSteps", 5000);
            sim.println("API-MSC-SET-INT-OK");
        } catch (Throwable t) { sim.println("API-MSC-SET-INT-ERR " + t); }
        try {
            java.lang.reflect.Method g = msc.getClass().getMethod("get", String.class);
            sim.println("API-MSC-READBACK-after " + g.invoke(msc, "MaximumSteps"));
        } catch (Throwable t) {}

        try {
            java.util.Collection<star.common.SolverStoppingCriterion> cs =
                sim.getSolverStoppingCriterionManager().getObjects();
            for (star.common.SolverStoppingCriterion c : cs) {
                sim.println("API-CRIT " + c.getPresentationName() + " | " + c.getClass().getName());
            }
        } catch (Throwable t) { sim.println("API-CRIT-ERR " + t); }
        sim.println("AP-DONE");
    }
}
