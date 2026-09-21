// FINAL: velocity magnitude+direction, init, solve 500, export Cf
import star.common.*;
import star.base.neo.*;
import star.flow.*;
public class final_ extends StarMacro {
    public void execute() {
        Simulation sim = getActiveSimulation();
        sim.println("FN-START");
        Region r = sim.getRegionManager().getObjects().iterator().next();
        Boundary inlet = r.getBoundaryManager().getBoundary("default 2");
        PhysicsValueManager pvm = inlet.getValues();
        // 1. magnitude 50 m/s
        ScalarProfile mag = (ScalarProfile) pvm.getObject("速度幅值");
        mag.set("Value", 50.0);
        sim.println("FN-1-MAG-OK");
        // 2. direction: 流向规范 -> +X
        try {
            PhysicsConditionManager pcm = inlet.getConditions();
            Object dir = pcm.getObject("流向规范");
            sim.println("FN-2-DIR-CLS: " + dir.getClass().getName());
            // set method to 流向?
            try { dir.getClass().getMethod("setSelectedUserGroupName", String.class); } catch (Throwable t) {}
            // generic: set and select
            ((ClientServerObject) dir).set("Value", new DoubleVector(new double[]{1.0, 0.0, 0.0}));
            sim.println("FN-2-DIR-SET");
        } catch (Throwable t) { sim.println("FN-2-DIR-ERR: " + t.getMessage()); }
        // 3. initialize + solve
        try {
            sim.getSimulationIterator().set("MaximumIterations", 500);
            sim.println("FN-3-MAXIT");
        } catch (Throwable t) { sim.println("FN-3-ERR: " + t.getMessage()); }
        try {
            sim.getSimulationIterator().run(0, false);  // 0 步 = 仅初始化场
            sim.println("FN-4-INIT-OK");
        } catch (Throwable t) { sim.println("FN-4-INIT-ERR: " + t.getMessage()); }
        sim.saveState("C:/Users/Kogami/cb_dl/tmr/run1/flatplate_ready.sim");
        sim.println("FN-SAVED");
        // 4. run
        try {
            sim.getSimulationIterator().run();
            sim.println("FN-5-RUN-OK");
        } catch (Throwable t) { sim.println("FN-5-RUN-ERR: " + t.getMessage()); }
        sim.println("FN-DONE");
    }
}
