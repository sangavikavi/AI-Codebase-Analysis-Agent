import os
from pathlib import Path
from typing import Any


class MCPFileServer:
    """
    Model Context Protocol (MCP) File Operations Server:
    Exposes safe, read-only filesystem capabilities for agents to inspect codebase structure,
    read line slices, and search file trees.
    """

    @staticmethod
    def list_files(root_path: str, max_depth: int = 3) -> list[str]:
        """List files in the codebase up to a maximum depth."""
        p = Path(root_path)
        if not p.exists() or not p.is_dir():
            return []

        results = []
        for root, dirs, files in os.walk(p):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["node_modules", "venv"]]
            rel_root = os.path.relpath(root, p)
            depth = 0 if rel_root == "." else rel_root.count(os.sep) + 1
            if depth > max_depth:
                continue
            for f in files:
                rel = os.path.normpath(os.path.join(rel_root, f)).replace("\\", "/")
                results.append(rel)
        return results

    @staticmethod
    def read_file_slice(file_path: str, start_line: int, end_line: int) -> str:
        """Read specific line range from a file."""
        p = Path(file_path)
        if not p.exists() or not p.is_file():
            return f"Error: File '{file_path}' not found."

        try:
            lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
            s = max(0, start_line - 1)
            e = min(len(lines), end_line)
            return "\n".join(lines[s:e])
        except Exception as ex:
            return f"Error reading file: {str(ex)}"


mcp_file_server = MCPFileServer()
