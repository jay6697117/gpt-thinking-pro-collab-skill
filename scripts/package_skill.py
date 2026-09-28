"""Build only the allowlisted installable skill, with a detached fingerprint."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/gpt-thinking-pro-collab"
sys.path.insert(0, str(SKILL / "scripts"))
from artifact_utils import (
    ArtifactError,
    deterministic_zip,
    json_bytes,
    read_file,
    sha256,
    unique_paths,
    write_outputs,
)


def package_files(
    skill: Path = SKILL, spec_path: Path = ROOT / "package-files.json"
) -> dict[str, bytes]:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    if (
        spec.get("schemaVersion") != 1
        or spec.get("skillName") != "gpt-thinking-pro-collab"
    ):
        raise ArtifactError("Unsupported package specification")
    names = unique_paths(spec["files"])
    actual = set()
    for path in skill.rglob("*"):
        if "__pycache__" in path.parts or path.name == ".DS_Store":
            continue
        if path.is_symlink():
            raise ArtifactError(f"Package contains a symlink: {path}")
        if path.is_file():
            actual.add(path.relative_to(skill).as_posix())
    if actual != set(names):
        raise ArtifactError(
            f"Package allowlist mismatch; unexpected={sorted(actual - set(names))}, missing={sorted(set(names) - actual)}"
        )
    return {name: read_file(skill, name) for name in names}


def fingerprint(files: dict[str, bytes]) -> dict:
    hashes = {name: sha256(data) for name, data in sorted(files.items())}
    return {
        "schemaVersion": 1,
        "skillName": "gpt-thinking-pro-collab",
        "sourceSha256": sha256(json_bytes(hashes)),
        "files": hashes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        files = package_files()
        payload = deterministic_zip(
            {f"gpt-thinking-pro-collab/{name}": data for name, data in files.items()}
        )
        manifest = fingerprint(files)
        manifest["packageSha256"] = sha256(payload)
        write_outputs(
            {
                args.output: payload,
                args.output.with_suffix(
                    args.output.suffix + ".manifest.json"
                ): json_bytes(manifest),
            }
        )
        print(
            json.dumps(
                {
                    "files": len(files),
                    "sourceSha256": manifest["sourceSha256"],
                    "packageSha256": manifest["packageSha256"],
                    "output": str(args.output),
                }
            )
        )
        return 0
    except (ArtifactError, OSError, ValueError, KeyError) as exc:
        print(f"Package rejected: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
