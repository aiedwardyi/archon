from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from schemas.evaluation_schema import EvaluationResult
from schemas.execution_schema import ExecutionResult


EVALUATOR_VERSION = "v1"

# _meta is intentionally NOT required (nondeterministic transport metadata)
_REQUIRED_EXECUTION_RESULT_KEYS = {
    "kind",
    "status",
    "request_hash",
    "request",
    "outputs",
    "error",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    # Windows editors may introduce UTF-8 BOM; utf-8-sig handles both BOM and non-BOM.
    return json.loads(path.read_text(encoding="utf-8-sig"))


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def append_ndjson(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = canonical_json(obj)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def _check_required_keys(execution_result: Dict[str, Any]) -> Tuple[bool, List[str]]:
    missing = sorted(k for k in _REQUIRED_EXECUTION_RESULT_KEYS if k not in execution_result)
    if missing:
        return False, [f"missing_required_key:{k}" for k in missing]
    return True, []


def _check_no_error(execution_result: Dict[str, Any]) -> Tuple[bool, List[str]]:
    if execution_result.get("status") != "success":
        return False, ["execution_status_not_success"]
    if execution_result.get("error") not in (None, {}):
        return False, ["execution_error_field_present"]
    return True, []


def _check_outputs_shape(execution_result: Dict[str, Any]) -> Tuple[bool, List[str]]:
    outputs = execution_result.get("outputs")
    if not isinstance(outputs, dict):
        return False, ["outputs_not_object"]

    writes = outputs.get("writes")
    if writes is None:
        return True, []

    if not isinstance(writes, list):
        return False, ["writes_not_list"]

    for idx, w in enumerate(writes):
        if not isinstance(w, dict):
            return False, [f"write_record_not_object:{idx}"]
        for key in ("path", "sha256", "bytes"):
            if key not in w:
                return False, [f"write_record_missing_key:{idx}:{key}"]

    return True, []


def _check_write_records_exist(
    public_dir: Path, execution_result: Dict[str, Any]
) -> Tuple[bool, List[str], Dict[str, Any]]:
    outputs = execution_result.get("outputs") or {}
    writes = outputs.get("writes")

    if not writes:
        return True, [], {
            "writes_present": False,
            "writes_checked": 0,
            "writes_ok": 0,
        }

    reasons: List[str] = []
    checked = 0
    ok = 0

    for w in writes:
        checked += 1
        path_str = w.get("path")
        expected_sha = w.get("sha256")
        expected_bytes = w.get("bytes")

        p = Path(path_str)
        if not p.is_absolute():
            p = (public_dir.parent.parent / p).resolve()

        if not p.exists():
            reasons.append(f"write_file_missing:{path_str}")
            continue

        data = p.read_bytes()
        if expected_sha and sha256_bytes(data) != expected_sha:
            reasons.append(f"write_sha_mismatch:{path_str}")
            continue

        if isinstance(expected_bytes, int) and len(data) != expected_bytes:
            reasons.append(f"write_bytes_mismatch:{path_str}")
            continue

        ok += 1

    checks = {
        "writes_present": True,
        "writes_checked": checked,
        "writes_ok": ok,
    }

    if reasons:
        return False, reasons, checks

    return True, [], checks


def evaluate(public_dir: Path, execution_result_raw: Dict[str, Any]) -> Dict[str, Any]:
    reasons: List[str] = []
    checks: Dict[str, Any] = {}

    try:
        ExecutionResult.model_validate(execution_result_raw)
        checks["execution_result_schema_valid"] = True
    except Exception:
        checks["execution_result_schema_valid"] = False
        reasons.append("execution_result_schema_invalid")

    ok, r = _check_required_keys(execution_result_raw)
    checks["required_keys_present"] = ok
    reasons.extend(r)

    ok, r = _check_no_error(execution_result_raw)
    checks["no_error_field"] = ok
    reasons.extend(r)

    ok, r = _check_outputs_shape(execution_result_raw)
    checks["outputs_shape_valid"] = ok
    reasons.extend(r)

    ok, r, write_checks = _check_write_records_exist(public_dir, execution_result_raw)
    checks["write_records_valid"] = ok
    checks.update(write_checks)
    reasons.extend(r)

    status = "pass" if not reasons else "fail"

    result = EvaluationResult(
        status=status,
        request_hash=str(execution_result_raw.get("request_hash") or ""),
        reasons=reasons,
        checks=checks,
        _meta={
            "produced_at": _utc_now_iso(),
            "evaluator_version": EVALUATOR_VERSION,
        },
    )
    return result.model_dump()


def consume(public_dir: Path) -> Dict[str, Any]:
    execution_result_path = public_dir / "last_execution_result.json"
    eval_result_path = public_dir / "last_evaluation_result.json"
    eval_log_path = public_dir / "evaluation_results.ndjson"

    execution_result = read_json(execution_result_path)
    evaluation_result = evaluate(public_dir, execution_result)

    atomic_write(
        eval_result_path,
        json.dumps(evaluation_result, indent=2, ensure_ascii=False) + "\n",
    )
    append_ndjson(eval_log_path, evaluation_result)

    return evaluation_result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--public",
        default="apps/offline-vite-react/public",
        help="Path to public directory",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    public_dir = (repo_root / args.public).resolve()

    consume(public_dir)

    print(f"Wrote: {public_dir / 'last_evaluation_result.json'}")
    print(f"Appended: {public_dir / 'evaluation_results.ndjson'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())