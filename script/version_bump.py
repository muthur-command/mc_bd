#!/usr/bin/env python3
"""Bump MUTHUR Command backend version (const + pyproject; optional CI workflow)."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from packaging.version import Version

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent

CONST_PATH = _REPO_ROOT / 'backend' / 'const.py'
PYPROJECT_PATH = _REPO_ROOT / 'pyproject.toml'
CI_WORKFLOW_PATH = _REPO_ROOT / '.github' / 'workflows' / 'ci.yaml'


def _utcnow_compact() -> str:
    return datetime.now(timezone.utc).strftime('%Y%m%d%H%M')


def _bump_release(release: tuple[int, int, int], bump_type: str) -> tuple[int, int, int]:
    """Bump a release tuple consisting of 3 numbers."""
    major, minor, patch = release

    if bump_type == 'patch':
        patch += 1
    elif bump_type == 'minor':
        minor += 1
        patch = 0

    return major, minor, patch


def _get_dev_change(dev: int) -> tuple[str, int]:
    """Return dev segment for packaging's internal _version._replace (not plain int)."""
    return ('dev', dev)


def bump_version(  # noqa: C901
    version: Version, bump_type: str, *, nightly_version: str | None = None
) -> Version:
    """Return a new version given a current version and action."""
    to_change = {}

    if bump_type == 'minor':
        to_change['dev'] = None
        to_change['pre'] = None

        if not version.is_prerelease or version.release[2] != 0:
            to_change['release'] = _bump_release(version.release, 'minor')

    elif bump_type == 'patch':
        to_change['dev'] = None
        to_change['pre'] = None

        if not version.is_prerelease:
            to_change['release'] = _bump_release(version.release, 'patch')

    elif bump_type == 'dev':
        if version.is_devrelease:
            to_change['dev'] = _get_dev_change(version.dev + 1)
        else:
            to_change['dev'] = _get_dev_change(0)
            to_change['pre'] = None
            to_change['release'] = _bump_release(version.release, 'minor')

    elif bump_type == 'beta':
        if version.is_devrelease:
            to_change['dev'] = None
            to_change['pre'] = ('b', 0)

        elif version.is_prerelease:
            if version.pre[0] == 'a':
                to_change['pre'] = ('b', 0)
            if version.pre[0] == 'b':
                to_change['pre'] = ('b', version.pre[1] + 1)
            else:
                to_change['pre'] = ('b', 0)
                to_change['release'] = _bump_release(version.release, 'patch')

        else:
            to_change['release'] = _bump_release(version.release, 'patch')
            to_change['pre'] = ('b', 0)

    elif bump_type == 'nightly':
        if not version.is_devrelease:
            raise ValueError('Can only be run on dev release')

        new_dev = _utcnow_compact()
        if nightly_version:
            new_version = Version(nightly_version)
            if new_version.release != version.release:
                raise ValueError('Nightly version must have the same release version')
            if not new_version.is_devrelease:
                raise ValueError('Nightly version must be a dev version')
            new_dev = new_version.dev

        if not isinstance(new_dev, int):
            new_dev = int(new_dev)
        to_change['dev'] = _get_dev_change(new_dev)

    else:
        raise ValueError(f'Unsupported type: {bump_type}')

    # Use internal replace (works on Python <3.13 where stdlib copy.replace is absent).
    temp = Version('0')
    temp._version = version._version._replace(**to_change)
    return Version(str(temp))


def read_version() -> Version:
    """Parse current version from backend/const.py (no package import)."""
    text = CONST_PATH.read_text(encoding='utf8')
    major_m = re.search(r'^MAJOR_VERSION:\s*Final\s*=\s*(\d+)\s*$', text, re.MULTILINE)
    minor_m = re.search(r'^MINOR_VERSION:\s*Final\s*=\s*(\d+)\s*$', text, re.MULTILINE)
    patch_m = re.search(r'^PATCH_VERSION:\s*Final\s*=\s*"([^"]*)"', text, re.MULTILINE)
    if not major_m or not minor_m or not patch_m:
        msg = f'Could not parse MAJOR/MINOR/PATCH from {CONST_PATH}'
        raise RuntimeError(msg)
    return Version(f'{major_m.group(1)}.{minor_m.group(1)}.{patch_m.group(1)}')


def write_version(version: Version) -> None:
    """Update backend/const.py with new version."""
    content = CONST_PATH.read_text(encoding='utf8')

    major, minor, patch = str(version).split('.', 2)

    content = re.sub(
        r'MAJOR_VERSION: Final = .*\n',
        f'MAJOR_VERSION: Final = {major}\n',
        content,
        count=1,
    )
    content = re.sub(
        r'MINOR_VERSION: Final = .*\n',
        f'MINOR_VERSION: Final = {minor}\n',
        content,
        count=1,
    )
    content = re.sub(
        r'PATCH_VERSION: Final = .*\n',
        f'PATCH_VERSION: Final = "{patch}"\n',
        content,
        count=1,
    )

    CONST_PATH.write_text(content, encoding='utf8')


def write_version_metadata(version: Version) -> None:
    """Update pyproject.toml [project] version."""
    content = PYPROJECT_PATH.read_text(encoding='utf8')

    content = re.sub(
        r'(version\W+=\W).+\n',
        f'\\g<1>"{version}"\n',
        content,
        count=1,
    )

    PYPROJECT_PATH.write_text(content, encoding='utf8')


def write_ci_workflow(version: Version) -> None:
    """Update CI workflow MC_SHORT_VERSION when .github/workflows/ci.yaml exists."""
    if not CI_WORKFLOW_PATH.is_file():
        return

    content = CI_WORKFLOW_PATH.read_text(encoding='utf8')

    short_version = '.'.join(str(version).split('.', maxsplit=2)[:2])
    content = re.sub(
        r'(\n\W+MC_SHORT_VERSION: )"[^"]+"\n',
        rf'\g<1>"{short_version}"\n',
        content,
        count=1,
    )

    CI_WORKFLOW_PATH.write_text(content, encoding='utf8')


def main() -> None:
    """Execute script (run from mc_bd repo root: uv run python script/version_bump.py …)."""
    parser = argparse.ArgumentParser(description='Bump MUTHUR Command backend version')
    parser.add_argument(
        'type',
        help='The type of bump to apply.',
        choices=['beta', 'dev', 'patch', 'minor', 'nightly'],
    )
    parser.add_argument('--commit', action='store_true', help='Create a version bump commit.')
    parser.add_argument('--set-nightly-version', help='Set the nightly version to', type=str)

    arguments = parser.parse_args()

    if arguments.set_nightly_version and arguments.type != 'nightly':
        parser.error('--set-nightly-version requires type set to nightly.')

    if arguments.commit and subprocess.run(['git', 'diff', '--quiet'], check=False, cwd=_REPO_ROOT).returncode == 1:
        print('Cannot use --commit because git is dirty.')
        sys.exit(1)

    os_cwd = Path.cwd()
    if os_cwd.resolve() != _REPO_ROOT.resolve():
        print(f'Run this script from the repository root: {_REPO_ROOT}', file=sys.stderr)
        sys.exit(1)

    current = read_version()
    bumped = bump_version(current, arguments.type, nightly_version=arguments.set_nightly_version)
    assert bumped > current, 'BUG! New version is not newer than old version'

    write_version(bumped)
    write_version_metadata(bumped)
    write_ci_workflow(bumped)
    print(bumped)

    if not arguments.commit:
        return

    subprocess.run(
        ['git', 'commit', '-nam', f'Bump version to {bumped}'],
        check=True,
        cwd=_REPO_ROOT,
    )


def test_bump_version(monkeypatch: Any) -> None:
    """Run with: pytest script/version_bump.py -q (from mc_bd root)."""
    import pytest

    assert bump_version(Version('0.56.0'), 'beta') == Version('0.56.1b0')
    assert bump_version(Version('0.56.0b3'), 'beta') == Version('0.56.0b4')
    assert bump_version(Version('0.56.0.dev0'), 'beta') == Version('0.56.0b0')

    assert bump_version(Version('0.56.3'), 'dev') == Version('0.57.0.dev0')
    assert bump_version(Version('0.56.0b3'), 'dev') == Version('0.57.0.dev0')
    assert bump_version(Version('0.56.0.dev0'), 'dev') == Version('0.56.0.dev1')

    assert bump_version(Version('0.56.3'), 'patch') == Version('0.56.4')
    assert bump_version(Version('0.56.3.b3'), 'patch') == Version('0.56.3')
    assert bump_version(Version('0.56.0.dev0'), 'patch') == Version('0.56.0')

    assert bump_version(Version('0.56.0'), 'minor') == Version('0.57.0')
    assert bump_version(Version('0.56.3'), 'minor') == Version('0.57.0')
    assert bump_version(Version('0.56.0.b3'), 'minor') == Version('0.56.0')
    assert bump_version(Version('0.56.3.b3'), 'minor') == Version('0.57.0')
    assert bump_version(Version('0.56.0.dev0'), 'minor') == Version('0.56.0')
    assert bump_version(Version('0.56.2.dev0'), 'minor') == Version('0.57.0')

    mod = sys.modules[__name__]
    monkeypatch.setattr(mod, '_utcnow_compact', lambda: '201904241254')
    assert bump_version(Version('0.56.0.dev0'), 'nightly') == Version('0.56.0.dev201904241254')
    assert bump_version(
        Version('2024.4.0.dev20240327'),
        'nightly',
        nightly_version='2024.4.0.dev202403271315',
    ) == Version('2024.4.0.dev202403271315')
    with pytest.raises(ValueError, match='Can only be run on dev release'):
        bump_version(Version('0.56.0'), 'nightly')
    with pytest.raises(ValueError, match='Nightly version must have the same release version'):
        bump_version(
            Version('0.56.0.dev0'),
            'nightly',
            nightly_version='2024.4.0.dev202403271315',
        )
    with pytest.raises(ValueError, match='Nightly version must be a dev version'):
        bump_version(Version('0.56.0.dev0'), 'nightly', nightly_version='0.56.0')


if __name__ == '__main__':
    main()
