from __future__ import annotations

from orchestrator import Orchestrator


def main():
    idea = input("Describe your product idea:\n> ").strip()
    if not idea:
        print("No input provided.")
        return

    orch = Orchestrator()
    prd_text, plan = orch.run(idea)

    print("\n==================== PRD (from PM stub) ====================\n")
    print(prd_text)

    print("\n==================== PLAN (schema output) ====================\n")
    # Pydantic v2 uses model_dump_json; v1 uses json()
    if hasattr(plan, "model_dump_json"):
        print(plan.model_dump_json(indent=2))
    else:
        print(plan.json(indent=2))


if __name__ == "__main__":
    main()
