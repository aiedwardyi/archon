from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.replay_execution_request import replay


def _append_ndjson(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class ReplayRunnerTests(unittest.TestCase):
    def test_replay_latest_request_writes_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            public_dir = Path(td) / "public"
            public_dir.mkdir(parents=True, exist_ok=True)

            # Create an NDJSON history with a single valid request
            req = {
                "kind": "execution_request",
                "task_id": "REPLAY-TEST-1",
                "milestone_id": "MS-REPLAY",
                "title": "Replay test request",
                "created_at": "2099-01-01T00:00:00+00:00",
                "payload": {
                    "action": "write_public_note",
                    "content": "Replay runner test note.\n",
                    "filename": "replay-test.md",
                },
            }
            _append_ndjson(public_dir / "execution_requests.ndjson", req)

            result = replay(public_dir=public_dir)

            self.assertEqual(result.get("status"), "success")
            self.assertTrue((public_dir / "last_execution_request.json").exists())
            self.assertTrue((public_dir / "last_execution_result.json").exists())
            self.assertTrue((public_dir / "execution_results.ndjson").exists())

            # Evaluation should exist on success
            self.assertTrue((public_dir / "last_evaluation_result.json").exists())
            self.assertTrue((public_dir / "evaluation_results.ndjson").exists())

            written_req = _read_json(public_dir / "last_execution_request.json")
            self.assertEqual(written_req.get("task_id"), "REPLAY-TEST-1")

    def test_replay_by_index(self):
        with tempfile.TemporaryDirectory() as td:
            public_dir = Path(td) / "public"
            public_dir.mkdir(parents=True, exist_ok=True)

            req1 = {
                "kind": "execution_request",
                "task_id": "REPLAY-TEST-A",
                "milestone_id": "MS-REPLAY",
                "title": "A",
                "created_at": "2099-01-01T00:00:00+00:00",
                "payload": {
                    "action": "write_public_note",
                    "content": "A\n",
                    "filename": "a.md",
                },
            }
            req2 = {
                "kind": "execution_request",
                "task_id": "REPLAY-TEST-B",
                "milestone_id": "MS-REPLAY",
                "title": "B",
                "created_at": "2099-01-01T00:00:00+00:00",
                "payload": {
                    "action": "write_public_note",
                    "content": "B\n",
                    "filename": "b.md",
                },
            }

            _append_ndjson(public_dir / "execution_requests.ndjson", req1)
            _append_ndjson(public_dir / "execution_requests.ndjson", req2)

            # index=0 should replay req1
            result = replay(public_dir=public_dir, index=0)
            self.assertEqual(result.get("status"), "success")

            written_req = _read_json(public_dir / "last_execution_request.json")
            self.assertEqual(written_req.get("task_id"), "REPLAY-TEST-A")


if __name__ == "__main__":
    unittest.main()