"""MCP tool for inbox processing.

This module provides the process_inbox_item MCP tool that routes inbox items
to appropriate folders with auto-suggested tags.

Pattern: Follows basic-memory MCP tool patterns (async functions, structured returns)
Critical Gotchas Addressed:
- Content classification (URL vs code vs thought)
- Folder routing logic
- Tag suggestion integration

Reference: prps/INITIAL_personal_notebook_mcp.md (Task 4.2)
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


async def process_inbox_item(
    title: str,
    content: str
) -> dict[str, Any]:
    """Process an inbox item with automatic routing and tagging.

    This MCP tool analyzes inbox content, classifies it (URL/code/thought),
    routes to appropriate folder, suggests tags, and creates the note.

    Args:
        title: Item title
        content: Item content (markdown, URL, code, etc.)

    Returns:
        dict: Processing result with structure:
            {
                "note_id": str,         # Generated 14-char ID
                "file_path": str,       # Full path to created file
                "folder": str,          # Routed folder
                "source_type": str,     # Detected type (url/code/thought)
                "tags": list[str],      # Suggested tags
                "note_type": str        # Note type (clipping/note)
            }

    Raises:
        ValueError: If title or content empty
        RuntimeError: If environment variables missing

    Example:
        ```python
        # Process a URL clipping
        result = await process_inbox_item(
            title="RAG Architecture Guide",
            content="https://docs.anthropic.com/rag\\n\\nGreat explanation of RAG..."
        )

        # Result:
        # {
        #     "note_id": "20251114153500",
        #     "file_path": "/vault/05 - Resources/20251114153500.md",
        #     "folder": "05 - Resources",
        #     "source_type": "url",
        #     "tags": ["rag", "architecture", "documentation"],
        #     "note_type": "clipping"
        # }

        # Process a code snippet
        result = await process_inbox_item(
            title="Async Context Manager Pattern",
            content="```python\\nasync def get_client():\\n    ...\\n```"
        )

        # Result:
        # {
        #     "note_id": "20251114153600",
        #     "file_path": "/vault/05 - Resources/20251114153600.md",
        #     "folder": "05 - Resources",
        #     "source_type": "code",
        #     "tags": ["python", "async", "patterns"],
        #     "note_type": "note"
        # }

        # Process a thought
        result = await process_inbox_item(
            title="Notes on Vector Search",
            content="Vector search allows semantic similarity..."
        )

        # Result:
        # {
        #     "note_id": "20251114153700",
        #     "file_path": "/vault/01 - Notes/20251114153700.md",
        #     "folder": "01 - Notes",
        #     "source_type": "thought",
        #     "tags": ["vector-search", "embeddings"],
        #     "note_type": "note"
        # }
        ```

    Pattern: InboxProcessor orchestrates router + tag_analyzer + vault_manager
    """
    # Validation
    if not title or not title.strip():
        raise ValueError("Title cannot be empty or whitespace only")

    if not content or not content.strip():
        raise ValueError("Content cannot be empty or whitespace only")

    # Get environment variable
    vault_path = os.getenv("VAULT_PATH")
    if not vault_path:
        raise RuntimeError("VAULT_PATH environment variable not set")

    # Import InboxProcessor (local import to avoid circular dependencies)
    from ...inbox.processor import InboxProcessor

    try:
        # Initialize processor
        processor = InboxProcessor(vault_path)

        # Process item (handles classification, routing, tagging, creation)
        result = await processor.process_item(title, content)

        logger.info(
            f"MCP process_inbox_item: processed '{title}' -> "
            f"{result['source_type']} -> {result['folder']}"
        )

        # Return result (InboxProcessor already returns structured dict)
        return result

    except Exception as e:
        logger.error(f"MCP process_inbox_item error: {e}", exc_info=True)
        raise
