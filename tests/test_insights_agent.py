from agents.insights_agent import InsightsAgent


def test_restaurant_archetype_hint_stays_generic_for_food_and_drink_projects():
    agent = InsightsAgent()

    insights = agent.generate_insights(
        prompt="Build a simple landing page for a local bakery with a hero, featured pastries, testimonials, and a contact section.",
        ui_archetype="restaurant",
        quality_target=None,
        prompt_score=90,
        build_confidence=80,
        files_generated=1,
        images_generated=5,
    )

    suggestions = [item["suggestion"] for item in insights]
    assert any("business name" in suggestion for suggestion in suggestions)
    assert all("cuisine type" not in suggestion for suggestion in suggestions)
