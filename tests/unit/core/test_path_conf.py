"""backend.core.path_conf — 关键路径常量。"""

from pathlib import Path

import backend.core.path_conf as pc


def test_base_path_matches_path_conf_file_location() -> None:
    assert pc.BASE_PATH == Path(pc.__file__).resolve().parent.parent
    assert (pc.BASE_PATH / "core" / "path_conf.py").is_file()


def test_upload_dir_under_static_dir() -> None:
    assert pc.UPLOAD_DIR == pc.STATIC_DIR / "upload"


def test_reload_lock_under_base_path() -> None:
    assert pc.RELOAD_LOCK_FILE == pc.BASE_PATH / ".reload.lock"
