"""Inbox processing module for Second Brain MCP Server.

This module provides automated inbox processing capabilities:
- Content routing based on source type detection
- Smart folder suggestions following Second Brain conventions
- Future: Full inbox processing pipeline

The inbox system achieves >90% routing accuracy by analyzing content patterns
and applying consistent rules aligned with the 00-05 folder structure.
"""

from .router import InboxRouter

__all__ = ["InboxRouter"]
