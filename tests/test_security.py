from pathlib import Path

import pytest

from developer_toolbox_mcp.security import SecurityError, resolve_safe_path, validate_text_file


def test_resolve_safe_path_accepts_workspace_file(tmp_path: Path) -> None:
    target = resolve_safe_path(tmp_path, "src/example.py")
    assert target == (tmp_path / "src/example.py").resolve()


def test_resolve_safe_path_blocks_parent_traversal(tmp_path: Path) -> None:
    with pytest.raises(SecurityError):
        resolve_safe_path(tmp_path, "../secret.txt")


def test_validate_text_file_blocks_env_file(tmp_path: Path) -> None:
    secret = tmp_path / ".env"
    secret.write_text("TOKEN=secret", encoding="utf-8")
    with pytest.raises(SecurityError):
        validate_text_file(secret, 10_000)


def test_validate_text_file_blocks_large_file(tmp_path: Path) -> None:
    large = tmp_path / "large.txt"
    large.write_text("x" * 101, encoding="utf-8")
    with pytest.raises(SecurityError):
        validate_text_file(large, 100)
