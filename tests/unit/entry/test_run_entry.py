"""backend.run — `__main__` 块调用 uvicorn.run。"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

_RUN_PY = Path(__file__).resolve().parents[3] / 'backend' / 'run.py'


@pytest.mark.skipif(not _RUN_PY.is_file(), reason='run.py missing')
def test_run_main_invokes_uvicorn_with_expected_target() -> None:
    import runpy

    with patch('uvicorn.run') as ur:
        runpy.run_path(str(_RUN_PY), run_name='__main__')

    ur.assert_called_once()
    kwargs = ur.call_args.kwargs
    assert kwargs.get('app') == 'backend.main:app'
    assert kwargs.get('host') == '127.0.0.1'
    assert kwargs.get('port') == 8000
    assert kwargs.get('reload') is True
