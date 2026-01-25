from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.consume_execution_request import consume


def _read_json(p: Path) -> dict:
    # Windows editors sometimes introduce a UTF-8 BOM; utf-8-sig handles both BOM and non-BOM.
    return json.loads(p.read_text(encoding="utf-8-sig"))


def _strip_meta(d: dict) -> dict:
    out = dict(d)
    out.pop("_meta", None)
    return out


class TestSnapshotDeterminism(unittest.TestCase):
    def test_execution_and_evaluation_match_golden_snapshots(self):
        repo_root = Path(__file__).resolve().parent.parent
        public_dir = repo_root / "apps" / "offline-vite-react" / "public"

        exec_golden_path = repo_root / "tests" / "snapshots" / "execution_result_golden.json"
        eval_golden_path = repo_root / "tests" / "snapshots" / "evaluation_result_golden.json"

        self.assertTrue(exec_golden_path.exists(), f"Missing golden snapshot: {exec_golden_path}")
        self.assertTrue(eval_golden_path.exists(), f"Missing golden snapshot: {eval_golden_path}")

        latest_exec = consume(public_dir)

        exec_golden = _read_json(exec_golden_path)
        self.assertEqual(_strip_meta(latest_exec), _strip_meta(exec_golden))

        # Assert the consumer wrote the same execution artifact
        exec_written_path = public_dir / "last_execution_result.json"
        self.assertTrue(exec_written_path.exists(), f"Missing artifact: {exec_written_path}")
        exec_written = _read_json(exec_written_path)
        self.assertEqual(_strip_meta(exec_written), _strip_meta(latest_exec))

        # Assert evaluator artifact matches golden
        eval_written_path = public_dir / "last_evaluation_result.json"
        self.assertTrue(eval_written_path.exists(), f"Missing evaluation artifact: {eval_written_path}")
        eval_written = _read_json(eval_written_path)

        eval_golden = _read_json(eval_golden_path)
        self.assertEqual(_strip_meta(eval_written), _strip_meta(eval_golden))


if __name__ == "__main__":
    unittest.main()