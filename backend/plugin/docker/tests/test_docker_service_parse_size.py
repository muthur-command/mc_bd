"""DockerService._parse_size 纯函数行为（不触达真实 Docker）。"""

from __future__ import annotations

import pytest

from backend.plugin.docker.service.docker_service import DockerService


@pytest.fixture
def svc() -> DockerService:
    return DockerService()


@pytest.mark.parametrize(
    ('raw', 'expected_bytes'),
    [
        ('', 0),
        ('0B', 0),
        ('  0b  ', 0),
        ('100', 100),
        ('1B', 1),
        ('2KB', 2 * 1024),
        ('1MB', 1024**2),
        ('1.5GB', int(1.5 * 1024**3)),
        ('1TB', 1024**4),
        ('not-a-size', 0),
    ],
)
def test_parse_size_cases(svc: DockerService, raw: str, expected_bytes: int) -> None:
    assert svc._parse_size(raw) == expected_bytes


def test_parse_size_strips_and_uppercases_unit(svc: DockerService) -> None:
    assert svc._parse_size('  10 mb ') == 10 * 1024**2
