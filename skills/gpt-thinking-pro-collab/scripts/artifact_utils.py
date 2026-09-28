"""Shared local artifact checks; never execute delivered code."""

from __future__ import annotations

import hashlib
import io
import json
import re
import subprocess
import zipfile
from pathlib import Path, PurePosixPath

BLOCKED_PARTS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "vendor",
    "dist",
    "build",
    "__pycache__",
    ".cache",
    ".next",
    ".codex",
    ".ssh",
    "browser-state",
    "local storage",
    "session storage",
    "cookies",
}
BLOCKED_SUFFIXES = {
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".crt",
    ".cer",
    ".db",
    ".sqlite",
    ".sqlite3",
}
SECRET_PATTERNS = {
    "private_key": re.compile(rb"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----"),
    "aws_access_key": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "service_token": re.compile(
        rb"\b(?:sk-(?:proj-)?[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,})\b"
    ),
    "assigned_secret": re.compile(
        rb"""(?i)\b(?:api[_-]?key|access[_-]?token|password|secret(?:[_-]?key)?)\b["']?\s*[:=]\s*["']([^"'\r\n]{8,})["']"""
    ),
}
PLACEHOLDERS = {
    "example",
    "placeholder",
    "changeme",
    "redacted",
    "your_api_key",
    "not-a-secret",
}


class ArtifactError(ValueError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode()


def relative_path(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ArtifactError("Expected a portable relative file path")
    if any(ord(char) < 32 for char in value):
        raise ArtifactError("Control characters are not allowed in paths")
    parts = value.split("/")
    if value.startswith("/") or any(part in {"", ".", ".."} for part in parts):
        raise ArtifactError(f"Unsafe path: {value}")
    path = PurePosixPath(value)
    if any(
        part.lower() in BLOCKED_PARTS or part.lower().startswith(".env")
        for part in parts
    ):
        raise ArtifactError(f"Excluded path: {value}")
    if path.suffix.lower() in BLOCKED_SUFFIXES or path.name.lower() in {
        "credentials",
        "credentials.json",
        "id_rsa",
        "id_ed25519",
    }:
        raise ArtifactError(f"Excluded credential or data file: {value}")
    return path.as_posix()


def local_path(root: Path, value: str) -> Path:
    name = relative_path(value)
    root = root.resolve()
    current = root
    parts = PurePosixPath(name).parts
    for index, part in enumerate(parts):
        current /= part
        if current.is_symlink():
            raise ArtifactError(f"Symlinks are not allowed: {name}")
        if index < len(parts) - 1 and current.exists() and not current.is_dir():
            raise ArtifactError(f"Parent is not a directory: {name}")
    if not current.resolve().is_relative_to(root):
        raise ArtifactError(f"Path escapes root: {name}")
    return current


def unique_paths(values: list[str]) -> list[str]:
    names = [relative_path(value) for value in values]
    folded = {name.casefold() for name in names}
    if len(folded) != len(names):
        raise ArtifactError("Duplicate or case-colliding paths")
    for name in names:
        if any(
            parent.as_posix().casefold() in folded
            for parent in PurePosixPath(name).parents
        ):
            raise ArtifactError(f"File/directory path conflict: {name}")
    return sorted(names)


def read_file(root: Path, name: str) -> bytes:
    path = local_path(root, name)
    if not path.is_file():
        raise ArtifactError(f"Expected a regular file: {name}")
    return path.read_bytes()


def scan_secrets(name: str, data: bytes) -> None:
    for rule, pattern in SECRET_PATTERNS.items():
        for match in pattern.finditer(data):
            if rule == "assigned_secret":
                value = match.group(1).decode("utf-8", errors="replace")
                if value.lower() in PLACEHOLDERS or value.startswith(("${", "{{", "<")):
                    continue
            raise ArtifactError(f"Possible secret in {name} ({rule}); value omitted")


def git_identity(root: Path) -> tuple[str | None, bool | None]:
    if not root.is_dir():
        raise ArtifactError("The project root must be an existing directory")
    probe = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if probe.returncode:
        return None, None
    if Path(probe.stdout.strip()).resolve() != root.resolve():
        raise ArtifactError("Use the Git repository root as --root")
    head = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
        capture_output=True,
        text=True,
    )
    status = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )
    return head.stdout.strip() if head.returncode == 0 else None, bool(status.stdout)


def deterministic_zip(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(
        buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data, compresslevel=9)
    return buffer.getvalue()


def write_outputs(outputs: dict[Path, bytes]) -> None:
    resolved = [path.resolve() for path in outputs]
    if len(set(resolved)) != len(resolved):
        raise ArtifactError("Output paths must be distinct")
    for path, data in outputs.items():
        if path.is_symlink() or (
            path.exists() and (not path.is_file() or path.read_bytes() != data)
        ):
            raise ArtifactError(f"Refusing to overwrite a different output: {path}")
        if not path.parent.is_dir():
            raise ArtifactError(f"Output parent does not exist: {path.parent}")
    for path, data in outputs.items():
        if not path.exists():
            with path.open("xb") as stream:
                stream.write(data)
