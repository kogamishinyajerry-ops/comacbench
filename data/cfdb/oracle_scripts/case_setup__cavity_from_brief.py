# oracle: cavity_from_brief（managed）——lid_driven_cavity_re400 算例改 Re=100
# （brief: L=0.1, U_lid=1, nu=1e-3, Re=100；held_out centerline_umax=0.665 Ghia 值。
#   re400 算例几何/探针一致，仅 transportProperties nu 2.5e-4 -> 1e-3。）
import shutil
from pathlib import Path

shutil.copytree(Path("/Users/Zhuanz/projects/jerry-personal/JerryDSH-COMACBench")
                / "data/cfdb/validation/lid_driven_cavity_re400", "case", dirs_exist_ok=True)
tp = Path("case/constant/transportProperties")
txt = tp.read_text()
assert "2.5e-4" in txt, "unexpected nu in reference case"
tp.write_text(txt.replace("2.5e-4", "1e-3"))
print("case/ written (Re=100 via nu=1e-3)")
