"""MCP tools for vault note operations (write, read).

This module provides MCP tools for creating and reading notes in the vault.
All tools enforce Second Brain conventions via VaultManager.

Pattern: Follows basic-memory MCP tool patterns (async functions, structured returns)
Critical Gotchas Addressed:
- ID collision detection (multiple notes per second)
- Folder/type validation
- Tag normalization (lowercase-hyphenated)
- Frontmatter validation via Pydantic

Reference: prps/INITIAL_personal_notebook_mcp.md (Task 5.2)
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


async def write_note(
    title: str,
    content: str,
    folder: str,
    note_type: str,
    tags: list[str]
) -> dict[str, Any]:
    """Create a new note with convention enforcement.

    This MCP tool creates a note in the Second Brain vault with:
    - Auto-generated 14-char ID (YYYYMMDDHHmmss)
    - Validated frontmatter
    - Folder/type validation
    - Tag normalization

    Args:
        title: Note title (will be converted to permalink)
        content: Markdown content body
        folder: Folder path (e.g., "01 - Notes", "02 - MOCs")
        note_type: Note type (must match folder conventions)
        tags: List of tags (will be normalized to lowercase-hyphenated)

    Returns:
        dict: Creation result with structure:
            {
                "note_id": str,         # Generated 14-char ID
                "file_path": str,       # Full path to created file
                "folder": str,          # Folder location
                "permalink": str,       # Generated permalink
                "tags": list[str]       # Normalized tags
            }

    Raises:
        ValueError: If folder/type mismatch or invalid data
        RuntimeError: If environment variables missing

    Example:
        ```python
        # Create a note
        result = await write_note(
            title="Vector Search Notes",
            content="# Vector Search\\n\\nEmbeddings explanation...",
            folder="01 - Notes",
            note_type="note",
            tags=["vector-search", "embeddings"]
        )

        # Result:
        # {
        #     "note_id": "20251114153000",
        #     "file_path": "/vault/01 - Notes/20251114153000.md",
        #     "folder": "01 - Notes",
        #     "permalink": "vector-search-notes",
        #     "tags": ["vector-search", "embeddings"]
        # }
        ```

    Pattern: Convention enforcement via VaultManager.create_note()
    """
    # Validation
    if not title or not title.strip():
        raise ValueError("Title cannot be empty or whitespace only")

    if not content or not content.strip():
        raise ValueError("Content cannot be empty or whitespace only")

    if not folder or not folder.strip():
        raise ValueError("Folder cannot be empty or whitespace only")

    if not note_type or not note_type.strip():
        raise ValueError("Note type cannot be empty or whitespace only")

    if not isinstance(tags, list):
        raise ValueError("Tags must be a list")

    # Get environment variable
    vault_path = os.getenv("VAULT_PATH")
    if not vault_path:
        raise RuntimeError("VAULT_PATH environment variable not set")

    # Import VaultManager (local import to avoid circular dependencies)
    from ...vault.manager import VaultManager

    try:
        # Initialize manager
        manager = VaultManager(vault_path)

        # Create note (VaultManager handles convention enforcement)
        file_path = await manager.create_note(
            title=title,
            content=content,
            folder=folder,
            note_type=note_type,
            tags=tags
        )

        # Extract note_id from file path
        note_id = file_path.stem  # filename without .md extension

        # Generate permalink (VaultManager does this too, but we need it for response)
        permalink = title.lower().replace(" ", "-")

        logger.info(
            f"MCP write_note: created note '{note_id}' in '{folder}'"
        )

        # Return structured response
        return {
            "note_id": note_id,
            "file_path": str(file_path),
            "folder": folder,
            "permalink": permalink,
            "tags": tags
        }

    except Exception as e:
        logger.error(f"MCP write_note error: {e}", exc_info=True)
        raise


async def read_note(
    note_id: str
) -> dict[str, Any] | None:
    """Read a note by its ID.

    This MCP tool reads a note from the vault and returns its frontmatter
    and content.

    Args:
        note_id: 14-char note ID (YYYYMMDDHHmmss) or permalink

    Returns:
        dict: Note data with structure:
            {
                "note_id": str,          # 14-char ID
                "title": str,            # Note title (from first H1 or filename)
                "content": str,          # Markdown content body
                "frontmatter": dict,     # Frontmatter data
                "file_path": str         # Full path to file
            }

    Raises:
        ValueError: If note_id is empty or invalid format
        FileNotFoundError: If note does not exist
        RuntimeError: If environment variables missing

    Example:
        ```python
        # Read a note
        result = await read_note(note_id="20251114153000")

        # Result:
        # {
        #     "note_id": "20251114153000",
        #     "title": "Vector Search Notes",
        #     "content": "# Vector Search\\n\\nEmbeddings explanation...",
        #     "frontmatter": {
        #         "id": "20251114153000",
        #         "type": "note",
        #         "tags": ["vector-search", "embeddings"],
        #         "created": "2025-11-14T15:30:00",
        #         "updated": "2025-11-14T15:30:00",
        #         "permalink": "vector-search-notes"
        #     },
        #     "file_path": "/vault/01 - Notes/20251114153000.md"
        # }
        ```

    Pattern: Use VaultManager.read_note() for consistent frontmatter parsing
    """
    # Validation
    if not note_id or not note_id.strip():
        raise ValueError("Note ID cannot be empty or whitespace only")

    # Get environment variable
    vault_path = os.getenv("VAULT_PATH")
    if not vault_path:
        raise RuntimeError("VAULT_PATH environment variable not set")

    # Import VaultManager (local import to avoid circular dependencies)
    from ...vault.manager import VaultManager

    try:
        # Initialize manager
        manager = VaultManager(vault_path)

        # Read note
        note_data = await manager.read_note(note_id)

        logger.info(
            f"MCP read_note: read note '{note_id}'"
        )

        # Return structured response
        return note_data

    except Exception as e:
        logger.error(f"MCP read_note error: {e}", exc_info=True)
        raise
