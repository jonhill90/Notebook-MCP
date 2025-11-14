"""MCP (Model Context Protocol) package for Second Brain vault.

This package provides MCP server implementation and tools for vault operations.

Pattern: Follows basic-memory MCP architecture
- tools/: MCP-compatible tool functions
- (future) server.py: MCP server implementation
- (future) registry.py: Tool registration

Reference: prps/INITIAL_personal_notebook_mcp.md
"""

from .tools import search_knowledge_base

__all__ = [
    "search_knowledge_base",
]
