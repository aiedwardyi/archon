from __future__ import annotations

import shutil
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from utils.componentized_runtime import build_componentized_preview, collect_existing_code_context


TMP_ROOT = REPO_ROOT / ".tmp-tests"
TMP_ROOT.mkdir(parents=True, exist_ok=True)


def _case_dir(name: str) -> Path:
    path = TMP_ROOT / name
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True, exist_ok=True)
    return path


class ComponentizedPreviewRuntimeTests(unittest.TestCase):
    def test_build_componentized_preview_uses_workspace_local_npm_cache(self):
        code_dir = _case_dir("componentized-preview-local-cache")
        try:
            (code_dir / "package.json").write_text(
                '{"name":"demo","scripts":{"build":"vite build"}}\n',
                encoding="utf-8",
            )
            captured_envs: list[dict[str, str]] = []

            def fake_run(
                command: list[str],
                cwd: Path,
                capture_output: bool,
                text: bool,
                timeout: int,
                env: dict[str, str],
                check: bool,
                **kwargs: object,
            ) -> SimpleNamespace:
                del cwd, capture_output, text, timeout, check, kwargs
                captured_envs.append(env)
                if command[-2:] == ["run", "build"]:
                    dist_dir = code_dir / "dist"
                    dist_dir.mkdir(parents=True, exist_ok=True)
                    (dist_dir / "index.html").write_text("<!doctype html><html></html>\n", encoding="utf-8")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            with mock.patch("utils.componentized_runtime.subprocess.run", side_effect=fake_run) as run_mock:
                result = build_componentized_preview(code_dir)

            npm_cache_dir = code_dir / ".npm-cache"
            self.assertEqual(result["status"], "success")
            self.assertTrue(npm_cache_dir.exists())
            self.assertEqual(captured_envs[0]["npm_config_cache"], str(npm_cache_dir))
            self.assertEqual(captured_envs[0]["NPM_CONFIG_CACHE"], str(npm_cache_dir))
            self.assertEqual(run_mock.call_count, 2)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)

    def test_collect_existing_code_context_skips_workspace_local_npm_cache(self):
        code_dir = _case_dir("componentized-preview-context-skip-npm-cache")
        try:
            (code_dir / "package.json").write_text('{"name":"demo"}\n', encoding="utf-8")
            (code_dir / ".npm-cache").mkdir()
            (code_dir / ".npm-cache" / "cache-entry.json").write_text('{"ignored":true}\n', encoding="utf-8")
            (code_dir / "src").mkdir()
            (code_dir / "src" / "App.tsx").write_text(
                "export default function App() { return null; }\n",
                encoding="utf-8",
            )

            context = collect_existing_code_context(code_dir)

            self.assertIn("--- FILE: package.json ---", context)
            self.assertIn("--- FILE: src/App.tsx ---", context)
            self.assertNotIn("cache-entry.json", context)
        finally:
            shutil.rmtree(code_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
