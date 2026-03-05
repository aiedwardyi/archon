"""
Load and organize reference images for vision API scoring.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

ARCHETYPES_DIR = Path(__file__).resolve().parent.parent / "archetypes"
GOOD_DIR = ARCHETYPES_DIR / "good_examples"
BAD_DIR = ARCHETYPES_DIR / "bad_examples"

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

    def get_good_examples(self, archetype: str, max_count: int = 4) -> list[tuple[str, Path]]:
        """Get good reference images for an archetype.

        Returns list of (label, path) tuples.
        """
        mapping = REFERENCE_MAP.get(archetype, {})
        patterns = mapping.get("good", [])

        if not patterns:
            # Fallback: try finding any images that match the archetype name
            fallback_patterns = [f"{archetype}*.png", f"{archetype}*.jpg"]
            results = self._resolve_files(self.good_dir, fallback_patterns, max_count)
            if results:
                logger.info(f"Found {len(results)} fallback good examples for '{archetype}'")
            return results

        results = self._resolve_files(self.good_dir, patterns, max_count)
        logger.info(f"Loaded {len(results)} good examples for '{archetype}'")
        return results

    def get_bad_examples(self, archetype: str, max_count: int = 2) -> list[tuple[str, Path]]:
        """Get bad reference images for an archetype.

        Returns list of (label, path) tuples.
        """
        mapping = REFERENCE_MAP.get(archetype, {})
        patterns = mapping.get("bad", [])

        if not patterns:
            # Fallback: try finding bad examples that match
            fallback_patterns = [f"bad_{archetype}*.png"]
            return self._resolve_files(self.bad_dir, fallback_patterns, max_count)

        results = self._resolve_files(self.bad_dir, patterns, max_count)
        logger.info(f"Loaded {len(results)} bad examples for '{archetype}'")
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
