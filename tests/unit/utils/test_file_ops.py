"""backend.utils.file_ops — 文件名、校验与上传。"""

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from fastapi import UploadFile

from backend.common.exception import errors
from backend.core.conf import settings
from backend.utils.file_ops import build_filename, upload_file, upload_file_verify


def test_build_filename_inserts_timestamp_before_extension() -> None:
    f = MagicMock(spec=UploadFile)
    f.filename = 'photo.jpg'
    mock_now = MagicMock()
    mock_now.timestamp.return_value = 1_700_000_000
    with patch('backend.utils.file_ops.timezone.now', return_value=mock_now):
        name = build_filename(f)
    assert name == 'photo_1700000000.jpg'


def test_upload_file_verify_empty_filename() -> None:
    f = MagicMock(spec=UploadFile)
    f.filename = ''
    with pytest.raises(errors.RequestError) as ei:
        upload_file_verify(f)
    assert ei.value.msg == '未知的文件类型'


def test_upload_file_verify_arbitrary_ext_no_raise() -> None:
    """非 image/video 字面扩展名时当前实现不校验白名单。"""
    f = MagicMock(spec=UploadFile)
    f.filename = 'doc.pdf'
    f.size = 100
    upload_file_verify(f)


def test_upload_file_verify_image_ext_not_in_whitelist() -> None:
    f = MagicMock(spec=UploadFile)
    f.filename = 'x.image'
    f.size = 100
    with patch.object(settings, 'UPLOAD_IMAGE_EXT_INCLUDE', ['jpg']):
        with pytest.raises(errors.RequestError) as ei:
            upload_file_verify(f)
        assert ei.value.msg == '此图片格式暂不支持'


def test_upload_file_verify_image_too_large() -> None:
    f = MagicMock(spec=UploadFile)
    f.filename = 'x.image'
    f.size = 999
    with (
        patch.object(settings, 'UPLOAD_IMAGE_EXT_INCLUDE', ['image']),
        patch.object(settings, 'UPLOAD_IMAGE_SIZE_MAX', 10),
    ):
        with pytest.raises(errors.RequestError) as ei:
            upload_file_verify(f)
        assert ei.value.msg == '图片超出最大限制，请重新选择'


@pytest.mark.asyncio
async def test_upload_file_writes_bytes(tmp_path) -> None:
    f = UploadFile(filename='t.txt', file=BytesIO(b'hello'))
    mock_now = MagicMock()
    mock_now.timestamp.return_value = 99
    with (
        patch('backend.utils.file_ops.UPLOAD_DIR', tmp_path),
        patch('backend.utils.file_ops.timezone.now', return_value=mock_now),
    ):
        name = await upload_file(f)
    assert name.endswith('.txt')
    assert '99' in name
    saved = tmp_path / name
    assert saved.read_bytes() == b'hello'
