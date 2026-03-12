from utils.reference_build_registry import (
    get_archetype_benchmark_guidance,
    load_local_reference_build,
    suggest_reference_archetype,
)


def test_load_local_reference_build_returns_project_149_for_saas_landing():
    reference = load_local_reference_build("saas_landing")

    assert reference is not None
    assert reference["project_id"] == 149
    assert reference["source"] == "local_benchmark"
    assert "Build Products" in reference["html_code"]
    assert ".hero" in reference["css_code"]


def test_suggest_reference_archetype_matches_badass_site_prompt():
    match = suggest_reference_archetype("bbuild me a badass site")

    assert match is not None
    assert match["project_id"] == 149
    assert match["archetype"] == "saas_landing"


def test_saas_guidance_includes_pysimple_reference_notes():
    reference = load_local_reference_build("saas_landing")

    assert reference is not None
    assert reference["project_id"] == 149
    assert "legacy-pysimple-cli-saas" in reference["benchmark_guidance"]


def test_load_local_reference_build_supports_published_only_legacy_examples():
    reference = load_local_reference_build("game")

    assert reference is not None
    assert reference["project_id"] == 43
    assert "Charmander" in reference["html_code"]
    assert "--fire" in reference["css_code"]
    assert "premium-feeling transitions" in reference["benchmark_guidance"]
    assert "count-up hero stats" in reference["benchmark_guidance"]


def test_suggest_reference_archetype_matches_pokemon_prompt():
    match = suggest_reference_archetype(
        "can you build me a pokemon fan page website with charmander, bulbasaur, and squirtle characters?"
    )

    assert match is not None
    assert match["project_id"] == 43
    assert match["archetype"] == "game"


def test_suggest_reference_archetype_matches_ff7_prompt():
    match = suggest_reference_archetype(
        "Create me a Final Fantasy 7 theme fan page site with cloud, barrett, and tifa plus a map"
    )

    assert match is not None
    assert match["project_id"] == 38
    assert match["archetype"] == "game"


def test_get_archetype_benchmark_guidance_merges_multiple_game_examples():
    guidance = get_archetype_benchmark_guidance("game")

    assert "legacy-pokemon-starters-fan-page" in guidance
    assert "legacy-digimon-agumon-fan-page" in guidance
    assert "legacy-ff9-zidane-vivi-tribute" in guidance
    assert "legacy-precision-calculator-ui" in guidance
    assert "legacy-alpha-launch-wizard" in guidance
