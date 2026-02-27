import requests
import json

base = "http://localhost:5000"

# Step 1: get all projects
projects = requests.get(f"{base}/api/projects").json()
completed = [p for p in projects if p.get("status", "").lower() in ("completed", "success")]
print(f"Found {len(completed)} completed projects: {[p['id'] for p in completed]}")

if not completed:
    print("No completed projects to test.")
    exit()

# Test first 3 completed projects
for project in completed[:3]:
    pid = project["id"]
    print(f"\n--- Project {pid}: {project.get('name', '')} ---")

    # Get head version
    head = requests.get(f"{base}/api/projects/{pid}/head").json()
    version = head.get("version")
    print(f"Head version: {version}")

    if not version:
        print("No head version found, skipping.")
        continue

    # Get file tree
    tree_res = requests.get(f"{base}/api/projects/{pid}/versions/{version}/files")
    print(f"File tree status: {tree_res.status_code}")
    tree_data = tree_res.json()
    print(f"Tree keys: {list(tree_data.keys())}")

    tree = tree_data.get("tree", [])
    print(f"Tree nodes: {len(tree)}")

    # Flatten tree
    def flatten(nodes):
        paths = []
        for n in nodes:
            if n.get("type") == "file":
                paths.append(n["path"])
            elif n.get("type") == "folder":
                paths.extend(flatten(n.get("children", [])))
        return paths

    file_paths = flatten(tree)
    print(f"Files found: {file_paths}")

    # Fetch content of each file
    for path in file_paths:
        res = requests.get(f"{base}/api/projects/{pid}/versions/{version}/files", params={"path": path})
        print(f"  {path}: status={res.status_code}, content_length={len(res.json().get('content', ''))}")
