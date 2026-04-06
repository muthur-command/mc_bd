#!/usr/bin/env python3
from __future__ import annotations

import sys

from pathlib import Path


def _pytest_collectable_under(path: Path) -> bool:
    """Whether pytest will find tests under this directory (default discovery patterns)."""
    if not path.is_dir():
        return path.is_file() and path.suffix == '.py'
    return any(path.rglob('test_*.py')) or any(path.rglob('*_test.py'))


def _collect_candidate_dirs(root: Path) -> list[Path]:
    """Paths to pass to pytest (dirs with tests, or explicit .py files such as script/version_bump.py)."""
    candidates: list[Path] = []
    tests = root / 'tests'
    if tests.is_dir():
        # 与 CI `pytest -m "not integration"` 一致，否则该桶会 0 收集 → exit 5
        skip_test_roots = frozenset({'integration'})
        for p in sorted(tests.iterdir()):
            if not p.is_dir() or p.name == '__pycache__' or p.name in skip_test_roots:
                continue
            if _pytest_collectable_under(p):
                candidates.append(p)
    plugin = root / 'backend' / 'plugin'
    if plugin.is_dir():
        candidates.append(plugin)
    # `pytest script/` does not collect `version_bump.py` (not test_*.py); pass files explicitly.
    script_dir = root / 'script'
    vb = script_dir / 'version_bump.py'
    if vb.is_file():
        candidates.append(vb)
    return candidates


def main() -> None:
    if len(sys.argv) < 2:
        print('usage: split_test_buckets.py <N>', file=sys.stderr)
        raise SystemExit(2)
    n = max(1, int(sys.argv[1]))
    root = Path(__file__).resolve().parents[2]
    candidates = _collect_candidate_dirs(root)

    if not candidates:
        print('.')
        return

    if len(candidates) < n:
        n = len(candidates)

    buckets: list[list[Path]] = [[] for _ in range(n)]
    for i, p in enumerate(candidates):
        buckets[i % n].append(p)

    fallback = root / 'tests' / 'unit'
    for bucket in buckets:
        if not bucket:
            bucket.append(fallback)

    for bucket in buckets:
        print(' '.join(str(p.relative_to(root)) for p in bucket))


if __name__ == '__main__':
    main()
