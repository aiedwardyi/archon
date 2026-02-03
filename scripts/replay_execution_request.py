from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from scripts.consume_execution_request import consume, canonicalize_request, sha256_of


def _read_ndjson(path: Path) -> Tuple[List[Dict[str, Any]], int]:
    """
    Read NDJSON robustly:
    - Returns (valid_objects, malformed_line_count)
    - Ignores malformed lines, but counts them.
    """
    if not path.exists():
        return [], 0

    valid: List[Dict[str, Any]] = []
    malformed = 0

    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                valid.append(obj)
            else:
                malformed += 1
        except Exception:
            malformed += 1

    return valid, malformed


def _compute_request_hash(req_raw: Dict[str, Any]) -> str:
    return sha256_of(canonicalize_request(req_raw))


def select_request(
    *,
    requests: List[Dict[str, Any]],
    request_hash: Optional[str],
    index: Optional[int],
) -> Dict[str, Any]:
    """
    Selection rules:
    - If request_hash is provided: pick the FIRST request whose computed hash matches.
    - Else if index is provided: pick requests[index].
    - Else: pick the LAST valid request.
    """
    if not requests:
        raise ValueError("No valid requests found to replay.")

    if request_hash:
        for r in requests:
            if _compute_request_hash(r) == request_hash:
                return r
        raise ValueError(f"request_hash not found in NDJSON: {request_hash}")

    if index is not None:
        if index < 0 or index >= len(requests):
            raise ValueError(f"index out of range: {index} (valid: 0..{len(requests)-1})")
        return requests[index]

    return requests[-1]


def atomic_write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def _read_json_if_exists(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _inject_replay_metadata(public_dir: Path, replay_meta: Dict[str, Any]) -> None:
    """
    Replay is an orchestration action, not consumer logic.
    We inject deterministic replay metadata into the *latest* on-disk artifacts so the UI can surface it.
    """
    exec_path = public_dir / "last_execution_result.json"
    eval_path = public_dir / "last_evaluation_result.json"

    exec_obj = _read_json_if_exists(exec_path)
    if isinstance(exec_obj, dict):
        exec_obj["_replay"] = replay_meta
        atomic_write_json(exec_path, exec_obj)

    eval_obj = _read_json_if_exists(eval_path)
    if isinstance(eval_obj, dict):
        eval_obj["_replay"] = replay_meta
        atomic_write_json(eval_path, eval_obj)


def replay(
    *,
    public_dir: Path,
    request_hash: Optional[str] = None,
    index: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Deterministic replay:
    - Read execution_requests.ndjson from public/
    - Select a request (hash / index / latest)
    - Overwrite last_execution_request.json
    - Run consumer, which writes:
        - last_execution_result.json (+ execution_results.ndjson)
        - last_evaluation_result.json (+ evaluation_results.ndjson) on success
    - Inject replay metadata into the latest artifacts for UI visibility
    """
    public_dir = public_dir.resolve()
    ndjson_path = public_dir / "execution_requests.ndjson"
    last_req_path = public_dir / "last_execution_request.json"

    requests, malformed = _read_ndjson(ndjson_path)
    chosen = select_request(requests=requests, request_hash=request_hash, index=index)

    atomic_write_json(last_req_path, chosen)

    result = consume(public_dir)

    replay_meta: Dict[str, Any] = {
        "selected_request_hash": _compute_request_hash(chosen),
        "malformed_ndjson_lines_ignored": malformed,
        "selected_index": index,
    }

    _inject_replay_metadata(public_dir, replay_meta)

    # Also return it to the caller (CLI output / tests)
    if isinstance(result, dict):
        result["_replay"] = replay_meta

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic replay runner for execution requests.")
    parser.add_argument(
        "--public",
        default="apps/offline-vite-react/public",
        help="Path to public directory",
    )
    parser.add_argument(
        "--request-hash",
        default=None,
        help="Replay the first request whose computed hash matches this value.",
    )
    parser.add_argument(
        "--index",
        type=int,
        default=None,
        help="Replay by 0-based index in execution_requests.ndjson (after filtering malformed lines).",
    )

    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    public_dir = (repo_root / args.public).resolve()

    result = replay(public_dir=public_dir, request_hash=args.request_hash, index=args.index)

    print("Replay complete.")
    print(f"Public dir: {public_dir}")
    print(f"Status: {result.get('status')}")
    print(f"Selected request_hash: {result.get('_replay', {}).get('selected_request_hash')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())