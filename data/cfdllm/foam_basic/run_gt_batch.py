#!/usr/bin/env python3
"""GT 批量预计算：gt_cases/<族>/<变体> -> gt_runs/<族>/<变体>（docker OpenFOAM v10）。

- 每例：拷贝 GT（源只读）→ docker Allrun → 记录 exit/log 尾/耗时/末时间目录；
- 官方执行判据：log.*Foam 倒数第二行 == "End"；
- 幂等：gt_runs 已存在且 status=ok 的跳过；
- 输出 gt_runs_status.json（逐例状态，供 PROVENANCE/报告引用）。

用法：python3 run_gt_batch.py [--timeout 900] [--force]
"""

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
GT = HERE / "gt_cases"
OUT = HERE / "gt_runs"
IMAGE = "openfoam/openfoam10-paraview510"
DOCKER_ENV = "source /opt/openfoam10/etc/bashrc"


def case_success(case_dir: Path) -> bool:
    """官方 execution_report.py 语义：任一 log.*Foam 倒数第二行 == 'End'。"""
    for p in case_dir.rglob("log.*Foam"):
        try:
            lines = p.read_text(errors="ignore").splitlines()
        except OSError:
            continue
        if len(lines) > 1 and lines[-2].strip() == "End":
            return True
    return False


def last_time_dir(case_dir: Path) -> str | None:
    cands = [d.name for d in case_dir.iterdir()
             if d.is_dir() and d.name.replace(".", "", 1).replace("-", "").isdigit()]
    return max(cands, key=float) if cands else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    status_path = HERE / "gt_runs_status.json"
    status = {} if args.force or not status_path.exists() else json.loads(status_path.read_text())

    cases = sorted(GT.glob("*/*"))
    print(f"[gt-batch] {len(cases)} cases", flush=True)
    for i, case in enumerate(cases, 1):
        rel = f"{case.parent.name}/{case.name}"
        if status.get(rel, {}).get("ok") and not args.force:
            continue
        dst = OUT / rel
        if dst.exists():
            shutil.rmtree(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(case, dst)
        (dst / "Allrun").chmod(0o755)
        t0 = time.time()
        try:
            r = subprocess.run(
                ["docker", "run", "--rm", "--platform", "linux/amd64",
                 "-v", f"{dst}:/case", "-w", "/case",
                 "--entrypoint", "bash", IMAGE,
                 "-c", f"{DOCKER_ENV}; ./Allrun"],
                capture_output=True, text=True, timeout=args.timeout)
            dur = round(time.time() - t0, 1)
            ok = r.returncode == 0 and case_success(dst)
            lt = last_time_dir(dst)
            status[rel] = {"ok": ok, "exit": r.returncode, "dur_s": dur,
                           "last_time": lt,
                           "err": (r.stderr or "")[-200:] if not ok else ""}
            mark = "ok" if ok else "FAIL"
            print(f"[{i}/{len(cases)}] {rel}: {mark} exit={r.returncode} "
                  f"{dur}s last={lt}", flush=True)
        except subprocess.TimeoutExpired:
            status[rel] = {"ok": False, "exit": -1, "dur_s": args.timeout,
                           "last_time": None, "err": "TIMEOUT"}
            print(f"[{i}/{len(cases)}] {rel}: TIMEOUT", flush=True)
        status_path.write_text(json.dumps(status, indent=1))
    n_ok = sum(1 for v in status.values() if v.get("ok"))
    print(f"[gt-batch] done: {n_ok}/{len(status)} ok -> {status_path}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
