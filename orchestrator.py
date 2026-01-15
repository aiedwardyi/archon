from __future__ import annotations

import os
from pathlib import Path
from google import genai
from google.genai.errors import ClientError

from agents.pm_agent import PMAgent
from agents.planner_agent import PlannerAgent
from agents.engineer_agent import EngineerAgent
from orchestrator_utils import select_executable_task, write_engineering_result
from utils.plan_cache import load_plan_with_repair, save_plan


class Orchestrator:
    def __init__(self):
        api_key = os.getenv("GENAI_API_KEY")
        if not api_key:
            raise RuntimeError("GENAI_API_KEY not found in environment variables.")

        self.client = genai.Client(api_key=api_key)

        self.pm = PMAgent(self.client)
        self.planner = PlannerAgent(self.client)
        self.engineer = EngineerAgent(self.client)

        self.repo_root = Path(__file__).parent

        # Free-tier friendly controls
        self.offline = os.getenv("OFFLINE_MODE", "0") == "1"
        self.cache_dir = self.repo_root / "cache"
        self.cache_dir.mkdir(exist_ok=True)

        self.cached_prd_path = self.cache_dir / "last_prd.txt"
        self.cached_plan_path = self.cache_dir / "last_plan.json"

    def _load_cached(self):
        if self.cached_prd_path.exists() and self.cached_plan_path.exists():
            prd_text = self.cached_prd_path.read_text(encoding="utf-8")

            # ✅ Deterministic repair + schema validation + canonical rewrite
            plan = load_plan_with_repair(self.cached_plan_path)

            return prd_text, plan
        return None

    def _save_cached(self, prd_text: str, plan):
        self.cached_prd_path.write_text(prd_text, encoding="utf-8")

        # ✅ Permanent fix: cache only canonical JSON from validated Plan
        save_plan(plan, self.cached_plan_path)

    def run(self, user_input: str, force_write: bool = False):
        """
        Returns:
          prd_text: str
          plan: Plan
          engineering_result: EngineeringResult | None
          written_paths: list[str]
        """

        # OFFLINE MODE: no API calls. Use cached PRD/Plan.
        if self.offline:
            cached = self._load_cached()
            if not cached:
                raise RuntimeError("OFFLINE_MODE=1 but no cached PRD/Plan found in cache/. Run once online first.")
            prd_text, plan = cached
        else:
            # ONLINE MODE: attempt fresh PRD+Plan; if quota hit, fall back to cache
            try:
                prd_text = self.pm.run(user_input)
                plan = self.planner.run(prd_text)
                self._save_cached(prd_text, plan)
            except ClientError as e:
                msg = str(e)
                if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
                    cached = self._load_cached()
                    if not cached:
                        raise
                    prd_text, plan = cached
                else:
                    raise

        task = select_executable_task(plan)
        if task is None or task.task_type != "scaffold":
            return prd_text, plan, None, []

        engineering_result = self.engineer.run(task)
        written_paths = write_engineering_result(engineering_result, repo_root=self.repo_root, force=force_write)

        return prd_text, plan, engineering_result, written_paths
