from __future__ import annotations

import json
from pathlib import Path

from schemas.plan_schema import Plan
from utils.json_repair import repair_json_newlines_in_strings


DEFAULT_PLAN_CACHE = Path("cache/last_plan.json")


def load_plan_with_repair(path: Path = DEFAULT_PLAN_CACHE) -> Plan:
    raw = path.read_text(encoding="utf-8")

    # Fast path: valid JSON already
    try:
        return Plan.model_validate_json(raw)
    except Exception:
        pass

    # Repair legacy pasted JSON
    repaired = repair_json_newlines_in_strings(raw)

    # Must be valid JSON after repair
    data = json.loads(repaired)

    plan = Plan.model_validate(data)

    # Canonicalize (permanent fix)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return plan


def save_plan(plan: Plan, path: Path = DEFAULT_PLAN_CACHE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(plan.model_dump(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
