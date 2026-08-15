from __future__ import annotations

from pathlib import Path


class SecurityError(ValueError):
    """Raised when a requested operation violates a toolbox security boundary."""


def resolve_safe_path(root: Path, requested_path: str) -> Path:
    """Resolve a user-controlled path while preventing escape from the configured root."""
    root = root.expanduser().resolve()
    candidate = (root / requested_path).resolve()

    if not candidate.is_relative_to(root):
        raise SecurityError("Path is outside the configured workspace")

    return candidate


def validate_text_file(path: Path, max_bytes: int) -> None:
    """Apply conservative checks before exposing a local file to an MCP client."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path.name}")
    if not path.is_file():
        raise SecurityError("Requested path is not a file")
    if path.stat().st_size > max_bytes:
        raise SecurityError(f"File exceeds the {max_bytes}-byte read limit")

    blocked_names = {".env", ".env.local", ".env.production"}
    blocked_suffixes = {".pem", ".key", ".p12", ".pfx"}
    if path.name.lower() in blocked_names or path.suffix.lower() in blocked_suffixes:
        raise SecurityError("Reading likely secret or credential files is blocked")
