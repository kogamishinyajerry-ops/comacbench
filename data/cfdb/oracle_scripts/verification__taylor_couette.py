# oracle: cfdb 参考算例逐字复制（镜像 data/cfdb，上游 b26799e 已验证全跑通）
# 路径为生成期固化的本机仓库根（沙箱内 __file__ 指向临时副本，不可用）
import shutil
from pathlib import Path
src = Path('/Users/Zhuanz/projects/jerry-personal/JerryDSH-COMACBench') / "data/cfdb/verification/taylor_couette"
shutil.copytree(src, "case", dirs_exist_ok=True)
