"""MCP tools for Second Brain vault operations.

This package provides MCP-compatible tool functions for:
- write_note: Create notes with convention enforcement
- read_note: Read notes by ID
- search_knowledge_base: Semantic search via vector similarity
- process_inbox_item: Route and tag inbox items
- create_moc: Generate Maps of Content for tag clusters

Pattern: Follows basic-memory tool organization
- Each tool in separate file
- Imported and re-exported from __init__.py
- Async functions for MCP compatibility

Reference: prps/INITIAL_personal_notebook_mcp.md
"""

from .vault import write_note, read_note
from .search import search_knowledge_base
from .inbox import process_inbox_item
from .moc import create_moc

__all__ = [
    "write_note",
    "read_note",
    "search_knowledge_base",
    "process_inbox_item",
    "create_moc",
]
