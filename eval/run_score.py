"""Quick script to score a screenshot N times and average."""
import sys, json, logging, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)

from google import genai
from eval_scorer import DesignScorer
from scoring_rubric import compute_weighted_total, DIMENSIONS

# Load API key
env_path = Path(__file__).parent.parent / "backend" / ".env"
api_key = None
for line in env_path.read_text().splitlines():
    if line.startswith("GENAI_API_KEY="):
        api_key = line.split("=", 1)[1].strip()
        break

if not api_key:
    print("ERROR: No GENAI_API_KEY found in backend/.env")
    sys.exit(1)

client = genai.Client(api_key=api_key)

MODELS = ["gemini-2.5-flash", "gemini-2.0-flash"]

screenshot = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "results/game/screenshot.png"
archetype = sys.argv[2] if len(sys.argv) > 2 else "game"
num_runs = int(sys.argv[3]) if len(sys.argv) > 3 else 3
output_path = sys.argv[4] if len(sys.argv) > 4 else None

print(f"Scoring {screenshot} as '{archetype}' ({num_runs} runs)...")

def score_with_fallback(screenshot, archetype):
    for model in MODELS:
        scorer = DesignScorer(genai_client=client, model=model)
        for attempt in range(3):
            try:
                result = scorer.score(screenshot, archetype)
                print(f"  [model={model}] Weighted total: {result.weighted_total}")
                return result, model
            except Exception as e:
                if "503" in str(e) or "UNAVAILABLE" in str(e):
                    wait = 10 * (attempt + 1)
                    print(f"  {model} 503 — waiting {wait}s (attempt {attempt+1}/3)")
                    time.sleep(wait)
                else:
                    print(f"  {model} error: {e}")
                    break
    raise RuntimeError("All models failed")

all_results = []
model_used = None
for i in range(num_runs):
    print(f"\n--- Run {i+1}/{num_runs} ---")
    result, model_used = score_with_fallback(screenshot, archetype)
    print(f"  Scores: {result.scores}")
    all_results.append(result)
    if i < num_runs - 1:
        time.sleep(3)

# Average scores
avg_scores = {}
for dim in DIMENSIONS:
    vals = [r.scores.get(dim.name, 0) for r in all_results]
    avg_scores[dim.name] = round(sum(vals) / len(vals), 1)

avg_total = compute_weighted_total(avg_scores)

# Collect all unique issues/strengths/improvements
all_issues = list(set(i for r in all_results for i in r.issues))[:5]
all_strengths = list(set(s for r in all_results for s in r.strengths))[:5]
all_improvements = list(set(s for r in all_results for s in r.specific_improvements))[:5]

summary = {
    "archetype": archetype,
    "model_used": model_used,
    "screenshot": str(screenshot),
    "num_runs": num_runs,
    "individual_totals": [r.weighted_total for r in all_results],
    "averaged_scores": avg_scores,
    "averaged_total": avg_total,
    "issues": all_issues,
    "strengths": all_strengths,
    "specific_improvements": all_improvements,
}

print(f"\n{'='*50}")
print(f"AVERAGED SCORE: {avg_total}/100")
print(f"Individual runs: {[r.weighted_total for r in all_results]}")
print(f"Per-dimension averages: {json.dumps(avg_scores, indent=2)}")

if output_path:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2))
    print(f"\nSaved to {out}")
