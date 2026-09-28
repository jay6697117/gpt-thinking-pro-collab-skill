"""Run repository checks without relying on a developer's global skill setup."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

import yaml
from package_skill import ROOT, SKILL, package_files


def read_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) != 3 or parts[0].strip():
        raise ValueError(f"Missing frontmatter: {path}")
    data = yaml.safe_load(parts[1])
    if not isinstance(data, dict) or not {"name", "description"}.issubset(data):
        raise ValueError(f"Invalid skill frontmatter: {path}")
    return data


def without_fences(text: str) -> str:
    lines = []
    marker = None
    for line in text.splitlines():
        opening = re.match(r"^\s*(`{3,}|~{3,})", line)
        if opening:
            current = opening.group(1)
            if marker is None:
                marker = current
            elif current[0] == marker[0] and len(current) >= len(marker):
                marker = None
            continue
        if marker is None:
            lines.append(line)
    if marker is not None:
        raise ValueError("Unclosed Markdown code fence")
    return "\n".join(lines)


def anchors(text: str) -> set[str]:
    return {
        re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")
        for heading in re.findall(r"^#{1,6}\s+(.+?)\s*#*$", without_fences(text), re.M)
    }


def check_documents(paths: list[Path]) -> list[str]:
    failures = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        try:
            visible = without_fences(text)
        except ValueError as exc:
            failures.append(f"{path.relative_to(ROOT)}: {exc}")
            continue
        for destination in re.findall(r"\]\(([^)]+)\)", visible):
            if re.match(r"^[a-z][a-z0-9+.-]*:", destination, re.I):
                continue
            file_part, _, fragment = unquote(destination).partition("#")
            target = (path.parent / file_part).resolve() if file_part else path
            if not target.exists():
                failures.append(f"{path.relative_to(ROOT)}: missing link {destination}")
            elif (
                fragment
                and target.is_file()
                and target.suffix == ".md"
                and fragment not in anchors(target.read_text(encoding="utf-8"))
            ):
                failures.append(
                    f"{path.relative_to(ROOT)}: missing anchor {destination}"
                )
        if re.search(r"\bTODO\b|\[TODO", text):
            failures.append(f"{path.relative_to(ROOT)}: unfinished template marker")
    return failures


def check_structure() -> list[str]:
    failures = []
    package_files()
    metadata = yaml.safe_load(
        (SKILL / "agents/openai.yaml").read_text(encoding="utf-8")
    )
    skill = read_frontmatter(SKILL / "SKILL.md")
    if skill["name"] != "gpt-thinking-pro-collab":
        failures.append("Unexpected skill name")
    if not isinstance(skill["description"], str) or not skill["description"].strip():
        failures.append("Skill description is empty")
    if metadata.get("policy", {}).get("allow_implicit_invocation") is not False:
        failures.append("Explicit invocation policy changed")
    interface = metadata.get("interface", {})
    if not 25 <= len(interface.get("short_description", "")) <= 64:
        failures.append("UI description must be 25–64 characters")
    if "$gpt-thinking-pro-collab" not in interface.get("default_prompt", ""):
        failures.append("Default prompt lacks explicit invocation")
    discovered = [path for path in (ROOT / "skills").rglob("SKILL.md")]
    if discovered != [SKILL / "SKILL.md"] or (ROOT / "SKILL.md").exists():
        failures.append("Expected one nested installable skill")
    workflow = yaml.load(
        (ROOT / ".github/workflows/check.yml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    if not {"push", "pull_request", "workflow_dispatch"}.issubset(workflow["on"]):
        failures.append("CI must cover push, pull requests, and manual verification")
    if workflow.get("permissions") != {"contents": "read"}:
        failures.append("CI should only need repository read permission")
    documents = [
        ROOT / "README.md",
        *sorted(
            path
            for path in (ROOT / "docs").rglob("*.md")
            if "history" not in path.relative_to(ROOT / "docs").parts
        ),
        SKILL / "SKILL.md",
        *sorted((SKILL / "references").glob("*.md")),
    ]
    return failures + check_documents(documents)


def main() -> int:
    try:
        failures = check_structure()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Structure check failed: {exc}", file=sys.stderr)
        return 1
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    commands = [
        [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-q"],
        [sys.executable, "-m", "ruff", "check", "--no-cache", "."],
        [sys.executable, "-m", "ruff", "format", "--check", "--no-cache", "."],
        ["git", "diff", "--check"],
    ]
    for command in commands:
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode:
            return result.returncode
    print(
        "All local checks passed: structure, links, package, tests, lint, format, diff."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
