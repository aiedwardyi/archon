# Deterministic test runner (Windows PowerShell)
# Why: ensures unittest discovery always runs the same way on every machine.

$ErrorActionPreference = "Stop"

$python = ".\venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
  throw "Python venv not found at $python. Activate/create venv first."
}

& $python -m unittest discover -s tests -p "test_*.py" -v
exit $LASTEXITCODE
