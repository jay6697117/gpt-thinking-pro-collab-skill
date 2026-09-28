from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from package_skill import SKILL, fingerprint, package_files
from verify_distribution import (
    REPOSITORY,
    SLUG,
    catalog_files,
    compare_files,
    github_files,
    installed_files,
)


class DistributionTest(unittest.TestCase):
    def test_package_excludes_repository_history_and_tests(self) -> None:
        files = package_files()
        self.assertIn("SKILL.md", files)
        self.assertIn("references/browser-workflow.md", files)
        self.assertIn("scripts/verify_delivery.py", files)
        self.assertFalse(any(name.startswith(("tests/", "docs/")) for name in files))
        self.assertTrue(
            {"README.md", "task_plan.md", "progress.md", "findings.md"}.isdisjoint(
                files
            )
        )

    def test_package_fingerprint_covers_every_file(self) -> None:
        files = package_files()
        original = fingerprint(files)
        changed = dict(files)
        changed["references/reporting.md"] += b"\nChanged\n"
        self.assertNotEqual(
            original["sourceSha256"], fingerprint(changed)["sourceSha256"]
        )
        self.assertEqual(original, fingerprint(dict(reversed(list(files.items())))))

    def test_package_rejects_unlisted_files(self) -> None:
        with tempfile.TemporaryDirectory(prefix="collab-package-") as temporary:
            destination = Path(temporary) / "skill"
            shutil.copytree(SKILL, destination)
            (destination / "private-notes.md").write_text("Not distributable")
            with self.assertRaisesRegex(ValueError, "allowlist mismatch"):
                package_files(destination)

    def test_comparison_detects_changed_missing_and_extra_content(self) -> None:
        expected = {"SKILL.md": b"current", "references/rules.md": b"important"}
        actual = {"SKILL.md": b"old", "progress.md": b"history"}
        result = compare_files(expected, actual)
        self.assertFalse(result["matches"])
        self.assertEqual(result["missing"], ["references/rules.md"])
        self.assertEqual(result["changed"], ["SKILL.md"])
        self.assertEqual(result["extra"], ["progress.md"])

    def test_github_comparison_discovers_extra_files_and_pins_the_revision(
        self,
    ) -> None:
        revision = "a" * 40
        api = f"https://api.github.com/repos/{REPOSITORY}"
        raw = (
            f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/skills/{SLUG}/"
        )
        responses = {
            f"{api}/commits/main": json.dumps({"sha": revision}).encode(),
            f"{api}/git/trees/{revision}?recursive=1": json.dumps(
                {
                    "truncated": False,
                    "tree": [
                        {"path": "README.md", "type": "blob", "mode": "100644"},
                        {"path": f"skills/{SLUG}", "type": "tree", "mode": "040000"},
                    ],
                }
            ).encode(),
            f"{raw}SKILL.md": b"current",
            f"{raw}extra.md": b"unlisted",
        }
        tree = json.loads(responses[f"{api}/git/trees/{revision}?recursive=1"])
        tree["tree"].extend(
            {"path": f"skills/{SLUG}/{name}", "type": "blob", "mode": "100644"}
            for name in ("SKILL.md", "extra.md")
        )
        responses[f"{api}/git/trees/{revision}?recursive=1"] = json.dumps(tree).encode()
        with patch("verify_distribution.fetch", side_effect=responses.__getitem__):
            actual = github_files("main")
        result = compare_files({"SKILL.md": b"current"}, actual)
        self.assertFalse(result["matches"])
        self.assertEqual(result["extra"], ["extra.md"])

    def test_github_rejects_incomplete_trees_and_non_regular_files(self) -> None:
        for tree in (
            {"truncated": True, "tree": []},
            {
                "truncated": False,
                "tree": [
                    {"path": f"skills/{SLUG}/link", "type": "blob", "mode": "120000"}
                ],
            },
        ):
            with (
                self.subTest(tree=tree),
                patch(
                    "verify_distribution.fetch",
                    side_effect=[
                        json.dumps({"sha": "a" * 40}).encode(),
                        json.dumps(tree).encode(),
                    ],
                ),
                self.assertRaises(ValueError),
            ):
                github_files("main")

    def test_catalog_handles_current_prefix_and_flags_old_root_package(self) -> None:
        payload = json.dumps(
            {
                "files": [
                    {
                        "path": "skills/gpt-thinking-pro-collab/SKILL.md",
                        "contents": "current",
                    }
                ]
            }
        ).encode()
        self.assertEqual(catalog_files(payload), {"SKILL.md": b"current"})
        old = json.dumps(
            {
                "files": [
                    {"path": "SKILL.md", "contents": "old"},
                    {"path": "task_plan.md", "contents": "history"},
                ]
            }
        ).encode()
        self.assertFalse(
            compare_files({"SKILL.md": b"current"}, catalog_files(old))["matches"]
        )

    def test_catalog_rejects_ambiguous_duplicate_paths(self) -> None:
        payload = json.dumps(
            {
                "files": [
                    {"path": "SKILL.md", "contents": "first"},
                    {"path": "SKILL.md", "contents": "second"},
                ]
            }
        ).encode()
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            catalog_files(payload)

    def test_installed_directory_comparison_includes_runtime_resources(self) -> None:
        with tempfile.TemporaryDirectory(prefix="collab-install-") as temporary:
            destination = Path(temporary) / "skill"
            shutil.copytree(SKILL, destination)
            self.assertTrue(
                compare_files(package_files(), installed_files(destination))["matches"]
            )
            (destination / "references/context.md").unlink()
            self.assertFalse(
                compare_files(package_files(), installed_files(destination))["matches"]
            )


if __name__ == "__main__":
    unittest.main()
