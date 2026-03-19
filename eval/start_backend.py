"""Start the backend without debug/reloader for eval runs."""
import sys
import os

os.chdir(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, os.getcwd())

# Read and exec app.py with debug=False
code = open("app.py", encoding="utf-8-sig").read()
code = code.replace("app.run(debug=True, port=5000)", "app.run(debug=False, port=5000)")
exec(compile(code, "app.py", "exec"))
