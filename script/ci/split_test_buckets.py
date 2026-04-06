#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: split_test_buckets.py <N>", file=sys.stderr)
        raise SystemExit(2)
    n = max(1, int(sys.argv[1]))
    root = Path(__file__).resolve().parents[2]

    candidates: list[Path] = []
    tests = root / "tests"
    if tests.is_dir():
        for p in sorted(tests.iterdir()):
            if p.is_dir() and p.name not in {"__pycache__"}:
                candidates.append(p)
    plugin = root / "backend" / "plugin"
    if plugin.is_dir():
        candidates.append(plugin)
    script_dir = root / "script"
    if any(script_dir.glob("*.py")):
        candidates.append(script_dir)

    if not candidates:
        print(".")
        return

    if len(candidates) < n:
        n = len(candidates)

    buckets: list[list[Path]] = [[] for _ in range(n)]
    for i, p in enumerate(candidates):
        buckets[i % n].append(p)

    fallback = root / "tests" / "unit"
    for bucket in buckets:
        if not bucket:
            bucket.append(fallback)

    for bucket in buckets:
        print(" ".join(str(p.relative_to(root)) for p in bucket))


if __name__ == "__main__":
    main()
