Context [1]:
Trajectory analysis performs a key role in the design of aircraft by modeling performance over the course of a mission. Often, for aircraft, fuel burn or range are the primary quantities of interest, but trajectory analysis results are also important for aircraft noise prediction, propulsion sizing, and operational performance prediction. Trajectory analysis tools model aircraft performance over time via numerical integration of governing equations of motion. There are many implementations of mission analysis, using different formulations and methods. Flight Optimization System (FLOPS) is a NASA developed code built with the well developed energy state approximation that simplifies trajectory analysis to an exchange between potential and kinetic energy. The simplification allows for an efficient implementation, but effectively uses a 2 degree of freedom model that lacks information about angle of attack, roll, and yaw. Two newer tools, SUAVE and PyMission, abandon the energy state approximation in favor of a collocation based approach that does account for aircraft angle of attack. The OTIS tool also uses collocation based approach, but combined with an implicit time integration scheme that offers potential computational savings. OTIS has more commonly been applied to spacecraft trajectory optimization and optimal control, but its approach is equally applicable to aircraft trajectory optimization.

Question: Does PyMission account for the roll angle of the aircraft?

Answer using ONLY the information in the contexts above.
Respond EXACTLY in this three-line format:
ANSWER: <your answer in one short sentence; write REFUSED if the contexts do not contain the answer>
BASIS: <report | computed | inferred>  (report = stated in the contexts; computed = derived by calculation; inferred = your own inference)
CITATION: <the context number(s) you used or checked, e.g. [1] or [1,2]>
