"""backend.cli — run()、Celery 子进程、main() 入口。"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def test_run_invokes_granian_serve() -> None:
    import backend.cli as cli_mod

    server = MagicMock()
    with patch.object(cli_mod, "console"):
        with patch("backend.cli.granian.Granian") as GranianCls:
            GranianCls.return_value = server
            cli_mod.run(host="127.0.0.1", port=9001, reload=True, workers=2)

            GranianCls.assert_called_once()
            kwargs = GranianCls.call_args.kwargs
            assert kwargs["target"] == "backend.main:app"
            assert kwargs["address"] == "127.0.0.1"
            assert kwargs["port"] == 9001
            assert kwargs["reload"] is False
            assert kwargs["workers"] == 2
            server.serve.assert_called_once()


def test_run_celery_worker_calls_subprocess() -> None:
    import backend.cli as cli_mod

    with patch.object(cli_mod.subprocess, "run") as sp:
        cli_mod.run_celery_worker("debug")
    sp.assert_called_once_with(
        ["celery", "-A", "backend.app.task.celery", "worker", "-l", "debug", "-P", "gevent"]
    )


def test_run_celery_beat_calls_subprocess() -> None:
    import backend.cli as cli_mod

    with patch.object(cli_mod.subprocess, "run") as sp:
        cli_mod.run_celery_beat("info")
    sp.assert_called_once_with(
        ["celery", "-A", "backend.app.task.celery", "beat", "-l", "info"]
    )


def test_run_celery_flower_calls_subprocess() -> None:
    import backend.cli as cli_mod

    with patch.object(cli_mod.subprocess, "run") as sp:
        cli_mod.run_celery_flower(9555, "u:p")
    sp.assert_called_once_with(
        [
            "celery",
            "-A",
            "backend.app.task.celery",
            "flower",
            "--port=9555",
            "--basic-auth=u:p",
        ]
    )


def test_cli_main_runs_invoke_async() -> None:
    import backend.cli as cli_mod

    with patch.object(cli_mod.asyncio, "run") as arun:
        with patch.object(cli_mod.cappa, "invoke_async", new_callable=AsyncMock, return_value=None):
            cli_mod.main()
    arun.assert_called_once()
    inner = arun.call_args[0][0]
    assert asyncio.iscoroutine(inner)
    inner.close()


def test_run_command_dataclass_delegates_to_run() -> None:
    import backend.cli as cli_mod

    with patch.object(cli_mod, "run") as r:
        cli_mod.Run(host="0.0.0.0", port=7000, no_reload=True, workers=3)()
    r.assert_called_once_with(host="0.0.0.0", port=7000, reload=True, workers=3)
