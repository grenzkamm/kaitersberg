"""Cross-file contracts in the authored skill sources."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SKILLS = ROOT / ".claude" / "skills"


class SkillContractTest(unittest.TestCase):
    def test_batch_and_integrated_gates_are_distinct_contracts(self) -> None:
        """The build runs two different gates, so the architecture must name both.

        A single "the gate" collapses them, and the batch check then either costs
        the full suite every time or the final proof runs on a shortcut.
        """
        architecture = (SKILLS / "architecture" / "template.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("**Batch gate recipe:**", architecture)
        self.assertIn("**Integrated and CI gate:**", architecture)
        self.assertNotIn(
            "`<the exact commands, in order>` - after every batch", architecture
        )

    def test_the_three_skills_hand_off_to_skills_that_exist_here(self) -> None:
        """This framework plans and stands up; it never claims to build.

        A handoff to a skill that was moved out is the failure this repository
        produces most easily, and the one a reader cannot see is missing.
        """
        gone = ("/write-spec", "/tech-design", "/build-loop", "`/build`", "`/qa`",
                "`/review`", "`/tasks`", "`/pr`", "`/merge`", "`/fix`", "`/audit`")
        for skill in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
            for document in sorted(skill.glob("*.md")):
                text = document.read_text(encoding="utf-8")
                for name in gone:
                    self.assertNotIn(name, text, f"{document}: {name}")


if __name__ == "__main__":
    unittest.main()
