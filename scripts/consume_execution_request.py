from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from schemas.execution_schema import ExecutionRequest, ExecutionResult
from scripts.deterministic_executor import execute


CONSUMER_VERSION = "v2"

# Fields we treat as allowed non-determinism for semantic identity.
# These should NOT affect request_hash.
_REQUEST_NONDTERMINISTIC_KEYS = {"created_at", "_meta"}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonicalize_request(req: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove allowed non-deterministic fields so that "same semantic request"
    yields the same hash even if timestamps or transport metadata differs.
    """
    out = dict(req)
    for k in list(out.keys()):
        if k in _REQUEST_NONDTERMINISTIC_KEYS:
            out.pop(k, None)
    return out


def sha256_of(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    # Be tolerant of UTF-8 BOM (common on Windows)
    return json.loads(path.read_text(encoding="utf-8-sig"))


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8", newline="\n")
    tmp.replace(path)


def append_ndjson(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def build_execution_result(public_dir: Path, req_raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Schema-validates the incoming request and produces a schema-valid result artifact.
    Also performs deterministic task execution (allow-listed writes under public/generated).
    """
    # Validate request contract
    req = ExecutionRequest.model_validate(req_raw)

    # Deterministic semantic hash
    request_hash = sha256_of(canonicalize_request(req_raw))

    try:
        outputs, _writes = execute(
            public_dir=public_dir,
            request_hash=request_hash,
            task_id=req.task_id,
            payload=req.payload or {},
        )

        result_model = ExecutionResult(
            status="success",
            request_hash=request_hash,
            request=req,
            outputs=outputs,
            error=None,
            _meta={"produced_at": _utc_now_iso(), "consumer_version": CONSUMER_VERSION},
        )
        return result_model.model_dump()

    except Exception as e:
        # Visible failure as artifact
        result_model = ExecutionResult(
            status="error",
            request_hash=request_hash,
            request=req,
            outputs={},
            error={"message": str(e), "type": e.__class__.__name__},
            _meta={"produced_at": _utc_now_iso(), "consumer_version": CONSUMER_VERSION},
        )
        return result_model.model_dump()


def consume(public_dir: Path) -> Dict[str, Any]:
    """
    Pure file-based consumer entrypoint for tests and future backend triggers.
    Reads:
      - last_execution_request.json
    Writes:
      - last_execution_result.json (overwrite, atomic)
      - execution_results.ndjson (append)
      - public/generated/* (allow-listed deterministic outputs)
    """
    request_path = public_dir / "last_execution_request.json"
    result_path = public_dir / "last_execution_result.json"
    log_path = public_dir / "execution_results.ndjson"

    req_raw = read_json(request_path)
    result = build_execution_result(public_dir, req_raw)

    atomic_write(result_path, json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    append_ndjson(log_path, result)

    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--public",
        default="apps/offline-vite-react/public",
        help="Path to Vite public directory",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    public_dir = (repo_root / args.public).resolve()

    result_path = public_dir / "last_execution_result.json"
    log_path = public_dir / "execution_results.ndjson"

    consume(public_dir)

    print(f"Wrote: {result_path}")
    print(f"Appended: {log_path}")
    print(f"Generated dir: {public_dir / 'generated'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
