"""Compare independent workflow decisions with the maintained scenario oracle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def compare_results(results: list[dict], expected: dict[str, str]) -> list[str]:
    failures = []
    seen = set()
    for result in results:
        identity = result.get("id")
        if identity in seen or identity not in expected:
            failures.append(f"Duplicate or unknown case: {identity}")
        seen.add(identity)
        if result.get("decision") != expected.get(identity):
            failures.append(
                f"{identity}: expected {expected.get(identity)}, received {result.get('decision')}"
            )
        if not isinstance(result.get("reason"), str) or not result["reason"].strip():
            failures.append(f"{identity}: missing evaluation reason")
    failures.extend(
        f"Missing case: {identity}" for identity in sorted(set(expected) - seen)
    )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    args = parser.parse_args()
    expected = json.loads(
        (ROOT / "tests/scenarios/expected.json").read_text(encoding="utf-8")
    )
    failures = compare_results(
        json.loads(args.results.read_text(encoding="utf-8")), expected
    )
    print(
        json.dumps(
            {"cases": len(expected), "failures": failures}, ensure_ascii=False, indent=2
        )
    )
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
