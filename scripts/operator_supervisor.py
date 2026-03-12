from __future__ import annotations

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_LOG = REPO_ROOT / "operator-loop.out.log"
ERR_LOG = REPO_ROOT / "operator-loop.err.log"
STOP_FILE = REPO_ROOT / "operator-loop.stop"


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with ERR_LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"[{timestamp}] {message}\n")


def main() -> int:
    python_exe = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
    operator_script = REPO_ROOT / "eval" / "operator_loop.py"

    log("operator supervisor starting")

    while True:
        if STOP_FILE.exists():
            log("stop file detected, supervisor exiting")
            try:
                STOP_FILE.unlink()
            except OSError:
                pass
            return 0

        log("launching operator loop child")
        with OUT_LOG.open("ab") as stdout, ERR_LOG.open("ab") as stderr:
            child = subprocess.Popen(
                [
                    str(python_exe),
                    str(operator_script),
                    "--expected-branch",
                    "eval/loops",
                    "--max-cycles",
                    "0",
                    "--commit-wins",
                ],
                cwd=REPO_ROOT,
                stdout=stdout,
                stderr=stderr,
                stdin=subprocess.DEVNULL,
            )

        exit_code = child.wait()
        log(f"operator loop child exited with code {exit_code}")

        if STOP_FILE.exists():
            log("stop file detected after child exit, supervisor exiting")
            try:
                STOP_FILE.unlink()
            except OSError:
                pass
            return 0

        time.sleep(10)


if __name__ == "__main__":
    raise SystemExit(main())
