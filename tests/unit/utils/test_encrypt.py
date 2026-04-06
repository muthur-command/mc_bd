"""backend.utils.encrypt — AES 加解密往返。"""

from backend.utils.encrypt import AESCipher


def test_aes_encrypt_decrypt_roundtrip(aes_key_hex_64_chars: str) -> None:
    cipher = AESCipher(aes_key_hex_64_chars)
    plain = 'hello-mc-bd'
    blob = cipher.encrypt(plain)
    assert cipher.decrypt(blob) == plain


def test_aes_decrypt_accepts_hex_string(aes_key_hex_64_chars: str) -> None:
    cipher = AESCipher(aes_key_hex_64_chars)
    blob = cipher.encrypt('x')
    as_hex = blob.hex()
    assert cipher.decrypt(as_hex) == 'x'
