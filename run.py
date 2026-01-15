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
        if written:
            print("Engineer ran, but produced no structured output (files were written).")
            print("\nWritten files:")
            for p in written:
                print(f" - {p}")
        else:
            print("Engineer step was skipped (offline mode, quota exhaustion, or no supported task selected).")
    else:
        # If EngineeringResult is a pydantic model
        if hasattr(eng_result, "model_dump_json"):
            print(eng_result.model_dump_json(indent=2))
        else:
            print(eng_result)

        if written:
            print("\nWritten files:")
            for p in written:
                print(f" - {p}")


if __name__ == "__main__":
    main()
