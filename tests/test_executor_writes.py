from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path

from scripts.consume_execution_request import consume

TMP_ROOT = Path(__file__).resolve().parent.parent / ".tmp-tests"
TMP_ROOT.mkdir(parents=True, exist_ok=True)


def _write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


class ExecutorWritesTests(unittest.TestCase):
    def test_write_public_note_is_deterministic_and_allowlisted(self):
        req = {
            "kind": "execution_request",
            "task_id": "OFFLINE-NOTE-1",
            "milestone_id": "MS-1",
            "title": "Write note",
            "created_at": "2099-01-01T00:00:00+00:00",
            "payload": {
                "action": "write_public_note",
                "content": "hello deterministic world\n",
            },
            "_meta": {"source_ip": "127.0.0.1", "received_at": "2099-01-01T00:00:00+00:00"},
        }

        case_dir = TMP_ROOT / "executor-writes"
        shutil.rmtree(case_dir, ignore_errors=True)
        case_dir.mkdir(parents=True, exist_ok=True)
        try:
            public_dir = case_dir / "public"
            _write_json(public_dir / "last_execution_request.json", req)

            r1 = consume(public_dir)
            r2 = consume(public_dir)

            self.assertEqual(r1["status"], "success")
            self.assertEqual(r1["request_hash"], r2["request_hash"])
            self.assertEqual(r1["outputs"], r2["outputs"])

            gen_dir = public_dir / "generated"
            self.assertTrue(gen_dir.exists())

            note_path = Path(r1["outputs"]["note_path"])
            self.assertTrue(note_path.exists())
            self.assertTrue(str(note_path).startswith(str(gen_dir)))

            # content stable
            self.assertEqual(note_path.read_text(encoding="utf-8"), "hello deterministic world\n")
        finally:
            shutil.rmtree(case_dir, ignore_errors=True)

    def test_iteration_scope_enforced(self):
        from scripts.safe_write import enforce_iteration_scope

        class _F:
            def __init__(self, path: str):
                self.path = path

        allowed = ["src/style.css"]
        outputs = [_F("src/style.css"), _F("src/index.html")]

        with self.assertRaises(ValueError) as ctx:
            enforce_iteration_scope(allowed, outputs)

        self.assertIn("src/index.html", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
