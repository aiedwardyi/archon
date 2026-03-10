from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from models import ImageAsset, Project, get_session
except ImportError:
    from backend.models import ImageAsset, Project, get_session

try:
    from PIL import Image
except Exception:
    Image = None


CATEGORY_RULES = [
    ("hero_background", ("hero",)),
    ("product_shot", ("product",)),
    ("character_portrait", ("character", "portrait")),
    ("lifestyle", ("lifestyle",)),
    ("collection", ("collection", "showcase")),
    ("icon", ("icon", "logo")),
    ("pattern", ("pattern", "texture")),
    ("abstract", ("abstract", "gradient")),
]

PROMPT_CATEGORY_RULES = [
    ("hero_background", ("hero", "background", "banner")),
    ("product_shot", ("product", "shoe", "device", "bottle", "packaging", "studio shot")),
    ("character_portrait", ("character", "portrait", "person", "avatar", "face")),
    ("lifestyle", ("lifestyle", "in use", "walking", "outdoor", "scene")),
    ("collection", ("collection", "showcase", "gallery", "assortment")),
    ("icon", ("icon", "logo", "mark", "symbol")),
    ("pattern", ("pattern", "texture", "surface", "fabric")),
    ("abstract", ("abstract", "gradient", "shape", "atmospheric")),
]


def _read_json_file(path: Path) -> dict[str, Any] | None:
    try:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        print(f"Image catalog: failed to read {path}: {exc}")
        return None


def _extract_dimensions(path: Path) -> tuple[int | None, int | None]:
    if Image is None:
        return None, None
    try:
        with Image.open(path) as img:
            return img.width, img.height
    except Exception:
        return None, None


def _first_category_match(text: str, rules: list[tuple[str, tuple[str, ...]]]) -> str | None:
    normalized = text.lower()
    for category, keywords in rules:
        if any(keyword in normalized for keyword in keywords):
            return category
    return None


def categorize_asset(key: str | None, prompt: str | None = None) -> str:
    key_text = str(key or "").strip().lower()
    category = _first_category_match(key_text, CATEGORY_RULES)
    if category:
        return category
    prompt_text = str(prompt or "").strip().lower()
    category = _first_category_match(prompt_text, PROMPT_CATEGORY_RULES)
    return category or "other"


def _parse_project_and_version(manifest_path: Path) -> tuple[int | None, int | None]:
    try:
        project_id = int(manifest_path.parent.parent.name)
        version_name = manifest_path.parent.name
        if version_name.startswith("v"):
            return project_id, int(version_name[1:])
    except Exception:
        pass
    return None, None


def _coerce_created_at(path: Path) -> datetime:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime)
    except Exception:
        return datetime.utcnow()


def _normalize_local_path(local_path: str | None) -> Path | None:
    if not local_path:
        return None
    path = Path(local_path)
    if not path.is_absolute():
        path = (REPO_ROOT / path).resolve()
    return path


def catalog_design_assets(
    project_id: int,
    version: int,
    design_assets: Iterable[dict[str, Any]],
    archetype: str | None = None,
) -> int:
    session = get_session()
    inserted = 0
    try:
        for asset in design_assets:
            local_path = _normalize_local_path(asset.get("local_path"))
            if not local_path or not local_path.exists() or not local_path.is_file():
                continue
            local_path_str = str(local_path.resolve())
            existing = session.query(ImageAsset).filter(ImageAsset.local_path == local_path_str).first()
            if existing:
                continue
            width, height = _extract_dimensions(local_path)
            session.add(ImageAsset(
                filename=local_path.name,
                key=str(asset.get("key") or local_path.stem),
                category=categorize_asset(asset.get("key"), asset.get("prompt")),
                archetype=archetype,
                source_project_id=project_id,
                source_version=version,
                local_path=local_path_str,
                width=width,
                height=height,
                prompt=asset.get("prompt"),
                created_at=_coerce_created_at(local_path),
            ))
            inserted += 1
        if inserted:
            session.commit()
        else:
            session.rollback()
        return inserted
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def ingest_image_library() -> tuple[int, int, int]:
    manifests = sorted(REPO_ROOT.glob("generated/*/v*/last_design_assets.json"))
    session = get_session()
    inserted = 0
    categories = Counter()
    projects = set()
    try:
        archetype_by_project = {
            project_id: archetype
            for project_id, archetype in session.query(Project.id, Project.locked_ui_archetype).all()
        }
    finally:
        session.close()

    for manifest_path in manifests:
        project_id, version = _parse_project_and_version(manifest_path)
        if project_id is None or version is None:
            continue
        data = _read_json_file(manifest_path) or {}
        assets = data.get("assets", [])
        valid_assets = []
        for asset in assets:
            local_path = _normalize_local_path(asset.get("local_path"))
            if not local_path or not local_path.exists() or not local_path.is_file():
                continue
            valid_assets.append(asset)
        if not valid_assets:
            continue
        before_count = inserted
        inserted += catalog_design_assets(
            project_id=project_id,
            version=version,
            design_assets=valid_assets,
            archetype=archetype_by_project.get(project_id),
        )
        if inserted > before_count:
            projects.add(project_id)
            for asset in valid_assets:
                categories[categorize_asset(asset.get("key"), asset.get("prompt"))] += 1

    return inserted, len(categories), len(projects)


def infer_category_from_reference(reference: str) -> str:
    stem = Path(reference).stem
    normalized = re.sub(r"[-\s]+", "_", stem)
    return categorize_asset(normalized)
