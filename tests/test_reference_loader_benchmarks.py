import asyncio

from eval.reference_loader import ReferenceLoader
from utils.reference_build_registry import (
    get_sorted_reference_build_entries,
    resolve_reference_build_source_paths,
)


def test_fintech_benchmark_entries_have_resolvable_source_paths():
    loader = ReferenceLoader()

    assert loader._benchmark_archetype("fintech") == "fintech"
    entries = get_sorted_reference_build_entries("fintech")
    assert len(entries) > 0

    source_paths = resolve_reference_build_source_paths(entries[0])
    assert source_paths is not None
    assert source_paths["html_path"].exists()
    assert source_paths["css_path"].exists()


def test_editor_benchmark_entries_have_resolvable_source_paths():
    entries = get_sorted_reference_build_entries("editor")

    assert len(entries) > 0
    source_paths = resolve_reference_build_source_paths(entries[0])
    assert source_paths is not None
    assert source_paths["html_path"].exists()
    assert source_paths["css_path"].exists()


def test_reference_loader_uses_subprocess_when_asyncio_loop_is_running(monkeypatch, tmp_path):
    loader = ReferenceLoader()
    entry = get_sorted_reference_build_entries("editor")[0]
    screenshot_path = loader._benchmark_cache_path(entry)
    source_paths = resolve_reference_build_source_paths(entry)
    assert source_paths is not None

    called = {}

    def fake_run(cmd, check, cwd):
        called["cmd"] = cmd
        called["cwd"] = cwd
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        screenshot_path.write_bytes(b"fake-png")
        return None

    monkeypatch.setattr("eval.reference_loader.subprocess.run", fake_run)

    async def run_test():
        path = loader._ensure_benchmark_screenshot(entry)
        assert path == screenshot_path

    asyncio.run(run_test())

    assert called["cmd"][0]
    assert called["cmd"][1:3] == ["-m", "eval.screenshotter"]
    assert called["cwd"]
