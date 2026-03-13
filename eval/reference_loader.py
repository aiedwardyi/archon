"""
Load and organize reference images for vision API scoring.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
PROMPT_REFS_DIR = ROOT / "prompts" / "archetypes" / "references"
LEGACY_ARCHETYPES_DIR = ROOT / "archetypes"
GOOD_DIR = LEGACY_ARCHETYPES_DIR / "good_examples"
BAD_DIR = LEGACY_ARCHETYPES_DIR / "bad_examples"
CACHE_DIR = ROOT / "eval" / ".reference_cache"
ARCHETYPE_ALIASES = {
    "game_ff7": "game",
    "game_ff8": "game",
    "game_ff9": "game",
}
BENCHMARK_ARCHETYPE_ALIASES = {
    "fintech": "dashboard",
}

try:
    from screenshotter import capture_sync
except ImportError:
    from eval.screenshotter import capture_sync
from utils.reference_build_registry import (
    get_sorted_reference_build_entries,
    resolve_reference_build_source_paths,
)

# Mapping from archetype name to glob patterns for good/bad examples
REFERENCE_MAP = {
    "dashboard": {
        "good": ["dashboard.png", "dashboard2.png", "dashboard3.png", "dashbboard4.png"],
        "bad": ["bad_dashboard*.png"],
    },
    "game": {
        "good": ["game-fanpage.png", "game-fanpage2.png", "game-fanpage3.png", "game-fanpage4.png"],
        "bad": ["bad_game*.png", "bad_fantasy*.png"],
    },
    "saas_landing": {
        "good": ["website.png", "website2.png", "website3.png"],
        "bad": [],
    },
    "fintech": {
        "good": ["dashboard.png", "dashboard2.png"],  # Fintech dashboards are similar
        "bad": ["bad_dashboard*.png"],
    },
    "ecommerce": {
        "good": ["website.png", "website2.png"],
        "bad": [],
    },
    "portfolio": {
        "good": ["website.png", "website2.png"],  # Closest available references
        "bad": [],
    },
}


class ReferenceLoader:
    def __init__(self, good_dir: Path = None, bad_dir: Path = None):
        self.good_dir = good_dir or GOOD_DIR
        self.bad_dir = bad_dir or BAD_DIR

    def _resolve_files(self, directory: Path, patterns: list[str], max_count: int = 4) -> list[tuple[str, Path]]:
        """Resolve glob patterns to actual file paths.

        Returns list of (label, path) tuples.
        """
        results = []
        for pattern in patterns:
            if "*" in pattern:
                # Glob pattern
                for p in sorted(directory.glob(pattern)):
                    if p.is_file():
                        results.append((p.stem, p))
            else:
                # Exact filename
                p = directory / pattern
                if p.is_file():
                    results.append((p.stem, p))

        # Deduplicate by path
        seen = set()
        unique = []
        for label, path in results:
            if path not in seen:
                seen.add(path)
                unique.append((label, path))

        return unique[:max_count]

    def _canonicalize_archetype(self, archetype: str) -> str:
        return ARCHETYPE_ALIASES.get(str(archetype).strip().lower(), str(archetype).strip().lower())

    def _benchmark_archetype(self, archetype: str) -> str:
        canonical = self._canonicalize_archetype(archetype)
        return BENCHMARK_ARCHETYPE_ALIASES.get(canonical, canonical)

    def _benchmark_cache_path(self, entry: dict[str, object]) -> Path:
        label = str(entry.get("label", "benchmark")).strip() or "benchmark"
        slug = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in label).strip("-")
        return CACHE_DIR / f"{slug}.png"

    def _ensure_benchmark_screenshot(self, entry: dict[str, object]) -> Path | None:
        source_paths = resolve_reference_build_source_paths(entry)
        if source_paths is None:
            return None

        screenshot_path = self._benchmark_cache_path(entry)
        html_path = source_paths["html_path"]
        css_path = source_paths["css_path"]
        base_css_path = source_paths["base_css_path"]

        source_mtimes = [html_path.stat().st_mtime, css_path.stat().st_mtime]
        if base_css_path.exists():
            source_mtimes.append(base_css_path.stat().st_mtime)
        latest_source_mtime = max(source_mtimes)

        if screenshot_path.exists() and screenshot_path.stat().st_mtime >= latest_source_mtime:
            return screenshot_path

        try:
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            capture_sync(
                html_path.resolve().as_uri(),
                screenshot_path,
                wait_seconds=0.5,
                full_page=True,
            )
            return screenshot_path
        except Exception as exc:
            logger.warning(
                "Failed to render benchmark screenshot for '%s': %s",
                entry.get("label", "benchmark"),
                exc,
            )
            return None

    def _load_benchmark_references(self, archetype: str, max_count: int = 4) -> list[tuple[str, Path]]:
        benchmark_archetype = self._benchmark_archetype(archetype)
        entries = get_sorted_reference_build_entries(benchmark_archetype)
        results: list[tuple[str, Path]] = []
        for entry in entries[:max_count]:
            screenshot_path = self._ensure_benchmark_screenshot(entry)
            if screenshot_path is None:
                continue
            label = str(entry.get("label", screenshot_path.stem))
            results.append((label, screenshot_path))
        if results:
            logger.info(
                "Loaded %s benchmark reference screenshots for '%s'",
                len(results),
                benchmark_archetype,
            )
        return results

    def _load_prompt_reference_dir(self, archetype: str, max_count: int = 4) -> list[tuple[str, Path]]:
        canonical = self._canonicalize_archetype(archetype)
        refs_dir = PROMPT_REFS_DIR / canonical
        if not refs_dir.exists():
            return []
        files = [
            (path.stem, path)
            for path in sorted(refs_dir.iterdir())
            if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif"}
        ]
        if files:
            logger.info(f"Loaded {len(files[:max_count])} prompt reference images for '{canonical}'")
        return files[:max_count]

    def get_good_examples(self, archetype: str, max_count: int = 4) -> list[tuple[str, Path]]:
        """Get good reference images for an archetype.

        Returns list of (label, path) tuples.
        """
        benchmark_refs = self._load_benchmark_references(archetype, max_count=max_count)
        prompt_refs = self._load_prompt_reference_dir(archetype, max_count=max_count)
        merged: list[tuple[str, Path]] = []
        seen: set[Path] = set()
        for label, path in benchmark_refs + prompt_refs:
            if path in seen:
                continue
            seen.add(path)
            merged.append((label, path))
            if len(merged) >= max_count:
                break
        if merged:
            return merged

        canonical = self._canonicalize_archetype(archetype)
        mapping = REFERENCE_MAP.get(canonical, {})
        patterns = mapping.get("good", [])

        if not patterns:
            # Fallback: try finding any images that match the archetype name
            fallback_patterns = [f"{canonical}*.png", f"{canonical}*.jpg"]
            results = self._resolve_files(self.good_dir, fallback_patterns, max_count)
            if results:
                logger.info(f"Found {len(results)} fallback good examples for '{canonical}'")
            return results

        results = self._resolve_files(self.good_dir, patterns, max_count)
        logger.info(f"Loaded {len(results)} good examples for '{canonical}'")
        return results

    def get_bad_examples(self, archetype: str, max_count: int = 2) -> list[tuple[str, Path]]:
        """Get bad reference images for an archetype.

        Returns list of (label, path) tuples.
        """
        canonical = self._canonicalize_archetype(archetype)
        mapping = REFERENCE_MAP.get(canonical, {})
        patterns = mapping.get("bad", [])

        if not patterns:
            # Fallback: try finding bad examples that match
            fallback_patterns = [f"bad_{canonical}*.png"]
            return self._resolve_files(self.bad_dir, fallback_patterns, max_count)

        results = self._resolve_files(self.bad_dir, patterns, max_count)
        logger.info(f"Loaded {len(results)} bad examples for '{canonical}'")
        return results

    def list_available(self) -> dict[str, dict[str, int]]:
        """List how many good/bad references are available per archetype."""
        result = {}
        for archetype in REFERENCE_MAP:
            good = self.get_good_examples(archetype)
            bad = self.get_bad_examples(archetype)
            result[archetype] = {"good": len(good), "bad": len(bad)}
        return result


if __name__ == "__main__":
    loader = ReferenceLoader()
    print("Available reference images:")
    for arch, counts in loader.list_available().items():
        print(f"  {arch}: {counts['good']} good, {counts['bad']} bad")
