from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import ValidationError

from schemas.execution_schema import ExecutionRequest, ExecutionResult
from scripts.deterministic_executor import execute
from scripts.evaluate_execution_result import consume as evaluate_consume


CONSUMER_VERSION = "v3"
_REQUEST_NONDTERMINISTIC_KEYS = {"created_at", "_meta"}

# Phase 5 (metadata-only): this consumer produces engineer execution results.
_AGENT_ROLE = "engineer"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonicalize_request(req: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(req)
    for k in _REQUEST_NONDTERMINISTIC_KEYS:
        out.pop(k, None)
    return out


def sha256_of(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


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
    with path.open("a", encoding="utf-8") as f:
        f.write(canonical_json(obj) + "\n")


def _safe_request_placeholder(req_raw: Optional[Dict[str, Any]]) -> ExecutionRequest:
    """
    ExecutionResult requires a request object even on failure.
    When the input is missing/invalid, we create a placeholder that makes the failure visible.
    """
    payload: Dict[str, Any] = {"_invalid_request": True}
    if isinstance(req_raw, dict):
        payload["_raw"] = req_raw
    return ExecutionRequest(
        kind="execution_request",
        task_id="__INVALID__",
        milestone_id=None,
        title="Invalid execution request",
        created_at=None,
        payload=payload,
        _meta=None,
    )


def _build_error_result(
    *,
    req_raw: Optional[Dict[str, Any]],
    request_hash: str,
    error_type: str,
    message: str,
) -> Dict[str, Any]:
    req_obj = _safe_request_placeholder(req_raw)

    result = ExecutionResult(
        agent_role=_AGENT_ROLE,
        status="error",
        request_hash=request_hash,
        request=req_obj,
        outputs={},
        error={"message": message, "type": error_type},
        _meta={
            "produced_at": _utc_now_iso(),
            "consumer_version": CONSUMER_VERSION,
        },
    )

    # Strictly validate our own output before writing.
    ExecutionResult.model_validate(result.model_dump())
    return result.model_dump()


def build_execution_result(public_dir: Path, req_raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    STRICT BOUNDARY:
    - Validate ExecutionRequest immediately.
    - If invalid, return an error ExecutionResult artifact (do not throw).
    - If valid, execute deterministically and return a validated ExecutionResult.
    """
    request_hash = sha256_of(canonicalize_request(req_raw))

    try:
        req = ExecutionRequest.model_validate(req_raw)
    except ValidationError as ve:
        return _build_error_result(
            req_raw=req_raw,
            request_hash=request_hash,
            error_type="ExecutionRequestSchemaInvalid",
            message=str(ve),
        )

    try:
        outputs, _writes = execute(
            public_dir=public_dir,
            request_hash=request_hash,
            task_id=req.task_id,
            payload=req.payload or {},
        )

        result = ExecutionResult(
            agent_role=_AGENT_ROLE,
            status="success",
            request_hash=request_hash,
            request=req,
            outputs=outputs,
            error=None,
            _meta={
                "produced_at": _utc_now_iso(),
                "consumer_version": CONSUMER_VERSION,
            },
        )

        # Strictly validate our own output before writing.
        ExecutionResult.model_validate(result.model_dump())
        return result.model_dump()

    except Exception as e:
        result = ExecutionResult(
            agent_role=_AGENT_ROLE,
            status="error",
            request_hash=request_hash,
            request=req,
            outputs={},
            error={"message": str(e), "type": e.__class__.__name__},
            _meta={
                "produced_at": _utc_now_iso(),
                "consumer_version": CONSUMER_VERSION,
            },
        )

        # Strictly validate our own output before writing.
        ExecutionResult.model_validate(result.model_dump())
        return result.model_dump()


def consume(public_dir: Path) -> Dict[str, Any]:
    """
    STRICT BOUNDARY:
    - Never crash on missing/invalid request.
    - Always write a visible ExecutionResult artifact and append to NDJSON history.
    """
    request_path = public_dir / "last_execution_request.json"
    result_path = public_dir / "last_execution_result.json"
    log_path = public_dir / "execution_results.ndjson"

    try:
        req_raw = read_json(request_path)
    except Exception as e:
        # Missing file / invalid JSON should still produce visible artifacts
        result = _build_error_result(
            req_raw=None,
            request_hash="",
            error_type=e.__class__.__name__,
            message=str(e),
        )
    else:
        result = build_execution_result(public_dir, req_raw)

    atomic_write(result_path, json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    append_ndjson(log_path, result)

    if result.get("status") == "success":
        evaluate_consume(public_dir)

    return result


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

    print(f"Wrote: {public_dir / 'last_execution_result.json'}")
    print(f"Appended: {public_dir / 'execution_results.ndjson'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())