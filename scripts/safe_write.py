from __future__ import annotations
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

ALLOWED_EXTENSIONS = {
    "", ".txt", ".md", ".json",
    ".html", ".css", ".js", ".jsx", ".ts", ".tsx",
    ".py", ".java", ".c", ".cpp", ".h", ".hpp",
    ".xml", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".sh", ".bash", ".bat", ".ps1",
    ".svg", ".gitignore", ".env.example",
    # Database & query files
    ".sql", ".prisma", ".graphql", ".gql",
    # Environment & config
    ".env", ".lock", ".editorconfig",
    # Rust / Go / other common languages
    ".rs", ".go", ".rb", ".php", ".swift", ".kt",
    # Docs
    ".rst", ".mdx",
}

@dataclass(frozen=True)
class WriteRecord:
    path: str
    sha256: str
    bytes: int


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _ensure_within_dir(base: Path, target: Path) -> None:
    """
    Verify target is strictly inside base.
    Both paths must already be resolved (absolute).
    Uses is_relative_to() so the check is CWD-independent.
    """
    try:
        target.relative_to(base)
    except ValueError:
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
    allowlist_dir = allowlist_dir.resolve()
    allowlist_dir.mkdir(parents=True, exist_ok=True)

    rel = Path(relative_path)

    # Disallow absolute paths and UNC / rooted paths
    if rel.is_absolute() or str(rel).startswith(("\\\\", "/")):
        raise ValueError(f"Unsafe path (absolute): {relative_path}")

    # Anchor target to allowlist_dir — resolve from here so CWD doesn't matter
    target = (allowlist_dir / rel).resolve()

    # Enforce extension allowlist
    exts = set(allowed_extensions) if allowed_extensions is not None else ALLOWED_EXTENSIONS
    # Check suffix — but also handle multi-dot filenames like .env.example
    # by checking if the full filename ends with any allowed extension
    target_name_lower = target.name.lower()
    suffix_lower = target.suffix.lower()
    allowed = (
        suffix_lower in exts
        or any(target_name_lower.endswith(ext) for ext in exts if ext)
    )
    if not allowed:
        raise ValueError(f"Disallowed extension: {target.suffix} (allowed: {sorted(exts)})")

    # Ensure no traversal outside allowlist_dir (CWD-independent)
    _ensure_within_dir(allowlist_dir, target)

    data = content.encode("utf-8")
    digest = _sha256_bytes(data)

    # Atomic write
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(target)

    return WriteRecord(path=str(target), sha256=digest, bytes=len(data))


def enforce_iteration_scope(allowed_files: Iterable[str], outputs) -> None:
    allowed = {str(p).replace("\\", "/").strip() for p in allowed_files if p}
    if not allowed:
        return
    offending = []
    for f in outputs:
        path = f.path.replace("\\", "/").strip()
        if path not in allowed:
            offending.append(path)
    if offending:
        raise ValueError(
            "Engineer output includes files outside allowed scope: "
            + ", ".join(offending)
        )



