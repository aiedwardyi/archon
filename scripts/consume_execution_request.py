from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_of(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8", newline="\n")
    tmp.replace(path)


def append_ndjson(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def build_execution_result(req: Dict[str, Any]) -> Dict[str, Any]:
    if not req.get("task_id"):
        return {
            "kind": "execution_result",
            "status": "error",
            "error": "Missing task_id",
            "request": req,
        }

    return {
        "kind": "execution_result",
        "status": "success",
        "request_hash": sha256_of(req),
        "request": req,
        "outputs": {
            "note": "Stub executor: task execution not implemented yet."
        },
    }


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

    request_path = public_dir / "last_execution_request.json"
    result_path = public_dir / "last_execution_result.json"
    log_path = public_dir / "execution_results.ndjson"

    req = read_json(request_path)
    result = build_execution_result(req)

    atomic_write(result_path, json.dumps(result, indent=2) + "\n")
    append_ndjson(log_path, result)

    print(f"Wrote: {result_path}")
    print(f"Appended: {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
