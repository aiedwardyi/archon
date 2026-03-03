"""
Parse, extract, and replace archetype sections in engineer.txt, planner.txt, and design_agent.txt.
"""

import re
import shutil
from datetime import datetime
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
BACKUPS_DIR = Path(__file__).resolve().parent / "backups"

ENGINEER_FILE = PROMPTS_DIR / "engineer.txt"
PLANNER_FILE = PROMPTS_DIR / "planner.txt"
DESIGN_AGENT_FILE = PROMPTS_DIR / "design_agent.txt"

# Delimiter pattern used in engineer.txt
# Matches both "# ARCHETYPE 3: SAAS DASHBOARD" and "# ARCHETYPE: GAME / INTERACTIVE"
ARCHETYPE_HEADER_RE = re.compile(
    r"^# ═{10,}\n"
    r"^# ARCHETYPE(?:\s+\d+)?:\s*(.+?)\s*\n"
    r"^# ═{10,}$",
    re.MULTILINE,
)

# Mapping from eval config names to engineer.txt header names (numbered archetypes)
ARCHETYPE_NAME_MAP = {
    "dashboard": "SAAS DASHBOARD",
    "saas_dashboard": "SAAS DASHBOARD",
    "saas_landing": "SAAS LANDING PAGE",
    "ecommerce": "E-COMMERCE",
    "portfolio": "PORTFOLIO / AGENCY",
    "fintech": "FINTECH / TRADING",
    "restaurant": "RESTAURANT / FOOD",
    "medical": "MEDICAL / HEALTHCARE",
    "wedding": "WEDDING / EVENT",
    "news": "NEWS / MAGAZINE",
    "real_estate": "REAL ESTATE",
    "education": "EDUCATION / COURSES",
    "photography": "PHOTOGRAPHY / GALLERY",
    "music": "MUSIC / EVENTS",
    "fitness": "FITNESS / GYM",
    "travel": "TRAVEL / BOOKING",
    "legal": "LEGAL / CONSULTING",
    "nonprofit": "NON-PROFIT / CHARITY",
    "crypto": "CRYPTO / WEB3",
    "ai_product": "AI / ML PRODUCT",
    "agency": "AGENCY / STUDIO",
    "job_board": "JOB BOARD / CAREERS",
    "food_delivery": "FOOD DELIVERY / APP",
    "dev_docs": "DEVELOPER DOCS / TOOLS",
    "startup": "STARTUP / LAUNCH PAGE",
    "blog": "BLOG / PERSONAL",
    "game": "GAME / INTERACTIVE",
    "gaming": "GAME / INTERACTIVE",
}

# Shell sections in STEP 2 that don't have numbered archetype headers
# Maps config name -> shell name in the "-> SHELL:" line
SHELL_SECTION_MAP = {
    "game": "GAME / INTERACTIVE",
    "gaming": "GAME / INTERACTIVE",
}

# Pattern to find STEP 2 shell sections: "PRIMARY ACTION: ..." blocks
SHELL_SECTION_RE = re.compile(
    r'^(PRIMARY ACTION:\s*"[^"]+"\n(?:  -> .+\n)+)',
    re.MULTILINE,
)


class PromptParser:
    def __init__(self, engineer_path: Path = None, planner_path: Path = None, design_agent_path: Path = None):
        self.engineer_path = engineer_path or ENGINEER_FILE
        self.planner_path = planner_path or PLANNER_FILE
        self.design_agent_path = design_agent_path or DESIGN_AGENT_FILE

    def _read(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def _write(self, path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")

    def _is_shell_section(self, archetype_name: str) -> bool:
        """Check if this archetype is a shell section (STEP 2) rather than a numbered archetype."""
        return archetype_name.lower().strip() in SHELL_SECTION_MAP

    def _resolve_name(self, archetype_name: str) -> str:
        """Resolve a short config name to the full header name in engineer.txt."""
        key = archetype_name.lower().strip()
        if key in ARCHETYPE_NAME_MAP:
            return ARCHETYPE_NAME_MAP[key]
        # Try matching directly against header names (case-insensitive)
        return archetype_name.upper()

    def _find_shell_section_span(self, text: str, archetype_name: str) -> tuple[int, int] | None:
        """Find the span of a STEP 2 shell section (e.g., GAME / INTERACTIVE)."""
        key = archetype_name.lower().strip()
        shell_name = SHELL_SECTION_MAP.get(key)
        if not shell_name:
            return None

        for m in SHELL_SECTION_RE.finditer(text):
            if shell_name.upper() in m.group(0).upper():
                return (m.start(), m.end())
        return None

    def _find_section_span(self, text: str, archetype_name: str) -> tuple[int, int] | None:
        """Find the start and end byte offsets of an archetype section.

        Returns (start, end) where start is the beginning of the header delimiter
        and end is just before the next header delimiter (or end of archetype block).
        """
        resolved = self._resolve_name(archetype_name)
        matches = list(ARCHETYPE_HEADER_RE.finditer(text))

        for i, m in enumerate(matches):
            if m.group(1).strip().upper() == resolved.upper():
                start = m.start()
                if i + 1 < len(matches):
                    end = matches[i + 1].start()
                else:
                    # Last archetype — find the next major section or end of file
                    # Look for ANTI-PATTERNS or CSS DESIGN SEED or end
                    after = text[m.end():]
                    next_section = re.search(r"^(?:ANTI-PATTERNS|CSS DESIGN SEED|FINAL CHECKLIST)", after, re.MULTILINE)
                    if next_section:
                        end = m.end() + next_section.start()
                    else:
                        end = len(text)
                return (start, end)
        return None

    def list_archetypes(self) -> list[str]:
        """List all archetype names found in engineer.txt."""
        text = self._read(self.engineer_path)
        return [m.group(1).strip() for m in ARCHETYPE_HEADER_RE.finditer(text)]

    def _find_any_span(self, text: str, archetype_name: str) -> tuple[int, int] | None:
        """Find the span of either a numbered archetype section or a shell section."""
        # Try numbered archetype first
        span = self._find_section_span(text, archetype_name)
        if span:
            return span
        # Fall back to shell section (STEP 2)
        return self._find_shell_section_span(text, archetype_name)

    def extract_section(self, archetype_name: str) -> str:
        """Extract the full text of one archetype section from engineer.txt."""
        text = self._read(self.engineer_path)
        span = self._find_any_span(text, archetype_name)
        if span is None:
            available = self.list_archetypes()
            shell_available = list(SHELL_SECTION_MAP.values())
            raise ValueError(
                f"Archetype '{archetype_name}' not found in {self.engineer_path}. "
                f"Numbered archetypes: {available}. Shell sections: {shell_available}"
            )
        return text[span[0]:span[1]].rstrip() + "\n"

    def replace_section(self, archetype_name: str, new_text: str) -> None:
        """Replace an archetype section in-place in engineer.txt."""
        text = self._read(self.engineer_path)
        span = self._find_any_span(text, archetype_name)
        if span is None:
            raise ValueError(f"Archetype '{archetype_name}' not found in {self.engineer_path}")

        # Ensure new_text ends with a newline for clean joining
        if not new_text.endswith("\n"):
            new_text += "\n"
        # Add blank line separator before next section
        new_text += "\n"

        updated = text[:span[0]] + new_text + text[span[1]:]
        self._write(self.engineer_path, updated)

    def backup_prompt_file(self) -> Path:
        """Copy engineer.txt to eval/backups/engineer_{timestamp}.txt."""
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUPS_DIR / f"engineer_{timestamp}.txt"
        shutil.copy2(self.engineer_path, backup_path)
        return backup_path

    def backup_all_prompt_files(self) -> list[Path]:
        """Backup engineer.txt, planner.txt, and design_agent.txt."""
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        paths = []
        for name, src in [
            ("engineer", self.engineer_path),
            ("planner", self.planner_path),
            ("design_agent", self.design_agent_path),
        ]:
            if src.exists():
                dst = BACKUPS_DIR / f"{name}_{timestamp}.txt"
                shutil.copy2(src, dst)
                paths.append(dst)
        return paths

    def extract_planner_archetype_list(self) -> list[str]:
        """Extract the list of valid ui_archetype values from planner.txt."""
        text = self._read(self.planner_path)
        match = re.search(r'"ui_archetype":\s*"([^"]+)"', text)
        if match:
            # The planner has a long pipe-separated list
            return [a.strip() for a in match.group(1).split("|") if a.strip() and a.strip() != "null"]
        return []

    def get_design_agent_text(self) -> str:
        """Return the full design_agent.txt content."""
        return self._read(self.design_agent_path)

    def update_design_agent(self, new_content: str) -> None:
        """Replace design_agent.txt content."""
        self._write(self.design_agent_path, new_content)


if __name__ == "__main__":
    parser = PromptParser()
    print("Available archetypes:")
    for name in parser.list_archetypes():
        print(f"  - {name}")
    print()
    print("Extracting SAAS DASHBOARD section:")
    section = parser.extract_section("dashboard")
    print(f"  Extracted {len(section)} chars, {len(section.splitlines())} lines")
    print("  OK - parser working correctly")
