import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import build_file_tree


def test_build_file_tree_skips_runtime_componentized_dirs(tmp_path: Path):
    code_dir = tmp_path / "code"
    src_dir = code_dir / "src"
    node_modules_dir = code_dir / "node_modules"
    dist_dir = code_dir / "dist"
    npm_cache_dir = code_dir / ".npm-cache"

    src_dir.mkdir(parents=True)
    node_modules_dir.mkdir()
    dist_dir.mkdir()
    npm_cache_dir.mkdir()

    (src_dir / "App.tsx").write_text("export default function App() { return null; }\n", encoding="utf-8")
    (code_dir / "package.json").write_text('{"name":"demo"}\n', encoding="utf-8")
    (node_modules_dir / "react.js").write_text("// runtime dependency\n", encoding="utf-8")
    (dist_dir / "index.html").write_text("<!doctype html>\n", encoding="utf-8")
    (npm_cache_dir / "cache.json").write_text("{}\n", encoding="utf-8")

    tree = build_file_tree(code_dir, code_dir)
    paths = []

    def collect(nodes: list[dict]):
        for node in nodes:
            paths.append(node["path"])
            if node.get("children"):
                collect(node["children"])

    collect(tree)

    assert "package.json" in paths
    assert "src" in paths
    assert "src/App.tsx" in paths
    assert "node_modules" not in paths
    assert "dist" not in paths
    assert ".npm-cache" not in paths
