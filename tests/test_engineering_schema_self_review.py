from __future__ import annotations

import unittest

from schemas.engineering_schema import EngineeringResult


class EngineeringSchemaSelfReviewTests(unittest.TestCase):
    def test_engineering_result_accepts_componentized_self_review(self):
        result = EngineeringResult.model_validate(
            {
                "task_id": "TASK-123",
                "summary": "Built a componentized trading workspace.",
                "self_review": {
                    "scores": {
                        "spacing_layout": 8,
                        "typography": 7,
                        "color_depth": 8,
                        "interactivity": 9,
                        "content_authenticity": 8,
                        "polish_flow": 7,
                    },
                    "weak_dimensions": ["typography", "polish_flow"],
                    "next_pass": "Strengthen heading treatment and add more section polish.",
                },
                "change_manifest": {
                    "preserved": ["App shell", "Accent palette"],
                    "modified": ["Hero section"],
                    "added": ["Wishlist drawer"],
                    "regression_checks": ["Cart still updates totals", "Filters still update visible cards"],
                },
                "files": [
                    {
                        "path": "src/App.tsx",
                        "content": "export default function App() { return <div />; }\n",
                    }
                ],
            }
        )

        self.assertEqual(result.self_review.scores.typography, 7)
        self.assertEqual(result.self_review.weak_dimensions, ["typography", "polish_flow"])
        self.assertEqual(result.change_manifest.added, ["Wishlist drawer"])


if __name__ == "__main__":
    unittest.main()
