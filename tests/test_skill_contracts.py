"""Cross-file contracts in the authored skill sources."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
STATUS_TEMPLATE = ROOT / ".claude" / "skills" / "status" / "template.md"
SKILLS = ROOT / ".claude" / "skills"
README = ROOT / "README.md"


class SkillContractTest(unittest.TestCase):
    def test_bug_4_status_template_uses_the_board_scope_line(self) -> None:
        template = STATUS_TEMPLATE.read_text(encoding="utf-8")

        self.assertNotIn("the scope line from spec.md", template)
        self.assertIn("the scope line from features/INDEX.md", template)

    def test_batch_and_integrated_gates_are_distinct_contracts(self) -> None:
        architecture = (SKILLS / "architecture" / "template.md").read_text(
            encoding="utf-8"
        )
        tasks = (SKILLS / "tasks" / "template.md").read_text(encoding="utf-8")

        self.assertIn("**Batch gate recipe:**", architecture)
        self.assertIn("**Integrated and CI gate:**", architecture)
        self.assertNotIn(
            "`<the exact commands, in order>` - after every batch", architecture
        )
        self.assertIn("Integrated feature gate", tasks)

    def test_review_and_qa_templates_mark_one_current_snapshot(self) -> None:
        review = (SKILLS / "review" / "template.md").read_text(encoding="utf-8")
        qa = (SKILLS / "qa" / "report-template.md").read_text(encoding="utf-8")

        self.assertEqual(review.count("kaitersberg-report: review"), 1)
        self.assertEqual(qa.count("kaitersberg-report: qa"), 1)
        self.assertEqual(review.count("kaitersberg-subject-sha:"), 1)
        self.assertEqual(qa.count("kaitersberg-subject-sha:"), 1)

    def test_report_history_is_outside_the_current_snapshots(self) -> None:
        for name in ("review", "qa"):
            skill = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("evidence/report-history/", skill)
            self.assertIn("current snapshot", skill)

    def test_report_history_names_distinguish_rounds_at_the_same_sha(self) -> None:
        for name in ("review", "qa"):
            skill = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("<run-id>-r<round>", skill)
            self.assertIn("never overwrite", skill)

    def test_readme_describes_post_test_reports_and_rate_limit_event(self) -> None:
        readme = README.read_text(encoding="utf-8")
        self.assertIn("current `review.md` and `qa.md` snapshots", readme)
        self.assertIn("`rate_limited` (with Claude's `resetsAt`)", readme)

    def test_delivery_skills_scope_board_reads(self) -> None:
        expected = {
            "build": "dependency rows and the relevant parallel-safety row",
            "review": "only this feature's row",
            "qa": "only this feature's row",
            "pr": "only this feature's row",
        }
        for name, phrase in expected.items():
            skill = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn(phrase, skill)


if __name__ == "__main__":
    unittest.main()
