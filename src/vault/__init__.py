"""Vault management module for Second Brain MCP Server.

This module handles all vault operations including:
- Note creation, reading, updating, deletion (CRUD)
- Convention enforcement (folder structure, frontmatter, IDs)
- Tag analysis and auto-suggestion
- MOC (Map of Content) generation
"""

from .manager import VaultManager

__all__ = ["VaultManager"]
