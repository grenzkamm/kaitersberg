#!/usr/bin/env python3
"""Check the rules this repository states about its own skills.

    python3 scripts/lint-skills.py

Shellcheck and a Python linter find broken code. Nothing but this finds a skill
that hands off to a skill nobody wrote, a template that was renamed, or a rule
that lost its frontmatter - which are the failures this repository actually
produces. CLAUDE.md states each of these rules; this file is where they are
enforced instead of remembered.

Only `.claude/skills/` is checked: everything else is generated from it.
"""

import re
import sys
from pathlib import Path

SKILLS = Path(".claude/skills")
REQUIRED_KEYS = ["name", "description", "argument-hint", "user-invocable", "allowed-tools", "model"]
REQUIRED_SECTIONS = ["## Role", "## Hard rules", "## Checklist"]

# The skills are English; the documents they produce follow the briefing. A slip
# shows up as one of these, and a whole-word match keeps "die" out of "died".
GERMAN = ["der", "die", "das", "und", "nicht", "wird", "werden", "eine", "einen", "einem",
          "ist", "sind", "mit", "auf", "für", "von", "dem", "den", "beim", "durch",
          "damit", "kann", "soll", "muss", "wenn", "dann", "aber", "oder", "auch"]


def frontmatter(text):
    if not text.startswith("---\n"):
        return {}
    block = text.split("---\n", 2)[1]
    return {k.strip(): v.strip() for k, _, v in
            (line.partition(":") for line in block.splitlines() if ":" in line)}


def check(skill_dir, known):
    """Return a list of problems with one skill, each as a single line."""
    path = skill_dir / "SKILL.md"
    problems = []
    if not path.is_file():
        return [f"{skill_dir}: no SKILL.md"]
    text = path.read_text(encoding="utf-8")
    meta = frontmatter(text)

    for key in REQUIRED_KEYS:
        if key not in meta:
            problems.append(f"{path}: frontmatter is missing `{key}`")
    if meta.get("name") and meta["name"] != skill_dir.name:
        problems.append(f"{path}: frontmatter name `{meta['name']}` is not the folder "
                        f"`{skill_dir.name}` - the host resolves the skill by folder")
    for section in REQUIRED_SECTIONS:
        if section not in text:
            problems.append(f"{path}: no `{section}` section")

    # Relative links must resolve: a template renamed and not followed is a skill
    # that tells somebody to open a file that is not there.
    for target in re.findall(r"\]\((?!https?:|#)([^)]+)\)", text):
        target = target.split("#")[0].strip()
        if target and not (skill_dir / target).exists():
            problems.append(f"{path}: link to `{target}`, which does not exist")

    # Handoffs are the failure this repository produces most easily. A reference
    # stands on its own - `/build PROJ-x` - so a path segment (`<name>/spec.md`,
    # `/api/items`) and markup (`</script>`) must not be mistaken for one.
    references = re.findall(r"(?:^|[\s(\[])/([a-z][a-z-]{2,})(?=[\s.,;:!?)\]`]|$)", text, re.M)
    for name in set(references):
        if name not in known:
            problems.append(f"{path}: hands off to `/{name}`, which is not a skill here")

    hits = sorted({w for w in re.findall(r"\b[\wäöüß]+\b", text.lower()) if w in GERMAN})
    if hits:
        problems.append(f"{path}: German in an English skill: {', '.join(hits[:6])}")

    return problems


SELFTEST = """---
name: wrong-name
description: x
---
# X
## Role
Der Text ist deutsch und /nosuchskill wird verlinkt, siehe [gone.md](gone.md).
"""


def selftest(tmp):
    """One runnable check: the rules must actually fire, or this file is decoration."""
    (tmp / "sample").mkdir(parents=True)
    (tmp / "sample" / "SKILL.md").write_text(SELFTEST, encoding="utf-8")
    found = " ".join(check(tmp / "sample", {"sample"}))
    for expected in ("argument-hint", "is not the folder", "## Hard rules", "gone.md",
                     "/nosuchskill", "German"):
        assert expected in found, f"rule did not fire: {expected}\n{found}"
    print("selftest: every rule fires")


def main():
    if "--selftest" in sys.argv:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            selftest(Path(tmp))
        return 0

    if not SKILLS.is_dir():
        sys.exit(f"{SKILLS} not found - run this from the repository root")
    dirs = sorted(d for d in SKILLS.iterdir() if d.is_dir())
    known = {d.name for d in dirs}
    problems = [p for d in dirs for p in check(d, known)]

    for line in problems:
        print(line)
    print(f"{len(dirs)} skills checked, {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
