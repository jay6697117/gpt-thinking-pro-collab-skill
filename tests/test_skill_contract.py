from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
TEST_SOURCE_TEXT = Path(__file__).read_text(encoding="utf-8")
SKILL_TEXT = (ROOT_DIR / "SKILL.md").read_text(encoding="utf-8")
README_TEXT = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
OPENAI_YAML_TEXT = (ROOT_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")
STALE_INVOCATION = "$gpt-" + "pro-collab"


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


def extract_profile_rows(
    markdown: str,
) -> dict[str, tuple[tuple[str, ...], ...]]:
    profiles: dict[str, tuple[tuple[str, ...], ...]] = {}
    for line in markdown.splitlines():
        if not line.startswith("| `GPT-"):
            continue
        fields = tuple(
            tuple(re.findall(r"`([^`]+)`", cell)) for cell in line.strip("|").split("|")
        )
        canonical_name = fields[0][0]
        if canonical_name in profiles:
            raise AssertionError(f"Duplicate model profile: {canonical_name}")
        profiles[canonical_name] = fields
    return profiles


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

    def test_model_configuration_defaults_to_astra_pro(self) -> None:
        self.assertIn(
            "`\u6a21\u578b` \u662f\u9996\u9009\u4e2d\u6587\u914d\u7f6e\u952e",
            SKILL_TEXT,
        )
        self.assertIn("`model` \u662f\u5411\u540e\u517c\u5bb9\u522b\u540d", SKILL_TEXT)
        self.assertIn(
            "\u7528\u6237\u672a\u901a\u8fc7\u914d\u7f6e\u952e\u6216"
            "\u81ea\u7136\u8bed\u8a00\u6307\u5b9a\u6a21\u578b\u65f6\uff0c"
            "\u4f7f\u7528 `GPT-6 Astra Pro`",
            SKILL_TEXT,
        )

    def test_localized_configuration_keys_preserve_english_aliases(self) -> None:
        required_alias_rules = (
            "`\u6a21\u5f0f` \u662f\u9996\u9009\u4e2d\u6587\u914d\u7f6e\u952e",
            "`mode` \u662f\u5411\u540e\u517c\u5bb9\u522b\u540d",
            "`\u6a21\u5f0f: <value>`\u3001`mode: <value>`",
            "`\u6a21\u578b: <value>` \u6216 `model: <value>`",
            (
                "\u5f52\u4e00\u5316\u540e `targetModel` \u76f8\u540c\u5219"
                "\u6309\u4e00\u4e2a\u914d\u7f6e\u5904\u7406"
            ),
            "\u4e0d\u540c\u5219\u89c6\u4e3a\u51b2\u7a81\u914d\u7f6e",
            "\u51fa\u73b0\u591a\u4e2a\u4e0d\u540c\u6a21\u5f0f\u503c\u65f6",
        )

        for required_rule in required_alias_rules:
            with self.subTest(required_rule=required_rule):
                self.assertIn(required_rule, SKILL_TEXT)

    def test_supported_profiles_map_to_the_expected_reasoning_modes(self) -> None:
        expected_profiles = {
            "GPT-6 Astra Pro": (
                ("GPT-6 Astra Pro", "GPT-6 Pro", "6-pro"),
                ("GPT-6 Astra Pro",),
                ("GPT-6 Astra",),
                ("Pro",),
                (
                    "GPT-6 Astra",
                    "6 Astra",
                    "gpt-6-astra",
                    "GPT-6 Astra Pro",
                    "6 Astra Pro",
                ),
            ),
            "GPT-5.6 Pro": (
                ("GPT-5.6 Pro", "GPT-5.6 Sol Pro"),
                ("GPT-5.6 Pro",),
                ("GPT-5.6 Sol",),
                ("Pro",),
                ("GPT-5.6 Pro", "5.6 Pro", "GPT-5.6 Sol Pro", "5.6 Sol Pro"),
            ),
            "GPT-5.6 Thinking": (
                ("GPT-5.6 Thinking", "GPT-5.6 Sol"),
                ("GPT-5.6 Thinking",),
                ("GPT-5.6 Sol",),
                ("Extra High", "\u6781\u9ad8"),
                ("GPT-5.6 Thinking", "5.6 Thinking", "GPT-5.6 Sol", "5.6 Sol"),
            ),
        }

        self.assertEqual(extract_profile_rows(SKILL_TEXT), expected_profiles)

    def test_profile_aliases_and_identities_are_unambiguous(self) -> None:
        aliases: set[str] = set()
        identities: set[str] = set()
        for profile in extract_profile_rows(SKILL_TEXT).values():
            with self.subTest(target_model=profile[1]):
                self.assertFalse(aliases.intersection(profile[0]))
                self.assertFalse(identities.intersection(profile[4]))
                aliases.update(profile[0])
                identities.update(profile[4])

        self.assertTrue({"GPT-6 Astra Pro", "GPT-6 Pro", "6-pro"} <= aliases)
        self.assertNotIn("gpt-6-pro", aliases)
        self.assertNotIn("GPT-6 Astra mini", identities)
        self.assertNotIn("GPT-6", identities)
        self.assertNotIn("Pro", identities)

    def test_readme_model_table_matches_the_skill(self) -> None:
        documented_profiles = extract_profile_rows(README_TEXT)
        skill_profiles = extract_profile_rows(SKILL_TEXT)
        self.assertEqual(documented_profiles.keys(), skill_profiles.keys())
        for name, profile in skill_profiles.items():
            with self.subTest(profile=name):
                self.assertEqual(documented_profiles[name], (profile[0], *profile[2:]))

    def test_gate_rejects_cross_model_switches_and_fallbacks(self) -> None:
        required_guards = (
            "\u4e0d\u8981\u5207\u6362\u5230\u5176\u4ed6\u63a8\u7406\u6a21\u5f0f",
            "\u4e0d\u81ea\u52a8\u6062\u590d\u9009\u62e9\u6216\u65b0\u5efa\u5bf9\u8bdd\u91cd\u8bd5",
            "\u4e0d\u8981\u56de\u9000\u5230\u9ed8\u8ba4\u6a21\u578b",
            "\u4e0d\u5f97\u8ba9\u5e73\u53f0\u56de\u9000\u6a21\u578b\u7ee7\u7eed\u59d4\u6258",
            "\u4e0d\u8981\u4f7f\u7528\u6700\u63a5\u8fd1\u7684\u6863\u4f4d",
        )

        for required_guard in required_guards:
            with self.subTest(required_guard=required_guard):
                self.assertIn(required_guard, SKILL_TEXT)

        self.assertNotIn("Pro \u2192 \u6781\u9ad8 \u2192 Pro", SKILL_TEXT)

    def test_gate_requires_model_family_and_pro_mode_evidence(self) -> None:
        gate_section = SKILL_TEXT.split("### \u5f3a\u5236\u6a21\u578b\u95e8\u7981", 1)[
            1
        ].split("\n## ", 1)[0]
        self.assertIn("`modelFamily`", gate_section)
        self.assertIn("`reasoningMode`", gate_section)
        self.assertIn("`acceptedIdentities`", gate_section)
        required_guards = (
            "\u5148\u9009\u62e9\u5e76\u6838\u5b9e `modelFamily`",
            (
                "\u5fc5\u987b\u53e6\u6709\u754c\u9762 `Pro` \u5df2\u9009\u4e2d"
                "\u7684\u8bc1\u636e"
            ),
            (
                "\u6309\u5b8c\u6574\u8eab\u4efd\u5224\u65ad\uff0c"
                "\u4e0d\u505a\u5b50\u4e32\u653e\u884c"
            ),
            (
                "\u5728\u53d1\u9001\u8eab\u4efd\u68c0\u67e5\u6d88\u606f\u524d"
                "\u7acb\u5373\u7ec8\u6b62"
            ),
            (
                "\u81ea\u62a5\u660e\u786e\u79f0\u672a\u4f7f\u7528 Pro "
                "\u65f6\u5fc5\u987b\u5931\u8d25"
            ),
        )
        for required_guard in required_guards:
            with self.subTest(required_guard=required_guard):
                self.assertIn(required_guard, gate_section)

    def test_invalid_or_conflicting_configuration_fails_before_browser(self) -> None:
        required_fail_fast_rules = (
            "\u540c\u4e00\u6b21\u8c03\u7528\u51fa\u73b0\u51b2\u7a81\u7684\u6a21\u578b\u503c",
            "\u503c\u7f3a\u5931\u3001\u4e3a\u7a7a\u6216\u4e0d\u5728\u652f\u6301\u5217\u8868\u4e2d",
            "\u5728\u6253\u5f00 ChatGPT \u524d\u7ec8\u6b62\u76ee\u6807\u6a21\u578b\u8c03\u7528",
        )

        for required_rule in required_fail_fast_rules:
            with self.subTest(required_rule=required_rule):
                self.assertIn(required_rule, SKILL_TEXT)

    def test_readme_documents_astra_and_explicit_legacy_profiles(self) -> None:
        required_documentation = (
            "## \u6a21\u578b\u914d\u7f6e",
            "\u6a21\u578b: GPT-6 Astra Pro",
            "\u6a21\u578b: GPT-5.6 Thinking",
            "`GPT-6 Pro`",
            "`6-pro`",
            "`gpt-6-astra`",
            "https://developers.openai.com/api/docs/models/gpt-6-astra",
            "https://developers.openai.com/api/docs/guides/latest-model",
            "`GPT-5.6 Sol Pro`",
            "`GPT-5.6 Sol`",
            "`Pro`",
            "`Extra High`",
            (
                "GPT-5.6 Thinking` \u662f\u672c Skill \u63d0\u4f9b\u7684"
                "\u517c\u5bb9\u914d\u7f6e\u540d"
            ),
            "\u4e0d\u4f1a\u5207\u6362\u5230\u53e6\u4e00\u4e2a\u6a21\u578b\u7ee7\u7eed",
        )

        for required_text in required_documentation:
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, README_TEXT)

        usage_section = extract_level_two_section(README_TEXT, "\u4f7f\u7528")
        model_lines = [
            line
            for line in usage_section.splitlines()
            if line.startswith("\u6a21\u578b:")
        ]
        self.assertEqual(
            model_lines,
            [
                "\u6a21\u578b: GPT-6 Astra Pro",
                "\u6a21\u578b: GPT-5.6 Thinking",
                "\u6a21\u578b: GPT-6 Astra Pro",
            ],
        )
        self.assertIn("\u6a21\u5f0f: delegate", usage_section)
        self.assertNotIn("\nmodel:", usage_section)
        self.assertNotIn("\nmode:", usage_section)

    def test_ui_metadata_matches_the_configurable_model_workflow(self) -> None:
        self.assertIn(
            'display_name: "GPT \u53ef\u914d\u7f6e\u6a21\u578b\u534f\u4f5c"',
            OPENAI_YAML_TEXT,
        )
        self.assertIn("GPT-6 Astra Pro", OPENAI_YAML_TEXT)
        self.assertIn("$gpt-thinking-pro-collab", OPENAI_YAML_TEXT)
        self.assertNotIn(STALE_INVOCATION, OPENAI_YAML_TEXT)
        self.assertIn("\u6a21\u578b: GPT-6 Astra Pro", OPENAI_YAML_TEXT)
        self.assertNotIn("\u6a21\u578b: GPT-5.6 Pro", OPENAI_YAML_TEXT)
        self.assertIn("\u6a21\u5f0f: consult", OPENAI_YAML_TEXT)
        self.assertIn("allow_implicit_invocation: false", OPENAI_YAML_TEXT)

    def test_canonical_invocation_name_is_consistent(self) -> None:
        for artifact in (SKILL_TEXT, README_TEXT, OPENAI_YAML_TEXT):
            with self.subTest(artifact=artifact[:32]):
                self.assertIn("$gpt-thinking-pro-collab", artifact)

        self.assertNotIn(STALE_INVOCATION, SKILL_TEXT)
        self.assertNotIn(STALE_INVOCATION, OPENAI_YAML_TEXT)

    def test_python_source_uses_ascii_only(self) -> None:
        TEST_SOURCE_TEXT.encode("ascii")

    def test_readme_usage_examples_are_localized(self) -> None:
        usage_section = extract_level_two_section(README_TEXT, "\u4f7f\u7528")
        required_localized_text = (
            "\u9700\u6c42\uff1a",
            "\u9a8c\u6536\uff1a",
            "\u4f7f\u7528 GPT-6 Astra Pro \u548c delegate \u6a21\u5f0f",
        )
        stale_english_text = ("Request:", "Acceptance:", "Use GPT-5.6")

        for required_text in required_localized_text:
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, usage_section)

        for stale_text in stale_english_text:
            with self.subTest(stale_text=stale_text):
                self.assertNotIn(stale_text, usage_section)

        extract_fenced_blocks(README_TEXT)

    def test_readme_mermaid_visible_labels_are_localized(self) -> None:
        mermaid_blocks = [
            block
            for block in extract_fenced_blocks(README_TEXT)
            if block.startswith("flowchart ")
        ]
        self.assertEqual(len(mermaid_blocks), 1)

        visible_labels = re.findall(r'"([^"]+)"', mermaid_blocks[0])
        self.assertGreater(len(visible_labels), 0)
        for label in visible_labels:
            with self.subTest(label=label):
                self.assertIsNone(re.search(r"[A-Za-z]", label))

    def test_skill_markdown_fenced_blocks_use_english_content(self) -> None:
        han_character = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")

        for block_index, block in enumerate(extract_fenced_blocks(SKILL_TEXT)):
            with self.subTest(block_index=block_index):
                self.assertIsNone(han_character.search(block))


if __name__ == "__main__":
    unittest.main()
