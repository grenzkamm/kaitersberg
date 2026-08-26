"""Cross-file contracts in the authored skill sources."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
STATUS_TEMPLATE = ROOT / ".claude" / "skills" / "status" / "template.md"


class SkillContractTest(unittest.TestCase):
    def test_bug_4_status_template_uses_the_board_scope_line(self) -> None:
        template = STATUS_TEMPLATE.read_text(encoding="utf-8")

        self.assertNotIn("the scope line from spec.md", template)
        self.assertIn("the scope line from features/INDEX.md", template)


if __name__ == "__main__":
    unittest.main()
