"""Check a detached delivery manifest against a trusted local baseline."""

from __future__ import annotations

import argparse
import io
import json
import re
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from artifact_utils import (
    ArtifactError,
    git_identity,
    local_path,
    read_file,
    sha256,
    unique_paths,
)


def require_hash(value: object, field: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ArtifactError(f"{field} must be a lowercase SHA-256 digest")
    return value


def zip_files(payload: bytes, max_bytes: int) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        infos = archive.infolist()
        if sum(info.file_size for info in infos) > max_bytes:
            raise ArtifactError("Delivery exceeds the expanded-size limit")
        names = unique_paths([info.filename for info in infos if not info.is_dir()])
        files = {}
        members = set()
        for info in infos:
            name = info.filename[:-1] if info.is_dir() else info.filename
            unique_paths([name])
            if name.casefold() in members:
                raise ArtifactError("Duplicate or case-colliding archive members")
            members.add(name.casefold())
            mode = info.external_attr >> 16
            allowed_modes = {0, stat.S_IFDIR} if info.is_dir() else {0, stat.S_IFREG}
            if stat.S_IFMT(mode) not in allowed_modes:
                raise ArtifactError(f"Non-regular archive member: {name}")
            if not info.is_dir():
                files[name] = archive.read(info)
        if sorted(files) != names:
            raise ArtifactError("Archive file list mismatch")
        return files


def check_diff(root: Path, payload: bytes, changes: dict[str, dict]) -> None:
    if re.search(
        rb"^(?:(?:rename|copy) (?:from|to) |GIT binary patch$)", payload, re.M
    ):
        raise ArtifactError(
            "Use explicit file additions/deletions or ZIP for renames/binary changes"
        )
    for mode in re.findall(
        rb"^(?:new file mode|deleted file mode|old mode|new mode) (\d+)$", payload, re.M
    ):
        if mode not in {b"100644", b"100755"}:
            raise ArtifactError("Only regular-file patches are supported")
    with tempfile.TemporaryDirectory(prefix="collab-delivery-") as temporary:
        sandbox = Path(temporary)
        patch = sandbox / "delivery.patch"
        patch.write_bytes(payload)
        worktree = sandbox / "tree"
        worktree.mkdir()
        stat_result = subprocess.run(
            ["git", "apply", "--numstat", "-z", "--", str(patch)],
            cwd=worktree,
            capture_output=True,
        )
        if stat_result.returncode:
            raise ArtifactError("Git cannot parse this unified diff")
        try:
            paths = [
                record.split(b"\t", 2)[2].decode("utf-8")
                for record in stat_result.stdout.split(b"\0")
                if record
            ]
        except (IndexError, UnicodeError) as exc:
            raise ArtifactError("Unsupported patch path format") from exc
        if unique_paths(paths) != sorted(changes):
            raise ArtifactError("Patch paths differ from the manifest")
        for name, change in changes.items():
            if change["action"] != "add":
                destination = worktree / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(read_file(root, name))
                destination.chmod(local_path(root, name).stat().st_mode & 0o777)
        result = subprocess.run(
            ["git", "apply", "--check", "--", str(patch)],
            cwd=worktree,
            capture_output=True,
        )
        if result.returncode:
            raise ArtifactError("Patch does not apply to the captured current files")
        subprocess.run(
            ["git", "apply", "--", str(patch)],
            cwd=worktree,
            capture_output=True,
            check=True,
        )
        for name, change in changes.items():
            exists = (worktree / name).is_file()
            if exists != (change["action"] != "delete"):
                raise ArtifactError(f"Patch action differs from the manifest: {name}")
        actual = {
            path.relative_to(worktree).as_posix()
            for path in worktree.rglob("*")
            if path.is_file()
        }
        expected = {
            name for name, change in changes.items() if change["action"] != "delete"
        }
        if actual != expected:
            raise ArtifactError("Patch created unexpected files")


def verify_delivery(
    root: Path,
    payload: bytes,
    manifest: dict,
    baseline: dict | None,
    *,
    max_bytes: int = 128 * 1024 * 1024,
) -> dict:
    required = {
        "schemaVersion",
        "format",
        "baseCommit",
        "contextSha256",
        "artifactSha256",
        "changes",
        "review",
        "assumptions",
        "validationCommands",
        "risks",
    }
    if not isinstance(manifest, dict) or not required.issubset(manifest):
        raise ArtifactError("Delivery manifest is missing required fields")
    if type(manifest["schemaVersion"]) is not int or manifest["schemaVersion"] != 1:
        raise ArtifactError("Unsupported delivery schemaVersion")
    for field in ("assumptions", "validationCommands", "risks"):
        if not isinstance(manifest[field], list) or not all(
            isinstance(value, str) for value in manifest[field]
        ):
            raise ArtifactError(f"{field} must be a list of strings")
    kind = manifest.get("format")
    if kind not in {"text", "diff", "zip"}:
        raise ArtifactError("Unsupported delivery format")
    if require_hash(manifest.get("artifactSha256"), "artifactSha256") != sha256(
        payload
    ):
        raise ArtifactError("Artifact digest mismatch")
    changes_list = manifest.get("changes")
    if not isinstance(changes_list, list) or not all(
        isinstance(item, dict) for item in changes_list
    ):
        raise ArtifactError("changes must be a list of objects")
    names = unique_paths([item.get("path") for item in changes_list])
    changes = {item["path"]: item for item in changes_list}
    review = manifest.get("review")
    if not isinstance(review, dict) or review.get("kind") not in {
        "none",
        "author",
        "independent",
    }:
        raise ArtifactError("Declare the review kind without treating it as proof")
    if not isinstance(review.get("scope"), list) or not set(
        unique_paths(review["scope"])
    ).issubset(names):
        raise ArtifactError("Review scope must be within changed paths")
    if kind == "text" and changes:
        raise ArtifactError("Text advice cannot declare applicable file changes")
    if kind != "text" and not changes:
        raise ArtifactError("Code deliveries must list affected files")
    if manifest.get("baseCommit") != git_identity(root)[0]:
        raise ArtifactError("Source commit drifted")
    if changes and baseline is None:
        raise ArtifactError("Code delivery needs a trusted local pre-send baseline")
    context_hash = manifest.get("contextSha256")
    if context_hash is not None:
        require_hash(context_hash, "contextSha256")
    if baseline is not None:
        if not isinstance(baseline, dict) or not {
            "schemaVersion",
            "baseCommit",
            "archiveSha256",
            "files",
        }.issubset(baseline):
            raise ArtifactError("Malformed trusted baseline")
        if (
            type(baseline["schemaVersion"]) is not int
            or baseline["schemaVersion"] != 1
            or baseline.get("baseCommit") != manifest.get("baseCommit")
        ):
            raise ArtifactError("Baseline identity mismatch")
        if baseline.get("archiveSha256") != context_hash:
            raise ArtifactError("Context digest differs from the local baseline")
        base_items = baseline.get("files")
        if not isinstance(base_items, list) or not all(
            isinstance(item, dict) and {"path", "sha256"}.issubset(item)
            for item in base_items
        ):
            raise ArtifactError("Malformed baseline files")
        unique_paths([item["path"] for item in base_items])
        base_files = {
            item["path"]: require_hash(item["sha256"], "baseline file hash")
            for item in base_items
        }
    else:
        if context_hash is not None:
            raise ArtifactError("Context digest requires its trusted baseline")
        base_files = {}
    for name, change in changes.items():
        action = change.get("action")
        path = local_path(root, name)
        if action == "add":
            if (
                change.get("baseSha256") is not None
                or path.exists()
                or name in base_files
            ):
                raise ArtifactError(f"New-file collision or invalid baseline: {name}")
        elif action in {"modify", "delete"}:
            digest = require_hash(change.get("baseSha256"), "baseSha256")
            if (
                base_files.get(name) != digest
                or sha256(read_file(root, name)) != digest
            ):
                raise ArtifactError(
                    f"Working-tree file drifted or lacks trusted baseline: {name}"
                )
        else:
            raise ArtifactError(f"Unsupported file action: {action}")
    if kind == "zip":
        files = zip_files(payload, max_bytes)
        expected = {
            name for name, change in changes.items() if change["action"] != "delete"
        }
        if set(files) != expected:
            raise ArtifactError("ZIP contents differ from declared changes")
    elif kind == "diff":
        check_diff(root, payload, changes)
    return {
        "identityVerified": True,
        "baselineVerified": baseline is not None,
        "format": kind,
        "changedFiles": names,
        "reviewClaim": review["kind"],
        "requiresCodexReview": True,
        "appliedToWorkspace": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--max-expanded-bytes", type=int, default=128 * 1024 * 1024)
    args = parser.parse_args()
    try:
        if args.max_expanded_bytes <= 0:
            raise ArtifactError("Expanded-size limit must be positive")
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        baseline = (
            json.loads(args.baseline.read_text(encoding="utf-8"))
            if args.baseline
            else None
        )
        result = verify_delivery(
            args.root.resolve(),
            args.artifact.read_bytes(),
            manifest,
            baseline,
            max_bytes=args.max_expanded_bytes,
        )
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (
        ArtifactError,
        OSError,
        ValueError,
        TypeError,
        KeyError,
        RuntimeError,
        zipfile.BadZipFile,
        subprocess.SubprocessError,
    ) as exc:
        print(f"Delivery rejected: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
