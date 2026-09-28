"""Build a deterministic allowlisted source archive or an inline baseline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from artifact_utils import (
    ArtifactError,
    deterministic_zip,
    git_identity,
    json_bytes,
    read_file,
    scan_secrets,
    sha256,
    unique_paths,
    write_outputs,
)


def build_context(
    root: Path, paths: list[str], *, archive: bool = True
) -> tuple[bytes | None, dict]:
    root = root.resolve()
    names = unique_paths(paths)
    if not names and archive:
        raise ArtifactError("The allowlist must contain at least one file")
    before = git_identity(root)
    files = {name: read_file(root, name) for name in names}
    for name, data in files.items():
        scan_secrets(name, data)
    if git_identity(root) != before:
        raise ArtifactError(
            "Git identity changed while collecting context; capture again"
        )
    for name, data in files.items():
        if read_file(root, name) != data:
            raise ArtifactError(f"File changed while collecting context: {name}")
    payload = deterministic_zip(files) if archive else None
    manifest = {
        "schemaVersion": 1,
        "baseCommit": before[0],
        "dirty": before[1],
        "archiveSha256": sha256(payload) if payload is not None else None,
        "archiveBytes": len(payload) if payload is not None else None,
        "files": [
            {"path": name, "sha256": sha256(data), "bytes": len(data)}
            for name, data in sorted(files.items())
        ],
        "scan": {
            "scanner": "builtin-patterns-v1",
            "status": "no_match",
            "guaranteesSecretFree": False,
        },
    }
    return payload, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--paths-file",
        type=Path,
        required=True,
        help="One exact relative file path per line",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--manifest-only",
        action="store_true",
        help="Record a baseline for inline text; create no ZIP",
    )
    args = parser.parse_args()
    try:
        paths = [
            line
            for line in args.paths_file.read_text(encoding="utf-8").splitlines()
            if line
        ]
        payload, manifest = build_context(
            args.root, paths, archive=not args.manifest_only
        )
        if args.manifest_only:
            outputs = {args.output: json_bytes(manifest)}
        else:
            outputs = {
                args.output: payload,
                args.output.with_suffix(
                    args.output.suffix + ".manifest.json"
                ): json_bytes(manifest),
            }
        source_paths = {(args.root / name).resolve() for name in paths}
        if any(path.resolve() in source_paths for path in outputs):
            raise ArtifactError("Outputs must not overwrite a source file")
        write_outputs(outputs)
        print(
            json.dumps(
                {
                    "files": len(paths),
                    "archiveSha256": manifest["archiveSha256"],
                    "output": str(args.output),
                    "scan": manifest["scan"],
                },
                ensure_ascii=False,
            )
        )
        return 0
    except (ArtifactError, OSError, ValueError) as exc:
        print(f"Context rejected: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
