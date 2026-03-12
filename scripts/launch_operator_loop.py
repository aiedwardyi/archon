from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_LOG = REPO_ROOT / "operator-loop.out.log"
ERR_LOG = REPO_ROOT / "operator-loop.err.log"
PID_FILE = REPO_ROOT / "operator-loop.pid"


def main() -> int:
    python_exe = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
    supervisor_script = REPO_ROOT / "scripts" / "operator_supervisor.py"

    creationflags = 0
    if sys.platform == "win32":
        creationflags = (
            subprocess.DETACHED_PROCESS
            | subprocess.CREATE_NEW_PROCESS_GROUP
            | subprocess.CREATE_NO_WINDOW
        )

    with OUT_LOG.open("ab") as stdout, ERR_LOG.open("ab") as stderr:
        process = subprocess.Popen(
            [
                str(python_exe),
                str(supervisor_script),
            ],
            cwd=REPO_ROOT,
            stdout=stdout,
            stderr=stderr,
            stdin=subprocess.DEVNULL,
            creationflags=creationflags,
        )

    PID_FILE.write_text(str(process.pid), encoding="utf-8")
    print(process.pid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
