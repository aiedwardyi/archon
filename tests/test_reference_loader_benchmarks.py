from eval.reference_loader import BENCHMARK_ARCHETYPE_ALIASES, ReferenceLoader
from utils.reference_build_registry import (
    get_sorted_reference_build_entries,
    resolve_reference_build_source_paths,
)


def test_fintech_benchmark_alias_uses_dashboard_entries():
    loader = ReferenceLoader()

    assert loader._benchmark_archetype("fintech") == "dashboard"
    assert len(get_sorted_reference_build_entries(loader._benchmark_archetype("fintech"))) > 0


def test_editor_benchmark_entries_have_resolvable_source_paths():
    entries = get_sorted_reference_build_entries("editor")

    assert len(entries) > 0
    source_paths = resolve_reference_build_source_paths(entries[0])
    assert source_paths is not None
    assert source_paths["html_path"].exists()
    assert source_paths["css_path"].exists()
