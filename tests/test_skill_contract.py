from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/gpt-thinking-pro-collab"
sys.path.insert(0, str(ROOT / "scripts"))
from check import anchors, check_structure, read_frontmatter, without_fences
from check_scenario_results import compare_results


class SkillContractTest(unittest.TestCase):
    def test_packaged_skill_and_documentation_are_complete(self) -> None:
        self.assertEqual(check_structure(), [])

    def test_identity_and_explicit_invocation_are_preserved(self) -> None:
        frontmatter = read_frontmatter(SKILL / "SKILL.md")
        self.assertEqual(frontmatter["name"], "gpt-thinking-pro-collab")
        metadata = yaml.safe_load(
            (SKILL / "agents/openai.yaml").read_text(encoding="utf-8")
        )
        self.assertIs(metadata["policy"]["allow_implicit_invocation"], False)
        prompt = metadata["interface"]["default_prompt"]
        self.assertIn("$gpt-thinking-pro-collab", prompt)
        self.assertIn("模型: GPT-6 Astra Pro", prompt)
        self.assertIn("模式: consult", prompt)

    def test_model_profile_has_exactly_the_original_closed_allowlist(self) -> None:
        text = (SKILL / "references/configuration.md").read_text(encoding="utf-8")
        rows = [line for line in text.splitlines() if line.startswith("| `")]
        self.assertEqual(len(rows), 1)
        fields = [
            re.findall(r"`([^`]+)`", part) for part in rows[0].strip("|").split("|")
        ]
        self.assertEqual(
            fields,
            [
                ["GPT-6 Astra Pro", "GPT-6 Pro", "6 Pro"],
                ["GPT-6 Astra Pro"],
                ["GPT-6 Astra"],
                ["Pro"],
                ["GPT-6 Astra Pro", "GPT-6 Pro", "6 Pro"],
            ],
        )

    def test_copyable_examples_use_supported_model_and_mode_values(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        models = re.findall(r"^(?:模型|model)[:：]\s*(.*)$", text, re.M)
        modes = re.findall(r"^(?:模式|mode)[:：]\s*(.*)$", text, re.M)
        self.assertTrue(models)
        self.assertTrue(modes)
        self.assertTrue(set(models) <= {"GPT-6 Astra Pro", "GPT-6 Pro", "6 Pro"})
        self.assertTrue(set(modes) <= {"consult", "delegate"})

    def test_permission_and_conditional_routes_are_present(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(
            {"先确定任务合同", "权限边界", "对外调用前的必经检查", "传递等待与接入"}
            <= anchors(text)
        )
        targets = set(re.findall(r"\]\((references/[^)]+)\)", text))
        self.assertEqual(
            targets,
            {
                "references/configuration.md",
                "references/browser-workflow.md",
                "references/context.md",
                "references/review-delivery.md",
                "references/reporting.md",
            },
        )
        self.assertNotIn("browser:control-in-app-browser", text)

    def test_example_session_starts_without_implying_a_passed_gate(self) -> None:
        session = json.loads(
            (SKILL / "assets/session.example.json").read_text(encoding="utf-8")
        )
        self.assertEqual(session["state"], "unstarted")
        self.assertIsNone(session["gateEvidence"])
        self.assertIsNone(session["submissionEvidence"])
        self.assertFalse(session["applied"])
        self.assertEqual(
            session["model"]["acceptedUiLabels"],
            ["GPT-6 Astra Pro", "GPT-6 Pro", "6 Pro"],
        )

    def test_documented_script_commands_exist_in_package(self) -> None:
        referenced = set()
        for path in (SKILL / "references").glob("*.md"):
            referenced.update(
                re.findall(
                    r'\$SKILL_DIR/(scripts/[^"\s]+)', path.read_text(encoding="utf-8")
                )
            )
        self.assertEqual(
            referenced, {"scripts/context_bundle.py", "scripts/verify_delivery.py"}
        )
        for path in referenced:
            self.assertTrue((SKILL / path).is_file())

    def test_unclosed_markdown_fence_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            without_fences("标题\n```text\n未结束")
        self.assertEqual(without_fences("段落\n```text\n示例\n```\n结尾"), "段落\n结尾")

    def test_scenario_comparator_rejects_wrong_missing_and_duplicate_decisions(
        self,
    ) -> None:
        expected = {"C01": "local_readonly", "C02": "wait"}
        self.assertEqual(
            compare_results(
                [
                    {"id": "C01", "decision": "local_readonly", "reason": "只读范围"},
                    {"id": "C02", "decision": "wait", "reason": "当前正在生成"},
                ],
                expected,
            ),
            [],
        )
        invalid = [
            {"id": "C01", "decision": "local_implementation", "reason": "误判"},
            {"id": "C01", "decision": "local_readonly", "reason": ""},
        ]
        failures = compare_results(invalid, expected)
        self.assertTrue(any("Missing case" in item for item in failures))
        self.assertTrue(any("Duplicate" in item for item in failures))
        self.assertTrue(
            any("received local_implementation" in item for item in failures)
        )

    def test_scenario_inputs_and_oracle_have_matching_ids(self) -> None:
        cases = json.loads(
            (ROOT / "tests/scenarios/cases.json").read_text(encoding="utf-8")
        )
        expected = json.loads(
            (ROOT / "tests/scenarios/expected.json").read_text(encoding="utf-8")
        )
        actions = json.loads(
            (ROOT / "tests/scenarios/actions.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(cases), len({case["id"] for case in cases}))
        self.assertEqual({case["id"] for case in cases}, set(expected))
        self.assertTrue(set(expected.values()) <= set(actions))


if __name__ == "__main__":
    unittest.main()
