"""
Quick script to run a few game builds and save screenshots.
Uses Gemini for engineering + DALL-E for images (remaining OpenAI credits).
"""

import asyncio
import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))

from api_client import BuilderAPI, BuildError
from screenshotter import Screenshotter

RESULTS_DIR = Path(__file__).resolve().parent / "results" / "game_builds"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


async def run_single_build(api, screenshotter, prompt, build_name):
    """Run one build + screenshot cycle."""
    output_dir = RESULTS_DIR / build_name
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"BUILD: {build_name}")
    print(f"Prompt: {prompt[:80]}...")
    print(f"{'='*60}")

    try:
        result = api.create_and_build(
            name=build_name,
            description=prompt,
            timeout=600,
        )
        preview_url = result["preview_url"]
        print(f"Build complete: {preview_url}")

        # Screenshot
        screenshots = await screenshotter.capture_both(
            url=preview_url,
            output_dir=output_dir,
            wait_seconds=5.0,  # Extra wait for images to load
        )
        print(f"Screenshots saved: {list(screenshots.keys())}")

        # Save build info
        (output_dir / "build_info.txt").write_text(
            f"prompt: {prompt}\n"
            f"preview_url: {preview_url}\n"
            f"project_id: {result['project_id']}\n"
            f"version: {result['version']}\n"
            f"timestamp: {datetime.now().isoformat()}\n"
        )

        return {
            "name": build_name,
            "preview_url": preview_url,
            "screenshots": screenshots,
            "success": True,
        }

    except BuildError as e:
        print(f"BUILD FAILED: {e}")
        return {"name": build_name, "success": False, "error": str(e)}
    except Exception as e:
        print(f"ERROR: {e}")
        return {"name": build_name, "success": False, "error": str(e)}


async def main():
    api = BuilderAPI(base_url="http://localhost:5000")
    if not api.health_check():
        print("Flask server not running!")
        sys.exit(1)

    screenshotter = Screenshotter(viewport_width=1440, viewport_height=900)

    prompts = [
        (
            "game_ff8_v1",
            "Build a Final Fantasy VIII fan page with character profiles for Squall, Rinoa, and Zell, "
            "weapons gallery showing Gunblades and other iconic weapons, and an interactive world map "
            "of the FF8 universe. Use a dark cinematic theme with cyan/teal accents."
        ),
        (
            "game_ff8_v2",
            "Build an immersive Final Fantasy VIII tribute site. Include a dramatic hero banner, "
            "detailed character cards for Squall Leonhart, Rinoa Heartilly, and Zell Dincht with "
            "their weapons and abilities, a Gunblade weapons gallery, and a World Map section "
            "showing Balamb Garden, Deling City, and Esthar. Dark fantasy theme with glowing cyan accents."
        ),
        (
            "game_ff7_v1",
            "Build a Final Fantasy VII fan page with character profiles for Cloud Strife, Tifa Lockhart, "
            "and Aerith Gainsborough. Include a Materia system guide, iconic weapons showcase featuring "
            "the Buster Sword and Masamune, and a World of Gaia exploration section. Dark theme with "
            "green Mako energy accents. Make it cinematic and immersive."
        ),
    ]

    results = []
    for name, prompt in prompts:
        result = await run_single_build(api, screenshotter, prompt, name)
        results.append(result)
        if not result["success"]:
            print(f"\n{name} failed, continuing to next...")

    print(f"\n{'='*60}")
    print("ALL BUILDS COMPLETE")
    print(f"{'='*60}")
    for r in results:
        status = "OK" if r["success"] else f"FAILED: {r.get('error', '?')}"
        print(f"  {r['name']}: {status}")
    print(f"\nScreenshots saved to: {RESULTS_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
