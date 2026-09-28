"""Read-only content comparison of source, an installation, and public snapshots."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from package_skill import fingerprint, package_files

REPOSITORY = "jay6697117/gpt-thinking-pro-collab-skill"
SLUG = "gpt-thinking-pro-collab"


def compare_files(expected: dict[str, bytes], actual: dict[str, bytes]) -> dict:
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    changed = sorted(
        name
        for name in expected.keys() & actual.keys()
        if expected[name] != actual[name]
    )
    return {
        "matches": not (missing or extra or changed),
        "missing": missing,
        "extra": extra,
        "changed": changed,
    }


def installed_files(directory: Path) -> dict[str, bytes]:
    directory = directory.resolve()
    if not directory.is_dir():
        raise ValueError("Installed directory does not exist")
    result = {}
    for path in directory.rglob("*"):
        if "__pycache__" in path.parts or path.name == ".DS_Store":
            continue
        if path.is_symlink():
            raise ValueError("Unexpected symlink inside the installed skill")
        if path.is_file():
            result[path.relative_to(directory).as_posix()] = path.read_bytes()
    return result


def fetch(url: str) -> bytes:
    request = urllib.request.Request(
        url, headers={"User-Agent": "gpt-collab-distribution-check/1"}
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read()


def github_files(ref: str) -> dict[str, bytes]:
    api = f"https://api.github.com/repos/{REPOSITORY}"
    commit = json.loads(fetch(f"{api}/commits/{urllib.parse.quote(ref, safe='')}"))
    revision = commit.get("sha") if isinstance(commit, dict) else None
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40,64}", revision):
        raise ValueError("GitHub did not resolve the requested commit")
    tree = json.loads(fetch(f"{api}/git/trees/{revision}?recursive=1"))
    if (
        not isinstance(tree, dict)
        or tree.get("truncated") is not False
        or not isinstance(tree.get("tree"), list)
    ):
        raise ValueError("GitHub returned an incomplete directory tree")
    prefix = f"skills/{SLUG}/"
    names = []
    for entry in tree["tree"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise ValueError("Malformed GitHub tree entry")
        if not entry["path"].startswith(prefix) or entry.get("type") == "tree":
            continue
        if entry.get("type") != "blob" or entry.get("mode") not in {"100644", "100755"}:
            raise ValueError("The published skill contains a non-regular file")
        names.append(entry["path"][len(prefix) :])
    if len(names) != len(set(names)):
        raise ValueError("Duplicate GitHub tree entry")
    base = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{prefix}"

    def retrieve(name: str) -> tuple[str, bytes]:
        return name, fetch(base + urllib.parse.quote(name, safe="/"))

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        return dict(executor.map(retrieve, names))


def catalog_files(payload: bytes) -> dict[str, bytes]:
    data = json.loads(payload)
    entries = data.get("files")
    if not isinstance(entries, list):
        raise ValueError("Catalog response has no files array")
    result = {}
    prefix = f"skills/{SLUG}/"
    for entry in entries:
        path, content = entry["path"], entry["contents"]
        if not isinstance(path, str) or not isinstance(content, str):
            raise ValueError("Malformed catalog file")
        if path.startswith(prefix):
            path = path[len(prefix) :]
        elif path.startswith(f"{SLUG}/"):
            path = path[len(SLUG) + 1 :]
        if path in result:
            raise ValueError("Duplicate catalog file path")
        result[path] = content.encode("utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installed", type=Path)
    parser.add_argument(
        "--github-ref", help="Public branch, tag, or commit to compare; never publishes"
    )
    parser.add_argument("--catalog", action="store_true")
    args = parser.parse_args()
    expected = package_files()
    results = {"source": fingerprint(expected), "checks": {}}
    checks = results["checks"]
    if args.installed:
        try:
            checks["installed"] = compare_files(
                expected, installed_files(args.installed)
            )
        except (OSError, ValueError) as exc:
            checks["installed"] = {"matches": False, "error": str(exc)}
    if args.github_ref:
        try:
            checks["github"] = compare_files(expected, github_files(args.github_ref))
        except (OSError, urllib.error.URLError, ValueError) as exc:
            checks["github"] = {
                "matches": False,
                "error": str(exc),
                "note": "Unpublished local changes are expected to differ.",
            }
    if args.catalog:
        base = f"https://www.skills.sh/{REPOSITORY}/{SLUG}"
        try:
            files = catalog_files(
                fetch(f"https://www.skills.sh/api/download/{REPOSITORY}/{SLUG}")
            )
            page = fetch(base).decode("utf-8")
            comparison = compare_files(expected, files)
            comparison["pageHasCurrentModel"] = "GPT-6 Astra Pro" in page
            comparison["matches"] = (
                comparison["matches"] and comparison["pageHasCurrentModel"]
            )
            checks["catalog"] = comparison
        except (OSError, urllib.error.URLError, ValueError, KeyError, TypeError) as exc:
            checks["catalog"] = {"matches": False, "error": str(exc)}
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if all(check["matches"] for check in checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
