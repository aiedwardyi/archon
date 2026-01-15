from __future__ import annotations

from orchestrator import Orchestrator


def main():
    idea = input("Describe your product idea:\n> ").strip()
    if not idea:
        print("No input provided.")
        return

    orch = Orchestrator()
    prd_text, plan, eng_result, written = orch.run(idea)

    print("\n==================== PRD (from PM stub) ====================\n")
    print(prd_text)

    print("\n==================== PLAN (schema output) ====================\n")
    # Pydantic v2 uses model_dump_json; v1 uses json()
    if hasattr(plan, "model_dump_json"):
        print(plan.model_dump_json(indent=2))
    else:
        print(plan.json(indent=2))

    print("\n==================== ENGINEER (execution output) ====================\n")
    if eng_result is None:
        print("No executable engineer task found (or unsupported task_type).")
    else:
        if hasattr(eng_result, "model_dump_json"):
            print(eng_result.model_dump_json(indent=2))
        else:
            print(eng_result.json(indent=2))

        print("\nFiles written:")
        for p in written:
            print(" -", p)


if __name__ == "__main__":
    main()
