"""加解密等用固定密钥（避免各测试文件重复定义）。"""

from __future__ import annotations

import pytest


@pytest.fixture
def aes_key_hex_64_chars() -> str:
    """32 字节 AES 密钥的 64 位十六进制字符串表示。"""
    return '0' * 64
