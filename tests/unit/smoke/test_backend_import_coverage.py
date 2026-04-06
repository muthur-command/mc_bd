"""批量验证 backend 下模块可导入（排除会执行副作用的入口脚本）。"""

from __future__ import annotations

import importlib

from pathlib import Path

import pytest


def _iter_backend_modules() -> list[str]:
    # .../tests/unit/smoke/this_file.py → parents[3] 为 mc_bd 仓库根
    mc_bd = Path(__file__).resolve().parents[3]
    backend = mc_bd / 'backend'
    skip_names = frozenset({'main.py', 'run.py', 'cli.py'})
    out: list[str] = []
    for p in sorted(backend.rglob('*.py')):
        if '__pycache__' in p.parts or 'tests' in p.parts:
            continue
        if p.name in skip_names:
            continue
        if p.parts[-2:] == ('alembic', 'env.py'):
            continue
        rel = p.relative_to(backend).with_suffix('')
        parts = rel.parts
        if parts[-1] == '__init__':
            parts = parts[:-1]
        if not parts:
            continue
        out.append('backend.' + '.'.join(parts))
    return out


@pytest.mark.slow
def test_all_backend_modules_importable() -> None:
    failures: list[tuple[str, str]] = []
    for mod in _iter_backend_modules():
        try:
            importlib.import_module(mod)
        except Exception as e:
            failures.append((mod, f'{type(e).__name__}: {e}'))
    assert not failures, '导入失败:\n' + '\n'.join(f'  {m}: {err}' for m, err in failures)
