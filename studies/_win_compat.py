"""Windows compatibility shim for the POSIX fcntl surface used by studies/.

Mirrors the msvcrt.locking shim already shipped in comacbench/__main__.py:
same contract (exclusive, non-blocking), same failure mode (OSError on
contention), so lock-guarded study entry points behave identically on
Windows. Never changes study semantics or scores.
"""
import sys

if sys.platform == 'win32':
    import msvcrt

    LOCK_EX = 2
    LOCK_NB = 4

    def _flock(fd, _flags):
        # msvcrt.locking with LK_NBLCK is exclusive + non-blocking; a held
        # lock raises OSError (EACCES/EDEADLK), matching the POSIX contract
        # the callers catch.
        msvcrt.locking(fd.fileno(), msvcrt.LK_NBLCK, 1)

    class fcntl:  # minimal shim of the POSIX module surface we use
        LOCK_EX = LOCK_EX
        LOCK_NB = LOCK_NB
        flock = staticmethod(_flock)
else:
    import fcntl  # noqa: F401  (re-exported for callers importing from here)
    LOCK_EX = fcntl.LOCK_EX
    LOCK_NB = fcntl.LOCK_NB
