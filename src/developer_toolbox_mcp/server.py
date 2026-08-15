from __future__ import annotations

import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .config import settings
from .security import SecurityError, resolve_safe_path, validate_text_file

mcp = FastMCP("Developer Toolbox MCP")


def _root() -> Path:
    return settings.workspace_root.expanduser().resolve()


@mcp.tool()
def health_check() -> dict[str, str]:
    """Return basic server health information without exposing host details."""
    return {"status": "ok", "service": "developer-toolbox-mcp", "version": "0.1.0"}


@mcp.tool()
def list_repo_files(path: str = ".", limit: int = 100) -> list[str]:
    """List workspace files without allowing traversal outside the configured root."""
    target = resolve_safe_path(_root(), path)
    if not target.exists() or not target.is_dir():
        raise SecurityError("Requested path is not an existing directory")

    safe_limit = max(1, min(limit, 200))
    entries: list[str] = []
    for item in sorted(target.iterdir(), key=lambda p: p.name.lower()):
        if item.name in {".git", ".venv", "__pycache__"}:
            continue
        relative = item.relative_to(_root()).as_posix()
        entries.append(relative + ("/" if item.is_dir() else ""))
        if len(entries) >= safe_limit:
            break
    return entries


@mcp.tool()
def read_file(path: str) -> str:
    """Read a UTF-8 text file inside the workspace with credential and size safeguards."""
    target = resolve_safe_path(_root(), path)
    validate_text_file(target, settings.max_file_bytes)
    try:
        return target.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise SecurityError("Only UTF-8 text files are supported") from exc


@mcp.tool()
def search_code(query: str, path: str = ".") -> list[dict[str, object]]:
    """Search text files in the workspace using a literal, case-insensitive query."""
    if not query.strip():
        raise ValueError("query must not be empty")

    target = resolve_safe_path(_root(), path)
    results: list[dict[str, object]] = []
    blocked_dirs = {".git", ".venv", "node_modules", "__pycache__"}

    files = [target] if target.is_file() else target.rglob("*")
    for file_path in files:
        if not file_path.is_file() or any(part in blocked_dirs for part in file_path.parts):
            continue
        try:
            validate_text_file(file_path, settings.max_file_bytes)
            text = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError, SecurityError):
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            if query.casefold() in line.casefold():
                results.append(
                    {
                        "path": file_path.relative_to(_root()).as_posix(),
                        "line": number,
                        "text": line[:300],
                    }
                )
                if len(results) >= settings.max_search_results:
                    return results
    return results


def _git(*args: str) -> str:
    """Execute a fixed git subcommand argument list; no shell interpolation is used."""
    result = subprocess.run(
        ["git", "-C", str(_root()), *args],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Git command failed")
    return result.stdout.strip()


@mcp.tool()
def git_status() -> str:
    """Return the repository status using a read-only Git command."""
    return _git("status", "--short", "--branch")


@mcp.tool()
def git_log(limit: int = 10) -> list[str]:
    """Return a bounded, compact commit history using a read-only Git command."""
    safe_limit = max(1, min(limit, 50))
    output = _git("log", f"-{safe_limit}", "--pretty=format:%h %s")
    return output.splitlines() if output else []


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
