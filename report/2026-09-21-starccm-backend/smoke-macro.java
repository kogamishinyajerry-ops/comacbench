import star.common.*;

public class macro extends StarMacro {
    public void execute() {
        Simulation sim = getActiveSimulation();
        sim.println("COMAC_SMOKE_OK");
    }
}
