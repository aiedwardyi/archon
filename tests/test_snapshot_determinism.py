from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.consume_execution_request import consume


def _read_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def _canonicalize_result_for_compare(result: dict) -> dict:
    """
    Match the repo's determinism-test convention:
    strip any future non-deterministic metadata (today: drop _meta).
    """
    out = dict(result)
    out.pop("_meta", None)
    return out


class TestSnapshotDeterminism(unittest.TestCase):
    def test_execution_result_matches_golden_snapshot_excluding_allowed_nondeterminism(self):
        """
        Why: golden-file regression guard. If deterministic behavior drifts,
        this test fails.
        """
        repo_root = Path(__file__).resolve().parent.parent
        public_dir = repo_root / "apps" / "offline-vite-react" / "public"
        golden_path = repo_root / "tests" / "snapshots" / "execution_result_golden.json"

        self.assertTrue(golden_path.exists(), f"Missing golden snapshot: {golden_path}")

        # Regenerate latest result from current request file
        latest_result = consume(public_dir)

        golden = _read_json(golden_path)
        self.assertEqual(
            _canonicalize_result_for_compare(golden),
            _canonicalize_result_for_compare(latest_result),
        )

        # Also ensure the consumer wrote the artifact we expect
        result_path = public_dir / "last_execution_result.json"
        self.assertTrue(result_path.exists(), f"Missing result artifact: {result_path}")
        last_written = _read_json(result_path)
        self.assertEqual(
            _canonicalize_result_for_compare(last_written),
            _canonicalize_result_for_compare(latest_result),
        )


if __name__ == "__main__":
    unittest.main()
