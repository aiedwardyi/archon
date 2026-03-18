"""
InsightsAgent — Post-build prompt coaching.
Compares user prompt against planner quality_target to generate specific improvement suggestions.
Phase 21: Build Insights
"""
from typing import Optional


class InsightsAgent:

    def generate_insights(
        self,
        prompt: str,
        ui_archetype: Optional[str],
        quality_target: Optional[dict],
        prompt_score: Optional[int],
        build_confidence: Optional[int],
        files_generated: int,
        images_generated: int,
    ) -> list:
        """
        Returns a list of 2-4 actionable suggestions.
        Each suggestion: {"category": str, "suggestion": str, "priority": "high"|"medium"|"low"}
        """
        suggestions = []
        prompt_lower = prompt.lower()
        word_count = len(prompt.split())

        # 1. Prompt length check
        if word_count < 10:
            suggestions.append({
                "category": "detail",
                "suggestion": "Your prompt is quite short. Try describing the specific sections, features, and content you want — for example: 'A dashboard with sales KPIs, a revenue chart, and a customer table'.",
                "priority": "high",
            })
        elif word_count < 20:
            suggestions.append({
                "category": "detail",
                "suggestion": "Adding more detail could improve results. Try specifying what content each section should contain, like specific names, numbers, or data.",
                "priority": "medium",
            })

        # 2. Visual style check
        color_keywords = ["color", "colour", "dark", "light", "theme", "palette", "blue", "red", "green", "purple", "orange", "teal", "navy", "gradient", "neon", "pastel"]
        has_color = any(kw in prompt_lower for kw in color_keywords)
        if not has_color:
            suggestions.append({
                "category": "visual",
                "suggestion": "You didn't specify a color scheme. Try adding something like 'dark theme with emerald accents' or 'clean white with blue highlights' for more polished results.",
                "priority": "medium",
            })

        # 3. Typography check
        font_keywords = ["font", "typography", "serif", "sans", "monospace", "plex", "inter", "roboto", "bold", "heading"]
        has_font = any(kw in prompt_lower for kw in font_keywords)
        if not has_font and word_count >= 10:
            suggestions.append({
                "category": "visual",
                "suggestion": "Consider specifying typography — for example 'modern sans-serif headings' or 'monospace for a developer aesthetic'. This shapes the overall feel significantly.",
                "priority": "low",
            })

        # 4. Content specificity check (from quality_target)
        if quality_target:
            must_have = quality_target.get("must_have_content", [])
            key_sections = quality_target.get("key_sections", [])

            # Check if user mentioned any key sections
            if key_sections:
                mentioned = sum(1 for sec in key_sections if any(word in prompt_lower for word in sec.lower().split()[:2]))
                if mentioned < len(key_sections) // 2:
                    example_sections = ", ".join(key_sections[:3])
                    suggestions.append({
                        "category": "content",
                        "suggestion": f"For a {ui_archetype or 'this type of'} app, try specifying key sections like: {example_sections}. The more specific you are about layout, the better the result.",
                        "priority": "high",
                    })

            # Check if user provided concrete data/names
            if must_have:
                has_specific_data = any(char.isdigit() for char in prompt) or any(
                    kw in prompt_lower for kw in ["$", "%", "€", "name", "company"]
                )
                if not has_specific_data:
                    example_content = must_have[0] if must_have else "specific names and numbers"
                    suggestions.append({
                        "category": "content",
                        "suggestion": f"Adding real data makes your app look polished. Try including specifics like '{example_content}' instead of leaving content to the AI.",
                        "priority": "medium",
                    })

        # 5. Prompt score feedback
        if prompt_score is not None and prompt_score < 50:
            suggestions.append({
                "category": "clarity",
                "suggestion": "Your prompt scored low on clarity. Try structuring it as: 'Build a [type] for [audience] with [specific features]. Use [visual style].'",
                "priority": "high",
            })

        # 6. Domain keywords check
        if ui_archetype and ui_archetype not in prompt_lower:
            archetype_hints = {
                "dashboard": "Try mentioning what data the dashboard should display (KPIs, charts, tables).",
                "ecommerce": "Specify product types, price ranges, and checkout features you want.",
                "portfolio": "Include the person's name, role, skills, and types of projects to showcase.",
                "saas_landing": "Mention the product name, key features, pricing tiers, and target audience.",
                "game": "Describe the game title, genre, characters, and what fans should see on the page.",
                "restaurant": "Include the business name, food or drink specialty, standout items, and atmosphere.",
                "blog": "Specify the blog's topic, target audience, and what kind of posts to feature.",
                "fitness": "Include gym name, workout types, trainer info, and membership options.",
            }
            hint = archetype_hints.get(ui_archetype)
            if hint:
                suggestions.append({
                    "category": "domain",
                    "suggestion": hint,
                    "priority": "medium",
                })

        # Cap at 4 suggestions, sorted by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        suggestions.sort(key=lambda s: priority_order.get(s["priority"], 2))
        return suggestions[:4]
