from __future__ import annotations

import copy
import io
import json
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/gpt-thinking-pro-collab"
sys.path.insert(0, str(SKILL / "scripts"))
from artifact_utils import ArtifactError, deterministic_zip, sha256, write_outputs
from context_bundle import build_context
from verify_delivery import verify_delivery


class ArtifactBehaviorTest(unittest.TestCase):
    def test_empty_project_can_capture_a_baseline_for_new_files(self) -> None:
        payload, baseline = build_context(self.root, [], archive=False)
        self.assertIsNone(payload)
        candidate = deterministic_zip({"new.py": b"value = 1\n"})
        changes = [{"path": "new.py", "action": "add", "baseSha256": None}]
        verify_delivery(
            self.root,
            candidate,
            self.manifest(candidate, baseline, kind="zip", changes=changes),
            baseline,
        )
        with self.assertRaises(ArtifactError):
            build_context(self.root, [])

    def test_unborn_git_repository_does_not_require_an_unauthorized_commit(
        self,
    ) -> None:
        subprocess.run(
            ["git", "-C", str(self.root), "init", "-q"], check=True, capture_output=True
        )
        baseline = self.baseline(archive=False)
        self.assertIsNone(baseline["baseCommit"])
        self.assertTrue(baseline["dirty"])
        verify_delivery(
            self.root, self.patch, self.manifest(self.patch, baseline), baseline
        )

    def test_delivery_rejects_non_object_or_boolean_schema(self) -> None:
        baseline = self.baseline()
        for manifest in (
            [],
            {**self.manifest(self.patch, baseline), "schemaVersion": True},
        ):
            with self.subTest(manifest=manifest), self.assertRaises(ArtifactError):
                verify_delivery(self.root, self.patch, manifest, baseline)

    def test_new_path_cannot_descend_through_an_existing_file(self) -> None:
        baseline = self.baseline()
        candidate = deterministic_zip({"source.py/new.py": b"value = 1\n"})
        changes = [{"path": "source.py/new.py", "action": "add", "baseSha256": None}]
        with self.assertRaisesRegex(ArtifactError, "Parent is not a directory"):
            verify_delivery(
                self.root,
                candidate,
                self.manifest(candidate, baseline, kind="zip", changes=changes),
                baseline,
            )

    def test_delivery_rejects_new_file_directory_conflicts(self) -> None:
        baseline = self.baseline()
        for parent in ("new.py", "NEW.py"):
            files = {"new.py": b"file", f"{parent}/child.py": b"child"}
            payload = deterministic_zip(files)
            changes = [
                {"path": name, "action": "add", "baseSha256": None} for name in files
            ]
            with self.subTest(parent=parent), self.assertRaises(ArtifactError):
                verify_delivery(
                    self.root,
                    payload,
                    self.manifest(payload, baseline, kind="zip", changes=changes),
                    baseline,
                )

    def test_zip_rejects_conflicting_directory_entries(self) -> None:
        baseline = self.baseline()
        for directories in (("docs/", "DOCS/"), ("source.py/",)):
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w") as archive:
                archive.writestr("source.py", b"value = 2\n")
                for directory in directories:
                    archive.writestr(directory, b"")
            payload = buffer.getvalue()
            with (
                self.subTest(directories=directories),
                self.assertRaises(ArtifactError),
            ):
                verify_delivery(
                    self.root,
                    payload,
                    self.manifest(payload, baseline, kind="zip"),
                    baseline,
                )

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="collab-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "project"
        self.root.mkdir()
        (self.root / "source.py").write_text("value = 1\n")
        self.patch = (
            b"--- a/source.py\n+++ b/source.py\n@@ -1 +1 @@\n-value = 1\n+value = 2\n"
        )

    def baseline(self, *, archive: bool = True) -> dict:
        return build_context(self.root, ["source.py"], archive=archive)[1]

    def manifest(
        self,
        payload: bytes,
        baseline: dict,
        *,
        kind: str = "diff",
        changes: list | None = None,
    ) -> dict:
        return {
            "schemaVersion": 1,
            "format": kind,
            "baseCommit": baseline["baseCommit"],
            "contextSha256": baseline["archiveSha256"],
            "artifactSha256": sha256(payload),
            "changes": changes
            if changes is not None
            else [
                {
                    "path": "source.py",
                    "action": "modify",
                    "baseSha256": baseline["files"][0]["sha256"],
                }
            ],
            "review": {
                "kind": "author",
                "scope": ["source.py"]
                if changes is None
                else [item["path"] for item in changes],
            },
            "assumptions": [],
            "validationCommands": [],
            "risks": [],
        }

    def init_git(self) -> None:
        for args in (
            ["init", "-q"],
            ["add", "source.py"],
            [
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-qm",
                "Add fixture",
            ],
        ):
            subprocess.run(
                ["git", "-C", str(self.root), *args], check=True, capture_output=True
            )

    def test_context_is_deterministic_and_records_dirty_bytes(self) -> None:
        self.init_git()
        (self.root / "source.py").write_text("value = 3\n")
        first, manifest = build_context(self.root, ["source.py"])
        second, repeated = build_context(self.root, ["source.py"])
        self.assertEqual(first, second)
        self.assertEqual(manifest, repeated)
        self.assertTrue(manifest["dirty"])
        self.assertEqual(manifest["files"][0]["sha256"], sha256(b"value = 3\n"))
        with zipfile.ZipFile(io.BytesIO(first)) as archive:
            self.assertEqual(archive.namelist(), ["source.py"])
            self.assertEqual(archive.read("source.py"), b"value = 3\n")

    def test_inline_context_has_no_archive_and_keeps_file_baseline(self) -> None:
        payload, baseline = build_context(self.root, ["source.py"], archive=False)
        self.assertIsNone(payload)
        self.assertIsNone(baseline["archiveSha256"])
        self.assertEqual(baseline["files"][0]["sha256"], sha256(b"value = 1\n"))

    def test_context_rejects_traversal_absolute_paths_and_duplicates(self) -> None:
        for paths in (
            ["../source.py"],
            ["/source.py"],
            ["C:/source.py"],
            ["source.py", "source.py"],
            ["source.py", "SOURCE.py"],
            ["source.py/../source.py"],
        ):
            with self.subTest(paths=paths), self.assertRaises(ArtifactError):
                build_context(self.root, paths)

    def test_context_excludes_credentials_dependencies_and_state(self) -> None:
        for name in (
            ".env",
            ".env.example",
            "node_modules/lib.js",
            "dist/app.js",
            "private.key",
            "cache.sqlite",
            ".git/config",
            "browser-state/profile.json",
        ):
            with self.subTest(name=name), self.assertRaises(ArtifactError):
                build_context(self.root, [name])

    def test_context_rejects_symlink_even_when_target_is_inside_root(self) -> None:
        (self.root / "link.py").symlink_to("source.py")
        with self.assertRaises(ArtifactError):
            build_context(self.root, ["link.py"])

    def test_context_scanner_omits_secret_value_from_error(self) -> None:
        value = "super-sensitive-value"
        (self.root / "config.py").write_text(f'api_key = "{value}"\n')
        with self.assertRaises(ArtifactError) as caught:
            build_context(self.root, ["config.py"])
        self.assertNotIn(value, str(caught.exception))

    def test_context_cli_does_not_write_on_scan_failure(self) -> None:
        (self.root / "config.py").write_text('password = "super-sensitive-value"\n')
        paths = Path(self.temporary.name) / "paths.txt"
        paths.write_text("config.py\n")
        output = Path(self.temporary.name) / "context.zip"
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                str(SKILL / "scripts/context_bundle.py"),
                "--root",
                str(self.root),
                "--paths-file",
                str(paths),
                "--output",
                str(output),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertFalse(output.exists())
        self.assertNotIn("super-sensitive-value", result.stderr)

    def test_outputs_are_idempotent_and_do_not_overwrite_existing_data(self) -> None:
        output = Path(self.temporary.name) / "artifact"
        write_outputs({output: b"original"})
        write_outputs({output: b"original"})
        with self.assertRaises(ArtifactError):
            write_outputs({output: b"changed"})
        self.assertEqual(output.read_bytes(), b"original")

    def test_valid_patch_uses_original_dirty_baseline_without_modifying_workspace(
        self,
    ) -> None:
        self.init_git()
        (self.root / "unrelated.txt").write_text("用户尚未提交的改动")
        baseline = self.baseline()
        before = (self.root / "source.py").read_bytes()
        result = verify_delivery(
            self.root, self.patch, self.manifest(self.patch, baseline), baseline
        )
        self.assertTrue(result["identityVerified"])
        self.assertTrue(result["requiresCodexReview"])
        self.assertFalse(result["appliedToWorkspace"])
        self.assertEqual((self.root / "source.py").read_bytes(), before)
        self.assertEqual(
            (self.root / "unrelated.txt").read_text(encoding="utf-8"),
            "用户尚未提交的改动",
        )

    def test_patch_for_dirty_target_applies_to_captured_worktree_bytes(self) -> None:
        self.init_git()
        (self.root / "source.py").write_text("value = 10\n")
        baseline = self.baseline(archive=False)
        payload = self.patch.replace(b"value = 1\n", b"value = 10\n")
        verify_delivery(self.root, payload, self.manifest(payload, baseline), baseline)
        self.assertEqual(
            (self.root / "source.py").read_text(encoding="utf-8"), "value = 10\n"
        )

    def test_changed_target_is_rejected_even_with_same_git_head(self) -> None:
        self.init_git()
        baseline = self.baseline()
        (self.root / "source.py").write_text("value = 99\n")
        with self.assertRaisesRegex(ArtifactError, "drifted"):
            verify_delivery(
                self.root, self.patch, self.manifest(self.patch, baseline), baseline
            )

    def test_model_cannot_replace_the_trusted_baseline_with_current_hash(self) -> None:
        baseline = self.baseline()
        (self.root / "source.py").write_text("value = 99\n")
        manifest = self.manifest(self.patch, baseline)
        manifest["changes"][0]["baseSha256"] = sha256(b"value = 99\n")
        with self.assertRaises(ArtifactError):
            verify_delivery(self.root, self.patch, manifest, baseline)

    def test_commit_drift_is_rejected(self) -> None:
        self.init_git()
        baseline = self.baseline()
        subprocess.run(
            [
                "git",
                "-C",
                str(self.root),
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "--allow-empty",
                "-qm",
                "Advance fixture",
            ],
            check=True,
            capture_output=True,
        )
        with self.assertRaisesRegex(ArtifactError, "commit drifted"):
            verify_delivery(
                self.root, self.patch, self.manifest(self.patch, baseline), baseline
            )

    def test_artifact_context_and_baseline_mismatches_are_rejected(self) -> None:
        baseline = self.baseline()
        for field in ("artifactSha256", "contextSha256"):
            manifest = self.manifest(self.patch, baseline)
            manifest[field] = "0" * 64
            with self.subTest(field=field), self.assertRaises(ArtifactError):
                verify_delivery(self.root, self.patch, manifest, baseline)
        with self.assertRaises(ArtifactError):
            verify_delivery(
                self.root, self.patch, self.manifest(self.patch, baseline), None
            )

    def test_invalid_hunks_are_rejected_despite_matching_hashes(self) -> None:
        baseline = self.baseline()
        invalid = self.patch.replace(b"-value = 1", b"-value = 9")
        with self.assertRaisesRegex(ArtifactError, "does not apply"):
            verify_delivery(
                self.root, invalid, self.manifest(invalid, baseline), baseline
            )

    def test_patch_paths_must_match_manifest(self) -> None:
        baseline = self.baseline()
        payload = self.patch.replace(b"source.py", b"other.py")
        with self.assertRaisesRegex(ArtifactError, "paths differ"):
            verify_delivery(
                self.root, payload, self.manifest(payload, baseline), baseline
            )

    def test_delete_and_add_actions_are_checked_in_temporary_workspace(self) -> None:
        baseline = self.baseline()
        payload = b"--- a/source.py\n+++ /dev/null\n@@ -1 +0,0 @@\n-value = 1\n--- /dev/null\n+++ b/new.py\n@@ -0,0 +1 @@\n+value = 2\n"
        changes = [
            {
                "path": "source.py",
                "action": "delete",
                "baseSha256": baseline["files"][0]["sha256"],
            },
            {"path": "new.py", "action": "add", "baseSha256": None},
        ]
        verify_delivery(
            self.root,
            payload,
            self.manifest(payload, baseline, changes=changes),
            baseline,
        )
        self.assertTrue((self.root / "source.py").exists())
        self.assertFalse((self.root / "new.py").exists())
        changes[0]["action"] = "modify"
        with self.assertRaisesRegex(ArtifactError, "action differs"):
            verify_delivery(
                self.root,
                payload,
                self.manifest(payload, baseline, changes=changes),
                baseline,
            )

    def test_zip_contains_only_declared_files(self) -> None:
        baseline = self.baseline()
        valid = deterministic_zip({"source.py": b"value = 2\n"})
        verify_delivery(
            self.root, valid, self.manifest(valid, baseline, kind="zip"), baseline
        )
        invalid = deterministic_zip(
            {"source.py": b"value = 2\n", "extra.py": b"not declared"}
        )
        with self.assertRaisesRegex(ArtifactError, "ZIP contents differ"):
            verify_delivery(
                self.root,
                invalid,
                self.manifest(invalid, baseline, kind="zip"),
                baseline,
            )

    def test_zip_rejects_traversal_symlink_and_expansion_limit(self) -> None:
        baseline = self.baseline()
        for name, mode in (
            ("../outside.py", 0o100644),
            ("source.py", stat.S_IFLNK | 0o777),
        ):
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w") as archive:
                info = zipfile.ZipInfo(name)
                info.external_attr = mode << 16
                archive.writestr(info, b"target")
            payload = buffer.getvalue()
            with self.subTest(name=name), self.assertRaises(ArtifactError):
                verify_delivery(
                    self.root,
                    payload,
                    self.manifest(payload, baseline, kind="zip"),
                    baseline,
                )
        payload = deterministic_zip({"source.py": b"x" * 100})
        with self.assertRaisesRegex(ArtifactError, "expanded-size"):
            verify_delivery(
                self.root,
                payload,
                self.manifest(payload, baseline, kind="zip"),
                baseline,
                max_bytes=10,
            )

    def test_existing_new_file_is_not_overwritten(self) -> None:
        baseline = self.baseline()
        payload = deterministic_zip({"new.py": b"candidate"})
        changes = [{"path": "new.py", "action": "add", "baseSha256": None}]
        manifest = self.manifest(payload, baseline, kind="zip", changes=changes)
        (self.root / "new.py").write_text("user work")
        with self.assertRaisesRegex(ArtifactError, "collision"):
            verify_delivery(self.root, payload, manifest, baseline)
        self.assertEqual(
            (self.root / "new.py").read_text(encoding="utf-8"), "user work"
        )

    def test_text_advice_can_have_no_context_and_no_changes(self) -> None:
        baseline = self.baseline(archive=False)
        payload = "审阅结果".encode()
        manifest = self.manifest(payload, baseline, kind="text", changes=[])
        result = verify_delivery(self.root, payload, manifest, None)
        self.assertEqual(result["changedFiles"], [])
        self.assertFalse(result["baselineVerified"])

    def test_review_claim_never_disables_codex_review(self) -> None:
        baseline = self.baseline()
        for kind in ("none", "author", "independent"):
            manifest = self.manifest(self.patch, baseline)
            manifest["review"]["kind"] = kind
            self.assertTrue(
                verify_delivery(self.root, self.patch, manifest, baseline)[
                    "requiresCodexReview"
                ]
            )

    def test_malformed_manifests_are_rejected(self) -> None:
        baseline = self.baseline()
        for field, value in (
            ("schemaVersion", 2),
            ("format", "shell"),
            ("changes", "anything"),
            ("review", None),
        ):
            manifest = copy.deepcopy(self.manifest(self.patch, baseline))
            manifest[field] = value
            with self.subTest(field=field), self.assertRaises(ArtifactError):
                verify_delivery(self.root, self.patch, manifest, baseline)

    def test_verifier_cli_reports_validation_without_applying(self) -> None:
        baseline = self.baseline(archive=False)
        directory = Path(self.temporary.name)
        artifact = directory / "candidate.diff"
        artifact.write_bytes(self.patch)
        manifest = directory / "manifest.json"
        manifest.write_text(json.dumps(self.manifest(self.patch, baseline)))
        baseline_path = directory / "baseline.json"
        baseline_path.write_text(json.dumps(baseline))
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                str(SKILL / "scripts/verify_delivery.py"),
                "--root",
                str(self.root),
                "--artifact",
                str(artifact),
                "--manifest",
                str(manifest),
                "--baseline",
                str(baseline_path),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)["appliedToWorkspace"])
        self.assertEqual(
            (self.root / "source.py").read_text(encoding="utf-8"), "value = 1\n"
        )


if __name__ == "__main__":
    unittest.main()
