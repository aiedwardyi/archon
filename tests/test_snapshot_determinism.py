from __future__ import annotations

import json
import re
import tempfile
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


_PUBLIC_SEGMENT_RE = re.compile(r"(^|/)(public/.*)", re.IGNORECASE)


def _normalize_path_string(s: str) -> str:
    """
    Normalize machine-specific absolute paths into a stable form.

    If the path contains a 'public/' segment, keep only 'public/...'.
    Otherwise, return the string unchanged.
    """
    s2 = s.replace("\\", "/")
    m = _PUBLIC_SEGMENT_RE.search(s2)
    if m:
        return m.group(2)
    return s


def _canonicalize_paths(obj):
    """
    Recursively walk dict/list structures and normalize values for keys that look like paths.
    """
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if isinstance(v, str) and (k == "path" or k.endswith("_path") or k.endswith("Path")):
                out[k] = _normalize_path_string(v)
            else:
                out[k] = _canonicalize_paths(v)
        return out

    if isinstance(obj, list):
        return [_canonicalize_paths(x) for x in obj]

    return obj


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


class TestSnapshotDeterminism(unittest.TestCase):
    def test_execution_and_evaluation_match_golden_snapshots(self):
        repo_root = Path(__file__).resolve().parent.parent

        exec_golden_path = repo_root / "tests" / "snapshots" / "execution_result_golden.json"
        eval_golden_path = repo_root / "tests" / "snapshots" / "evaluation_result_golden.json"

        self.assertTrue(exec_golden_path.exists(), f"Missing golden snapshot: {exec_golden_path}")
        self.assertTrue(eval_golden_path.exists(), f"Missing golden snapshot: {eval_golden_path}")

        exec_golden = _read_json(exec_golden_path)
        eval_golden = _read_json(eval_golden_path)

        # This is the deterministic seed request the golden snapshot was generated from.
        # It MUST match the golden snapshot request (including created_at, which is ignored for hashing).
        seed_request = {
            "kind": "execution_request",
            "task_id": "OFFLINE-SNAPSHOT-1",
            "milestone_id": "MS-SNAPSHOT",
            "title": "Golden snapshot seed request",
            "created_at": "2099-01-01T00:00:00+00:00",
            "payload": {
                "action": "write_public_note",
                "content": "Golden snapshot seed note.\n",
                "filename": "golden-note.md",
            },
        }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            temp_public = tmp_root / "public"
            temp_public.mkdir(parents=True, exist_ok=True)

            # The consumer reads this exact filename.
            _write_json(temp_public / "last_execution_request.json", seed_request)

            latest_exec = consume(temp_public)

            latest_exec_norm = _canonicalize_paths(_strip_meta(latest_exec))
            exec_golden_norm = _canonicalize_paths(_strip_meta(exec_golden))
            self.assertEqual(latest_exec_norm, exec_golden_norm)

            # Assert the consumer wrote the execution artifact
            exec_written_path = temp_public / "last_execution_result.json"
            self.assertTrue(exec_written_path.exists(), f"Missing artifact: {exec_written_path}")
            exec_written = _read_json(exec_written_path)

            exec_written_norm = _canonicalize_paths(_strip_meta(exec_written))
            self.assertEqual(exec_written_norm, latest_exec_norm)

            # Assert evaluator artifact matches golden
            eval_written_path = temp_public / "last_evaluation_result.json"
            self.assertTrue(eval_written_path.exists(), f"Missing evaluation artifact: {eval_written_path}")
            eval_written = _read_json(eval_written_path)

            eval_written_norm = _canonicalize_paths(_strip_meta(eval_written))
            eval_golden_norm = _canonicalize_paths(_strip_meta(eval_golden))
            self.assertEqual(eval_written_norm, eval_golden_norm)


if __name__ == "__main__":
    unittest.main()