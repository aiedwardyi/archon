from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from models import ImageAsset, get_session
except ImportError:
    from backend.models import ImageAsset, get_session
from utils.image_asset_catalog import infer_category_from_reference


IMG_SRC_RE = re.compile(r"<img\b[^>]*\bsrc=['\"]([^'\"]+)['\"]", re.IGNORECASE)
URL_RE = re.compile(r"background-image\s*:\s*url\(([^)]+)\)|url\(([^)]+)\)", re.IGNORECASE)
API_ASSET_RE = re.compile(r"^/api/assets/\d+/\d+/(?P<filename>.+)$")
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".avif"}

IGNORED_PREFIXES = ("data:", "http://", "https://", "//")


def _get_version_dir(project_id: int, version: int) -> Path:
    return REPO_ROOT / "generated" / str(project_id) / f"v{version}"


def _extract_references(html_text: str) -> set[str]:
    refs = set()
    for match in IMG_SRC_RE.findall(html_text):
        refs.add(match.strip())
    for full, fallback in URL_RE.findall(html_text):
        candidate = full or fallback
        refs.add(candidate.strip().strip("'\""))
    return refs


def _resolve_expected_filename(reference: str) -> str | None:
    if not reference or reference.startswith(IGNORED_PREFIXES):
        return None
    reference = reference.split("?", 1)[0].split("#", 1)[0].strip()
    api_match = API_ASSET_RE.match(reference)
    if api_match:
        filename = Path(api_match.group("filename")).name
        return filename if Path(filename).suffix.lower() in IMAGE_SUFFIXES else None
    if reference.startswith("/"):
        filename = Path(reference).name
        return filename if Path(filename).suffix.lower() in IMAGE_SUFFIXES else None
    filename = Path(reference).name
    return filename if Path(filename).suffix.lower() in IMAGE_SUFFIXES else None


def _expected_target(version_dir: Path, filename: str) -> tuple[Path, list[Path]]:
    target = version_dir / "assets" / filename
    candidates = [
        target,
        version_dir / "code" / "src" / "assets" / filename,
    ]
    return target, candidates


def _pick_reuse_candidate(category: str, archetype: str | None) -> ImageAsset | None:
    session = get_session()
    try:
        query = session.query(ImageAsset)
        candidate = None
        if archetype:
            candidate = (
                query.filter(ImageAsset.archetype == archetype, ImageAsset.category == category)
                .order_by(ImageAsset.created_at.desc(), ImageAsset.id.desc())
                .first()
            )
        if candidate is None:
            candidate = (
                query.filter(ImageAsset.category == category)
                .order_by(ImageAsset.created_at.desc(), ImageAsset.id.desc())
                .first()
            )
        if candidate is None and archetype:
            candidate = (
                query.filter(ImageAsset.archetype == archetype)
                .order_by(ImageAsset.created_at.desc(), ImageAsset.id.desc())
                .first()
            )
        return candidate
    finally:
        session.close()


def fill_missing_assets(project_id: int, version: int, archetype: str | None) -> int:
    version_dir = _get_version_dir(project_id, version)
    html_path = version_dir / "code" / "src" / "index.html"
    if not html_path.exists():
        return 0

    html_text = html_path.read_text(encoding="utf-8", errors="ignore")
    references = _extract_references(html_text)
    filled = 0

    for reference in sorted(references):
        filename = _resolve_expected_filename(reference)
        if not filename:
            continue
        target, candidates = _expected_target(version_dir, filename)
        if any(candidate.exists() and candidate.is_file() for candidate in candidates):
            continue
        category = infer_category_from_reference(filename)
        match = _pick_reuse_candidate(category, archetype)
        if not match:
            continue
        source_path = Path(match.local_path)
        if not source_path.exists() or not source_path.is_file():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target)
        filled += 1
        print(f"Filled missing image: {filename} <- reused from project {match.source_project_id}")

    return filled
