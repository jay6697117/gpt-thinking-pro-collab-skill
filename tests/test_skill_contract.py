from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
TEST_SOURCE_TEXT = Path(__file__).read_text(encoding="utf-8")
SKILL_TEXT = (ROOT_DIR / "SKILL.md").read_text(encoding="utf-8")
README_TEXT = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
OPENAI_YAML_TEXT = (ROOT_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")


def extract_fenced_blocks(markdown: str) -> list[str]:
    blocks: list[str] = []
    current_block: list[str] = []
    in_block = False

    for line in markdown.splitlines():
        if line.startswith("```"):
            if in_block:
                blocks.append("\n".join(current_block))
                current_block = []
            in_block = not in_block
            continue

        if in_block:
            current_block.append(line)

    if in_block:
        raise AssertionError("Unclosed fenced code block")

    return blocks


def extract_level_two_section(markdown: str, heading: str) -> str:
    lines = markdown.splitlines()
    marker = f"## {heading}"
    section_start = lines.index(marker) + 1
    section_end = next(
        (
            index
            for index in range(section_start, len(lines))
            if lines[index].startswith("## ")
        ),
        len(lines),
    )
    return "\n".join(lines[section_start:section_end])


class SkillContractTest(unittest.TestCase):
    def test_frontmatter_contains_only_supported_keys(self) -> None:
        lines = SKILL_TEXT.splitlines()
        self.assertEqual(lines[0], "---")
        frontmatter_end = lines.index("---", 1)
        keys = {
            line.split(":", 1)[0]
            for line in lines[1:frontmatter_end]
            if line and not line.startswith((" ", "\t"))
        }

        self.assertEqual(keys, {"name", "description"})
        self.assertIn("name: gpt-thinking-pro-collab", SKILL_TEXT)

    def test_model_configuration_has_a_backward_compatible_default(self) -> None:
        self.assertIn("\u552f\u4e00\u7684 `model` \u914d\u7f6e\u9879", SKILL_TEXT)
        self.assertIn(
            "\u672a\u63d0\u4f9b `model` \u65f6\u4f7f\u7528 `GPT-5.6 Pro`",
            SKILL_TEXT,
        )

    def test_supported_profiles_map_to_the_expected_reasoning_modes(self) -> None:
        expected_profile_fields = (
            ("`GPT-5.6 Pro`", "`GPT-5.6 Sol Pro`", "`Pro`"),
            ("`GPT-5.6 Thinking`", "`GPT-5.6 Sol`", "`Extra High`"),
        )

        for primary_name, official_name, reasoning_mode in expected_profile_fields:
            with self.subTest(primary_name=primary_name):
                profile_row = next(
                    line
                    for line in SKILL_TEXT.splitlines()
                    if line.startswith(f"| {primary_name}")
                )
                self.assertIn(official_name, profile_row)
                self.assertIn(reasoning_mode, profile_row)

    def test_gate_rejects_cross_model_switches_and_fallbacks(self) -> None:
        required_guards = (
            "\u4e0d\u8981\u5207\u6362\u5230\u5176\u4ed6\u63a8\u7406\u6a21\u5f0f",
            "\u4e0d\u8981\u56de\u9000\u5230\u9ed8\u8ba4\u6a21\u578b",
            "\u4e0d\u5f97\u8ba9\u5e73\u53f0\u56de\u9000\u6a21\u578b\u7ee7\u7eed\u59d4\u6258",
            "\u4e0d\u8981\u4f7f\u7528\u6700\u63a5\u8fd1\u7684\u6863\u4f4d",
        )

        for required_guard in required_guards:
            with self.subTest(required_guard=required_guard):
                self.assertIn(required_guard, SKILL_TEXT)

        self.assertNotIn("Pro \u2192 \u6781\u9ad8 \u2192 Pro", SKILL_TEXT)

    def test_invalid_or_conflicting_configuration_fails_before_browser(self) -> None:
        required_fail_fast_rules = (
            "\u540c\u4e00\u6b21\u8c03\u7528\u51fa\u73b0\u51b2\u7a81\u7684\u6a21\u578b\u503c",
            "\u503c\u7f3a\u5931\u3001\u4e3a\u7a7a\u6216\u4e0d\u5728\u652f\u6301\u5217\u8868\u4e2d",
            "\u5728\u6253\u5f00 ChatGPT \u524d\u7ec8\u6b62\u76ee\u6807\u6a21\u578b\u8c03\u7528",
        )

        for required_rule in required_fail_fast_rules:
            with self.subTest(required_rule=required_rule):
                self.assertIn(required_rule, SKILL_TEXT)

    def test_readme_documents_pro_configuration(self) -> None:
        required_documentation = (
            "## \u6a21\u578b\u914d\u7f6e",
            "model: GPT-5.6 Pro",
            "`GPT-5.6 Sol Pro`",
            "`Pro`",
            "\u4e0d\u4f1a\u5207\u6362\u5230\u53e6\u4e00\u4e2a\u6a21\u578b\u7ee7\u7eed",
        )

        for required_text in required_documentation:
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, README_TEXT)

        self.assertNotIn("GPT-5.6 Thinking", README_TEXT)
        self.assertNotIn("Extra High", README_TEXT)
        self.assertIsNone(re.search(r"GPT-5\.6 Sol(?! Pro)", README_TEXT))

        usage_section = extract_level_two_section(README_TEXT, "\u4f7f\u7528")
        model_lines = [
            line for line in usage_section.splitlines() if line.startswith("model:")
        ]
        self.assertEqual(model_lines, ["model: GPT-5.6 Pro"] * 2)

    def test_ui_metadata_matches_the_configurable_model_workflow(self) -> None:
        self.assertIn(
            'display_name: "GPT \u53ef\u914d\u7f6e\u6a21\u578b\u534f\u4f5c"',
            OPENAI_YAML_TEXT,
        )
        self.assertIn("GPT-5.6 Pro \u6216 Thinking", OPENAI_YAML_TEXT)
        self.assertIn("$gpt-pro-collab", OPENAI_YAML_TEXT)
        self.assertIn("model: GPT-5.6 Pro", OPENAI_YAML_TEXT)
        self.assertIn("allow_implicit_invocation: false", OPENAI_YAML_TEXT)

    def test_python_source_uses_ascii_only(self) -> None:
        TEST_SOURCE_TEXT.encode("ascii")

    def test_readme_usage_examples_are_localized(self) -> None:
        usage_section = extract_level_two_section(README_TEXT, "\u4f7f\u7528")
        required_localized_text = (
            "\u9700\u6c42\uff1a",
            "\u9a8c\u6536\uff1a",
            "\u4f7f\u7528 GPT-5.6 Pro \u548c delegate \u6a21\u5f0f",
        )
        stale_english_text = ("Request:", "Acceptance:", "Use GPT-5.6")

        for required_text in required_localized_text:
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, usage_section)

        for stale_text in stale_english_text:
            with self.subTest(stale_text=stale_text):
                self.assertNotIn(stale_text, usage_section)

        extract_fenced_blocks(README_TEXT)

    def test_skill_markdown_fenced_blocks_use_english_content(self) -> None:
        han_character = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")

        for block_index, block in enumerate(extract_fenced_blocks(SKILL_TEXT)):
            with self.subTest(block_index=block_index):
                self.assertIsNone(han_character.search(block))


if __name__ == "__main__":
    unittest.main()
