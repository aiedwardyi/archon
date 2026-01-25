from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

from scripts.safe_write import WriteRecord, safe_write_text


def execute(
    *,
    public_dir: Path,
    request_hash: str,
    task_id: str,
    payload: Dict[str, Any],
) -> Tuple[Dict[str, Any], List[WriteRecord]]:
    """
    Deterministic task execution (offline-first).
    Supported actions:
      - action: "write_public_note"
          - content: string (required)
          - filename: string (optional; deterministic fallback if missing)

    All writes are allow-listed under:
      <public_dir>/generated/
    """
    action = (payload or {}).get("action") or "write_public_note"

    writes: List[WriteRecord] = []
    outputs: Dict[str, Any] = {"action": action}

    allow_dir = public_dir / "generated"

    if action == "write_public_note":
        content = (payload or {}).get("content")
        if not isinstance(content, str) or not content.strip():
            # Deterministic failure represented as outputs (caller decides status)
            raise ValueError("payload.content must be a non-empty string for action=write_public_note")

        filename = (payload or {}).get("filename")
        if not isinstance(filename, str) or not filename.strip():
            # Deterministic fallback name derived from stable inputs
            filename = f"{task_id}-{request_hash[:12]}.md"

        rec = safe_write_text(
            allowlist_dir=allow_dir,
            relative_path=filename,
            content=content,
        )
        writes.append(rec)

        outputs["note_path"] = rec.path
        outputs["note_sha256"] = rec.sha256
        outputs["note_bytes"] = rec.bytes
        outputs["writes"] = [{"path": rec.path, "sha256": rec.sha256, "bytes": rec.bytes} for rec in writes]
        return outputs, writes

    raise ValueError(f"Unsupported action: {action}")
