"""与仓库 / backend 相关的路径（供 conftest、集成测试等复用）。"""

from __future__ import annotations

from pathlib import Path


def tests_dir() -> Path:
    """`tests/` 目录（本文件位于 `tests/helpers/`）。"""
    return Path(__file__).resolve().parents[1]


def backend_dotenv_path() -> Path:
    """`backend/.env`，用于收集阶段提示等。"""
    return tests_dir().parent / "backend" / ".env"
