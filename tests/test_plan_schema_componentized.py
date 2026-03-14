from __future__ import annotations

import unittest

from schemas.plan_schema import QualityTarget, Task


class PlanSchemaComponentizedTests(unittest.TestCase):
    def test_componentized_scaffold_fields_validate(self):
        task = Task(
            id="FE-1",
            description="Build the complete Studio Console as a componentized React + TypeScript app",
            depends_on=[],
            outputs=["Working React app scaffold"],
            execution_hint="engineer",
            task_type="scaffold",
            scaffold_mode="componentized_app",
            output_files=["package.json", "index.html", "src/main.tsx", "src/App.tsx"],
            ui_archetype="dashboard",
            render_path="C",
            quality_target=QualityTarget(
                visual_style="dark operator console with sharp typography",
                key_sections=["workspace", "sidebar", "preview"],
                must_have_content=["real project list", "live preview panel"],
                interactivity=["sidebar navigation", "tab switching"],
                avoid=["marketing hero"],
            ),
        )

        self.assertEqual(task.scaffold_mode, "componentized_app")
        self.assertEqual(task.render_path, "C")
        self.assertEqual(task.quality_target.interactivity, ["sidebar navigation", "tab switching"])


if __name__ == "__main__":
    unittest.main()
