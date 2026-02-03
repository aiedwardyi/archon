from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.consume_execution_request import consume as consume_request
from scripts.evaluate_execution_result import consume as consume_evaluation


def _read_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


class SchemaBoundaryTests(unittest.TestCase):
    def test_consumer_writes_visible_error_on_missing_request_file(self):
        with tempfile.TemporaryDirectory() as td:
            public_dir = Path(td) / "public"
            public_dir.mkdir(parents=True, exist_ok=True)

            # No last_execution_request.json exists
            result = consume_request(public_dir)

            self.assertEqual(result.get("status"), "error")
            self.assertTrue((public_dir / "last_execution_result.json").exists())
            self.assertTrue((public_dir / "execution_results.ndjson").exists())

            written = _read_json(public_dir / "last_execution_result.json")
            self.assertEqual(written.get("status"), "error")
            self.assertIn("error", written)

    def test_evaluator_writes_visible_fail_on_missing_execution_result_file(self):
        with tempfile.TemporaryDirectory() as td:
            public_dir = Path(td) / "public"
            public_dir.mkdir(parents=True, exist_ok=True)

            # No last_execution_result.json exists
            evaluation = consume_evaluation(public_dir)

            self.assertEqual(evaluation.get("status"), "fail")
            self.assertTrue((public_dir / "last_evaluation_result.json").exists())
            self.assertTrue((public_dir / "evaluation_results.ndjson").exists())

            written = _read_json(public_dir / "last_evaluation_result.json")
            self.assertEqual(written.get("status"), "fail")


if __name__ == "__main__":
    unittest.main()