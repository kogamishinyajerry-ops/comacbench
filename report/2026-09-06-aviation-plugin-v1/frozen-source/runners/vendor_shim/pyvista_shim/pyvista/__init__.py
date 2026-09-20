"""pyvista import shim (NOT installed into any venv).

Why this exists: runners/simulation_agent.py unconditionally imports
runners.foam_nmse (which imports pyvista) inside run_task(), even for
exec_kind=aviary_mission/pycycle_cycle tasks that never touch NMSE grading.
.venv-aviary (aviary stack) has no pyvista, and both the runner file and the
venv packages are frozen for this task. This stub satisfies the module-level
import ONLY; if any code path actually uses pyvista attributes it raises
loudly instead of silently pretending.
"""


def __getattr__(name):  # PEP 562
    raise RuntimeError(
        f"pyvista shim: attribute {name!r} requested — real pyvista is not "
        "available in this interpreter; NMSE grading must run under .venv")
