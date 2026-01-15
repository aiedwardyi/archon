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
        self.cached_idea_path = self.cache_dir / "last_idea.txt"

    def _load_cached(self):
        if (
            self.cached_prd_path.exists()
            and self.cached_plan_path.exists()
            and self.cached_idea_path.exists()
        ):
            cached_idea = self.cached_idea_path.read_text(encoding="utf-8").strip()
            prd_text = self.cached_prd_path.read_text(encoding="utf-8")
            plan = load_plan_with_repair(self.cached_plan_path)
            return cached_idea, prd_text, plan
        return None

    def _save_cached(self, idea: str, prd_text: str, plan):
        self.cached_idea_path.write_text(idea, encoding="utf-8")
        self.cached_prd_path.write_text(prd_text, encoding="utf-8")
        save_plan(plan, self.cached_plan_path)

    def run(self, user_input: str, force_write: bool = False):
        """
        Returns:
          prd_text: str
          plan: Plan
          engineering_result: EngineeringResult | None
          written_paths: list[str]
        """
        user_input_clean = user_input.strip()

        # ------------------------
        # OFFLINE MODE
        # ------------------------
        if self.offline:
            cached = self._load_cached()

            if not cached:
                from utils.offline_seed import (
                    offline_prd_from_idea,
                    offline_plan_dict_for_idea,
                )
                from schemas.plan_schema import Plan

                prd_text = offline_prd_from_idea(user_input_clean)
                plan = Plan.model_validate(
                    offline_plan_dict_for_idea(user_input_clean)
                )

                self._save_cached(user_input_clean, prd_text, plan)
                cached_idea = user_input_clean
            else:
                cached_idea, prd_text, plan = cached

            if cached_idea != user_input_clean:
                print("\n⚠️ OFFLINE_MODE is using cached PRD/Plan from a different idea:")
                print(f"   Cached idea: {cached_idea}")
                print(f"   Current idea: {user_input_clean}\n")

        # ------------------------
        # ONLINE MODE
        # ------------------------
        else:
            try:
                prd_text = self.pm.run(user_input)
                plan = self.planner.run(prd_text)
                self._save_cached(user_input_clean, prd_text, plan)

            except ClientError as e:
                msg = str(e)
                if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
                    cached = self._load_cached()

                    if cached:
                        cached_idea, prd_text, plan = cached

                        # ✅ If cached idea differs, generate a fresh offline stub for the new idea
                        if cached_idea != user_input_clean:
                            print(
                                "\n⚠️ Quota exhausted. Cached idea differs — generating a fresh OFFLINE stub for the new idea.\n"
                            )
                            from utils.offline_seed import (
                                offline_prd_from_idea,
                                offline_plan_dict_for_idea,
                            )
                            from schemas.plan_schema import Plan

                            prd_text = offline_prd_from_idea(user_input_clean)
                            plan = Plan.model_validate(
                                offline_plan_dict_for_idea(user_input_clean)
                            )
                            self._save_cached(user_input_clean, prd_text, plan)

                    else:
                        print(
                            "\n⚠️ Quota exhausted and no cache available — switching to OFFLINE stub.\n"
                        )
                        from utils.offline_seed import (
                            offline_prd_from_idea,
                            offline_plan_dict_for_idea,
                        )
                        from schemas.plan_schema import Plan

                        prd_text = offline_prd_from_idea(user_input_clean)
                        plan = Plan.model_validate(
                            offline_plan_dict_for_idea(user_input_clean)
                        )
                        self._save_cached(user_input_clean, prd_text, plan)
                else:
                    raise

        # ------------------------
        # TASK SELECTION
        # ------------------------
        task = select_executable_task(plan)
        if task is None or task.task_type != "scaffold":
            return prd_text, plan, None, []

        # ------------------------
        # ENGINEER
        # ------------------------
        if self.offline:
            print("\nℹ️ OFFLINE_MODE active — skipping engineer execution.\n")
            return prd_text, plan, None, []

        try:
            engineering_result = self.engineer.run(task)
        except ClientError as e:
            msg = str(e)
            if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
                print("\n⚠️ Engineer step skipped due to Gemini quota exhaustion.")
                print("   You can resume later or rerun with OFFLINE_MODE=1.\n")
                return prd_text, plan, None, []
            raise

        written_paths = write_engineering_result(
            engineering_result,
            repo_root=self.repo_root,
            force=force_write,
        )

        return prd_text, plan, engineering_result, written_paths
