from __future__ import annotations

import re
from typing import Any


SECTION_NAMES = {
    "chosen_subskills",
    "skill_file_reads",
    "routing_context",
    "plan",
    "execution",
    "validation",
}


def _parse_sections(output: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None

    for line in output.splitlines():
        stripped = line.strip()
        if stripped in SECTION_NAMES:
            current = stripped
            sections.setdefault(current, [])
            continue
        if current:
            sections[current].append(line)

    return {name: "\n".join(lines).strip() for name, lines in sections.items()}


def _extract_skills(block: str) -> list[str]:
    skills: list[str] = []
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if not line.startswith("-"):
            continue
        if line.startswith("- [provenance:"):
            continue

        code_match = re.search(r"`([^`]+)`", line)
        if code_match:
            skills.append(code_match.group(1))
            continue

        plain = line[1:].strip()
        if ":" in plain:
            plain = plain.split(":", 1)[0].strip()
        if plain:
            skills.append(plain)

    return skills


def _extract_file_reads(block: str) -> list[str]:
    reads: list[str] = []
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if line.startswith("- "):
            reads.append(line[2:].strip())
    return reads


def _strip_wrapping_backticks(value: str) -> str:
    if value.startswith("`") and value.endswith("`") and len(value) >= 2:
        return value[1:-1]
    return value


def contract_assert(output: str, context: dict[str, Any]) -> dict[str, Any]:
    config = (context or {}).get("config", {})
    required_sections = config.get("required_sections", ["chosen_subskills", "skill_file_reads", "plan"])
    sections = _parse_sections(output)
    missing = [name for name in required_sections if not sections.get(name)]

    if missing:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Missing required sections: {', '.join(missing)}",
        }

    return {"pass": True, "score": 1}


def expected_skill_set_assert(output: str, context: dict[str, Any]) -> dict[str, Any]:
    config = (context or {}).get("config", {})
    expected = list(config.get("expected_skills", []))
    exact_order = bool(config.get("exact_order", False))
    sections = _parse_sections(output)
    actual = _extract_skills(sections.get("chosen_subskills", ""))

    if exact_order:
        if actual[: len(expected)] != expected:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Expected chosen_subskills to start with {expected}, got {actual}",
            }
    else:
        missing = [skill for skill in expected if skill not in actual]
        if missing:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Missing expected skills: {missing}; got {actual}",
            }

    return {"pass": True, "score": 1}


def expected_any_skill_assert(output: str, context: dict[str, Any]) -> dict[str, Any]:
    config = (context or {}).get("config", {})
    expected_any = list(config.get("expected_any_skills", []))
    sections = _parse_sections(output)
    actual = _extract_skills(sections.get("chosen_subskills", ""))

    if not any(skill in actual for skill in expected_any):
        return {
            "pass": False,
            "score": 0,
            "reason": f"Expected at least one of {expected_any}, got {actual}",
        }

    return {"pass": True, "score": 1}


def no_disallowed_skills_assert(output: str, context: dict[str, Any]) -> dict[str, Any]:
    config = (context or {}).get("config", {})
    disallowed = set(config.get("disallowed_skills", []))
    sections = _parse_sections(output)
    actual = _extract_skills(sections.get("chosen_subskills", ""))
    found = [skill for skill in actual if skill in disallowed]

    if found:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Found disallowed skills in chosen_subskills: {found}",
        }

    return {"pass": True, "score": 1}


def skill_file_reads_cover_selected_assert(output: str, context: dict[str, Any]) -> dict[str, Any]:
    config = (context or {}).get("config", {})
    managed_skills = set(config.get("managed_skills", []))
    sections = _parse_sections(output)
    selected = _extract_skills(sections.get("chosen_subskills", ""))
    reads = _extract_file_reads(sections.get("skill_file_reads", ""))

    missing: list[str] = []
    for skill in selected:
        if managed_skills and skill not in managed_skills:
            continue
        target = f"/{skill}/SKILL.md"
        if not any(target in path or path.endswith(f"{skill}/SKILL.md") for path in reads):
            missing.append(skill)

    if missing:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Missing skill_file_reads coverage for selected managed skills: {missing}; reads={reads}",
        }

    return {"pass": True, "score": 1}


def skill_file_reads_only_child_skills_assert(output: str, context: dict[str, Any]) -> dict[str, Any]:
    sections = _parse_sections(output)
    reads = [_strip_wrapping_backticks(path) for path in _extract_file_reads(sections.get("skill_file_reads", ""))]

    invalid: list[str] = []
    for path in reads:
        if not path.endswith("/SKILL.md"):
            invalid.append(path)
            continue
        if "/skill-suite-orchestrator/SKILL.md" in path:
            invalid.append(path)

    if invalid:
        return {
            "pass": False,
            "score": 0,
            "reason": f"skill_file_reads must list only child SKILL.md files; found invalid entries: {invalid}",
        }

    return {"pass": True, "score": 1}


def mutually_exclusive_skills_assert(output: str, context: dict[str, Any]) -> dict[str, Any]:
    config = (context or {}).get("config", {})
    groups = list(config.get("mutually_exclusive_groups", []))
    sections = _parse_sections(output)
    actual = set(_extract_skills(sections.get("chosen_subskills", "")))

    violations: list[list[str]] = []
    for group in groups:
        present = [skill for skill in group if skill in actual]
        if len(present) > 1:
            violations.append(present)

    if violations:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Found mutually exclusive skills together: {violations}",
        }

    return {"pass": True, "score": 1}
