import io
import os
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import app as backend_app


@pytest.fixture()
def client():
    backend_app.app.config["TESTING"] = True
    with backend_app.app.test_client() as c:
        yield c


def _write(path: Path, content: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


def test_build_file_tree_hides_binary_assets_and_lockfiles(tmp_path):
    code_dir = tmp_path / "code"
    _write(code_dir / "src" / "App.tsx", "export default function App() { return <div /> }\n")
    _write(code_dir / "public" / "generated-assets" / "hero.png", b"\x89PNG\r\n")
    _write(code_dir / "package-lock.json", '{"name":"demo"}')
    _write(code_dir / "vite.config.ts", "export default {}\n")

    tree = backend_app.build_file_tree(code_dir, code_dir)

    assert any(node["path"] == "src" for node in tree)
    assert any(node["path"] == "vite.config.ts" for node in tree)
    flat_paths = []

    def _flatten(nodes):
        for node in nodes:
            flat_paths.append(node["path"])
            for child in node.get("children", []):
                _flatten([child])

    _flatten(tree)

    assert "public/generated-assets/hero.png" not in flat_paths
    assert "package-lock.json" not in flat_paths
    assert "public/generated-assets" not in flat_paths


def test_normalize_factsheet_metrics_recounts_outputs_from_visible_source_tree(monkeypatch, tmp_path):
    monkeypatch.setattr(backend_app, "PUBLIC_DIR", tmp_path)

    version_dir = backend_app.get_version_dir(77, 1)
    code_dir = version_dir / "code"
    _write(code_dir / "src" / "App.tsx", "export default function App() { return <div /> }\n")
    _write(code_dir / "src" / "main.tsx", "console.log('boot')\n")
    _write(code_dir / "public" / "generated-assets" / "hero.png", b"\x89PNG\r\n")

    factsheet = {
        "pipeline": {"status": "success", "duration_seconds": 12, "ui_archetype": "game"},
        "outputs": {"files_generated": 0, "images_generated": 0},
        "scoring": {
            "prompt_quality": {"score": 80},
            "build_confidence": {"score": 50, "label": "fair", "breakdown": []},
        },
        "quality_indicators": [],
        "readiness": {},
        "compliance": {},
    }

    normalized = backend_app.normalize_factsheet_metrics(77, 1, factsheet)

    assert normalized["outputs"] == {"files_generated": 2, "images_generated": 1}
    assert normalized["scoring"]["build_confidence"]["score"] == 100
    assert normalized["readiness"]["combined_score"] == 90.0
    assert any(qi["indicator"] == "Code generated" for qi in normalized["quality_indicators"])


def test_download_endpoint_skips_runtime_and_install_directories(client, monkeypatch, tmp_path):
    monkeypatch.setattr(backend_app, "PUBLIC_DIR", tmp_path)

    code_dir = backend_app.get_version_dir(88, 1) / "code"
    _write(code_dir / "src" / "App.tsx", "export default function App() { return <div /> }\n")
    _write(code_dir / "node_modules" / "pkg" / "index.js", "module.exports = {}\n")
    _write(code_dir / "dist" / "assets" / "bundle.js", "console.log('dist')\n")
    _write(code_dir / ".npm-cache" / "tmp" / "cache.txt", "cache\n")
    _write(code_dir / "public" / "generated-assets" / "hero.png", b"\x89PNG\r\n")

    response = client.get("/api/projects/88/versions/1/download")

    assert response.status_code == 200

    archive = zipfile.ZipFile(io.BytesIO(response.data))
    names = archive.namelist()

    assert "src/App.tsx" in names
    assert "public/generated-assets/hero.png" in names
    assert not any(name.startswith("node_modules/") for name in names)
    assert not any(name.startswith("dist/") for name in names)
    assert not any(name.startswith(".npm-cache/") for name in names)
