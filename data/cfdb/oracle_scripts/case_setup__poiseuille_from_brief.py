# oracle: poiseuille_from_brief（managed）——参考算例 verification/channel_poiseuille
# （H=0.01, L=0.12, U0=0.1, nu=5e-5, probes at x/H=10——与 brief 参数一致）
import shutil
from pathlib import Path
shutil.copytree(Path("/Users/Zhuanz/projects/jerry-personal/JerryDSH-COMACBench") / "data/cfdb/verification/channel_poiseuille", "case", dirs_exist_ok=True)
print("case/ written from reference case")
