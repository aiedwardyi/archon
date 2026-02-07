import sys
sys.path.insert(0, '.')

from agents.pm_agent import PMAgent
import json

requirements = """
I want to build a simple todo list app where users can:
- Add tasks with titles and descriptions
- Mark tasks as complete
- Delete tasks
- Filter by complete/incomplete

It should work on web and mobile.
"""

agent = PMAgent()
prd = agent.generate_prd(requirements)

with open('artifacts/last_prd.json', 'w', encoding='utf-8') as f:
    json.dump(prd.model_dump(), f, indent=2, ensure_ascii=False)

print("✅ PRD generated!")
print(f"Project: {prd.prd.document_title}")
