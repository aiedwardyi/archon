from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


ALLOWED_EXTENSIONS = {".txt", ".md", ".json"}


@dataclass(frozen=True)
class WriteRecord:
    path: str
    sha256: str
    bytes: int


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _ensure_within_dir(base: Path, target: Path) -> None:
    base_resolved = base.resolve()
    target_resolved = target.resolve()
    if base_resolved not in target_resolved.parents and base_resolved != target_resolved:
        raise ValueError(f"Unsafe path (escapes allowlist dir): {target}")


def safe_write_text(
    *,
    allowlist_dir: Path,
    relative_path: str,
    content: str,
    allowed_extensions: Optional[Iterable[str]] = None,
) -> WriteRecord:
    """
    Deterministic, allow-listed file write.
    - Writes ONLY under allowlist_dir
    - Rejects path traversal / escaping
    - Restricts file extensions
    - Atomic write
    """
    allowlist_dir.mkdir(parents=True, exist_ok=True)

    rel = Path(relative_path)

    # Disallow absolute paths and drive-rooted paths
    if rel.is_absolute() or str(rel).startswith(("\\\\", "/")):
        raise ValueError(f"Unsafe path (absolute): {relative_path}")

    # Build final target
    target = (allowlist_dir / rel)

    # Enforce extension allowlist
    exts = set(allowed_extensions) if allowed_extensions is not None else ALLOWED_EXTENSIONS
    if target.suffix.lower() not in exts:
        raise ValueError(f"Disallowed extension: {target.suffix} (allowed: {sorted(exts)})")

    # Ensure no traversal outside allowlist_dir
    _ensure_within_dir(allowlist_dir, target)

    data = content.encode("utf-8")
    digest = _sha256_bytes(data)

    # Atomic write
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(target)

    return WriteRecord(path=str(target), sha256=digest, bytes=len(data))
