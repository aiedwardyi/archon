from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.consume_execution_request import (
    canonicalize_request,
    consume,
    sha256_of,
)


def _write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _read_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def _canonicalize_result_for_compare(result: dict) -> dict:
    """
    The consumer may write append-only logs or overwrite results; for determinism we
    compare only stable fields.
    Today: everything should be stable for the same request, so we compare the whole result.
    If you later add non-deterministic metadata, strip it here (e.g. _meta.produced_at).
    """
    # Defensive: if a future version adds _meta timestamps, strip them:
    out = dict(result)
    out.pop("_meta", None)
    return out


class DeterminismTests(unittest.TestCase):
    def test_same_semantic_request_same_hash(self):
        req1 = {
            "kind": "execution_request",
            "task_id": "OFFLINE-1",
            "milestone_id": None,
            "title": None,
            "created_at": "2026-01-19T07:15:04.918628+00:00",
            "payload": {},
            "_meta": {
                "source_ip": "127.0.0.1",
                "received_at": "2026-01-19T07:15:04.918628+00:00",
            },
        }

        # Same task/payload but different timestamps/meta should hash identically
        req2 = {
            "kind": "execution_request",
            "task_id": "OFFLINE-1",
            "milestone_id": None,
            "title": None,
            "created_at": "2099-01-01T00:00:00+00:00",
            "payload": {},
            "_meta": {
                "source_ip": "10.0.0.5",
                "received_at": "2099-01-01T00:00:00+00:00",
            },
        }

        h1 = sha256_of(canonicalize_request(req1))
        h2 = sha256_of(canonicalize_request(req2))
        self.assertEqual(h1, h2)

    def test_consumer_is_deterministic_for_same_request(self):
        req = {
            "kind": "execution_request",
            "task_id": "OFFLINE-1",
            "milestone_id": None,
            "title": None,
            "created_at": "2026-01-19T07:15:04.918628+00:00",
            "payload": {},
            "_meta": {
                "source_ip": "127.0.0.1",
                "received_at": "2026-01-19T07:15:04.918628+00:00",
            },
        }

        with tempfile.TemporaryDirectory() as td:
            public_dir = Path(td) / "public"
            _write_json(public_dir / "last_execution_request.json", req)

            r1 = consume(public_dir)
            r2 = consume(public_dir)

            c1 = _canonicalize_result_for_compare(r1)
            c2 = _canonicalize_result_for_compare(r2)

            self.assertEqual(c1, c2)

            last_written = _read_json(public_dir / "last_execution_result.json")
            self.assertEqual(_canonicalize_result_for_compare(last_written), c2)


if __name__ == "__main__":
    unittest.main()
