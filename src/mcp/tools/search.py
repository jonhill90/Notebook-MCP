"""MCP tool for semantic search in Second Brain vault.

This module provides the search_knowledge_base MCP tool that exposes
VaultQdrantClient vector search functionality via the MCP protocol.

Pattern: Follows basic-memory MCP tool patterns (async functions, structured returns)
Critical Gotchas Addressed:
- Validates match_count range (1-20)
- Handles missing environment variables
- Returns structured responses for MCP compatibility

Reference: prps/INITIAL_personal_notebook_mcp.md (Task 3.2)
"""

import logging
import os
from typing import Optional, Any

logger = logging.getLogger(__name__)


async def search_knowledge_base(
    query: str,
    source_id: Optional[str] = None,
    match_count: int = 5
) -> dict[str, Any]:
    """Search vault using vector similarity.

    This MCP tool performs semantic search over Second Brain vault notes
    using OpenAI embeddings and Qdrant vector similarity.

    Args:
        query: Search query (2-5 keywords recommended for best results)
        source_id: Optional filter to specific folder (NOT IMPLEMENTED YET)
        match_count: Number of results (max 20, default: 5)

    Returns:
        dict: Search results with structure:
            {
                "query": str,           # Original query
                "match_count": int,     # Number of results returned
                "results": [            # List of matching notes
                    {
                        "note_id": str,  # 14-char YYYYMMDDHHmmss ID
                        "title": str,    # Note title
                        "score": float   # Similarity score (0.0-1.0)
                    },
                    ...
                ]
            }

    Raises:
        ValueError: If query is empty or match_count invalid
        RuntimeError: If environment variables missing
        Exception: If search fails

    Example:
        ```python
        # Search for notes about vector search
        results = await search_knowledge_base(
            query="vector search embeddings",
            match_count=5
        )

        # Results:
        # {
        #     "query": "vector search embeddings",
        #     "match_count": 3,
        #     "results": [
        #         {"note_id": "20251114020000", "title": "RAG Architecture", "score": 0.87},
        #         {"note_id": "20251113150000", "title": "Embeddings", "score": 0.75},
        #         {"note_id": "20251112100000", "title": "Qdrant", "score": 0.68}
        #     ]
        # }
        ```

    Pattern: Follows basic-memory MCP tool pattern:
        1. Validate inputs
        2. Initialize client
        3. Call client method
        4. Return structured response
    """
    # Validation
    if not query or not query.strip():
        raise ValueError("Query cannot be empty or whitespace only")

    if match_count < 1 or match_count > 20:
        raise ValueError("match_count must be between 1 and 20")

    # Get environment variables
    qdrant_url = os.getenv("QDRANT_URL")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not qdrant_url:
        raise RuntimeError("QDRANT_URL environment variable not set")

    if not openai_api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable not set")

    # Import VaultQdrantClient (local import to avoid circular dependencies)
    from ...vector.qdrant_client import VaultQdrantClient

    try:
        # Initialize client
        client = VaultQdrantClient(
            qdrant_url=qdrant_url,
            openai_api_key=openai_api_key
        )

        # Perform search
        results = await client.search_similar(query, limit=match_count)

        logger.info(
            f"MCP search_knowledge_base: query='{query}', "
            f"found {len(results)} results"
        )

        # Return structured response
        return {
            "query": query,
            "match_count": len(results),
            "results": results
        }

    except Exception as e:
        logger.error(f"MCP search_knowledge_base error: {e}", exc_info=True)
        raise


# Future enhancement: Filter by source_id (folder)
# This will be implemented in Phase 2 when folder filtering is added
# to VaultQdrantClient.search_similar()
#
# Example implementation:
# if source_id:
#     # Map source_id to folder name
#     folder_mapping = {
#         "inbox": "00 - Inbox",
#         "notes": "01 - Notes",
#         "mocs": "02 - MOCs",
#         # ...
#     }
#     folder = folder_mapping.get(source_id)
#     results = await client.search_similar(
#         query, limit=match_count, folder_filter=folder
#     )
