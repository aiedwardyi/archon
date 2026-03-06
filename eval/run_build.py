"""Build a project via the API, poll until done, and take a screenshot."""
import sys, json, logging, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)

from api_client import BuilderAPI

name = sys.argv[1] if len(sys.argv) > 1 else "Test Project"
description = sys.argv[2] if len(sys.argv) > 2 else "A test project"
output_json = sys.argv[3] if len(sys.argv) > 3 else None

api = BuilderAPI("http://localhost:5000")

if not api.health_check():
    print("ERROR: Backend not running at http://localhost:5000")
    sys.exit(1)

print(f"Creating project: {name}")
print(f"Description: {description[:100]}...")

result = api.create_and_build(name, description, timeout=600)
print(f"\nBuild complete!")
print(f"  project_id: {result['project_id']}")
print(f"  version: {result['version']}")
print(f"  preview_url: {result['preview_url']}")

if output_json:
    out = Path(output_json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2))
    print(f"  Saved to {out}")
