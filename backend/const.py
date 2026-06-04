"""Backend public constants (version, etc.)."""

from __future__ import annotations

from typing import Final

MAJOR_VERSION: Final = 2026
MINOR_VERSION: Final = 6
PATCH_VERSION: Final = '1'
__short_version__: Final = f'{MAJOR_VERSION}.{MINOR_VERSION}'
__version__: Final = f'{__short_version__}.{PATCH_VERSION}'
