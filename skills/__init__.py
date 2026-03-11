"""
Skill discovery with progressive disclosure (Anthropic pattern).

Level 1 (metadata): YAML frontmatter from SKILL.md - always loaded at startup.
Level 2 (instructions): Body of SKILL.md - LLM reads via bash (cat).
Level 3 (resources): Additional files (scripts, docs) - LLM reads/runs via bash.
"""

import os
import re
from pathlib import Path

SKILLS_DIR = Path(__file__).parent


def _parse_frontmatter(text: str) -> dict:
    """Parse YAML frontmatter from a SKILL.md file."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return {}

    metadata = {}
    for line in match.group(1).strip().splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()

    return metadata


def load_skill_metadata(skill_dir: Path) -> dict | None:
    """Level 1: Load only the YAML frontmatter (name + description)."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return None

    text = skill_md.read_text(encoding="utf-8")
    metadata = _parse_frontmatter(text)

    if not metadata.get("name") or not metadata.get("description"):
        return None

    metadata["path"] = str(skill_dir)
    return metadata


def discover_all_skills() -> dict[str, dict]:
    """Discover all skills and load their metadata (Level 1 only)."""
    skills = {}
    for entry in SKILLS_DIR.iterdir():
        if entry.is_dir() and (entry / "SKILL.md").exists():
            metadata = load_skill_metadata(entry)
            if metadata:
                skills[metadata["name"]] = metadata
    return skills


def build_metadata_prompt(skills: dict[str, dict]) -> str:
    """Build the system prompt section with skill metadata (Level 1).

    This is lightweight and always included in the system prompt so the LLM
    knows what skills exist and when to use them.
    """
    lines = ["Available skills:"]
    for name, meta in skills.items():
        lines.append(f"- **{name}**: {meta['description']}")
    return "\n".join(lines)
