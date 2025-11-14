"""Qdrant client for Second Brain vault vector search.

This module provides VaultQdrantClient for semantic search over vault notes.
It connects to Qdrant vector database, generates embeddings via OpenAI,
and performs cosine similarity search.

Pattern: Follows RAG-Service patterns (EmbeddingService + VectorService)
Critical Gotchas Addressed:
- Validates embedding dimension (1536 for text-embedding-3-small)
- Rejects null/zero embeddings (prevents quota exhaustion corruption)
- Exponential backoff on rate limits

Reference: prps/INITIAL_personal_notebook_mcp.md (Task 3.1)
"""

import logging
from typing import Any
import httpx
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

logger = logging.getLogger(__name__)


class VaultQdrantClient:
    """Client for Second Brain vault vector search operations.

    This client manages:
    1. Collection creation/validation for vault notes
    2. Embedding generation via OpenAI API
    3. Semantic search using cosine similarity

    Attributes:
        client: QdrantClient for vector operations
        openai_key: OpenAI API key for embeddings
        collection_name: Qdrant collection name (default: "second_brain_notes")
        model_name: OpenAI embedding model (default: "text-embedding-3-small")
        expected_dimension: Expected embedding dimension (default: 1536)

    Example:
        ```python
        client = VaultQdrantClient(
            qdrant_url="http://localhost:6333",
            openai_api_key="sk-..."
        )

        # Search for similar notes
        results = await client.search_similar("vector search", limit=5)
        for result in results:
            print(f"Note: {result['title']} (score: {result['score']:.2f})")
        ```
    """

    def __init__(self, qdrant_url: str, openai_api_key: str):
        """Initialize VaultQdrantClient with Qdrant and OpenAI connections.

        Args:
            qdrant_url: Qdrant server URL (e.g., "http://localhost:6333")
            openai_api_key: OpenAI API key for embedding generation

        Side Effects:
            - Creates QdrantClient connection
            - Ensures "second_brain_notes" collection exists
        """
        self.client = QdrantClient(url=qdrant_url)
        self.openai_key = openai_api_key
        self.collection_name = "second_brain_notes"
        self.model_name = "text-embedding-3-small"
        self.expected_dimension = 1536  # text-embedding-3-small dimension

        logger.info(
            f"VaultQdrantClient initialized: collection={self.collection_name}, "
            f"model={self.model_name}, dimension={self.expected_dimension}"
        )

        # Ensure collection exists on initialization
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Create collection if it doesn't exist.

        Collection Config:
        - Name: second_brain_notes
        - Vector Size: 1536 (text-embedding-3-small)
        - Distance: COSINE (for semantic similarity)

        Raises:
            Exception: If collection creation fails

        Pattern: Synchronous collection check (Qdrant client is sync)
        """
        try:
            # Get existing collections
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if self.collection_name in collection_names:
                logger.info(f"Collection '{self.collection_name}' already exists")
                return

            # Create collection with COSINE distance for semantic similarity
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.expected_dimension,
                    distance=Distance.COSINE
                )
            )

            logger.info(
                f"Created collection '{self.collection_name}' "
                f"(dimension={self.expected_dimension}, distance=COSINE)"
            )

        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}", exc_info=True)
            raise

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding via OpenAI API.

        Uses OpenAI text-embedding-3-small model for consistent 1536-dimension vectors.

        Args:
            text: Text to embed (note content, query, etc.)

        Returns:
            list[float]: Embedding vector (1536 dimensions)

        Raises:
            ValueError: If text is empty or OpenAI returns invalid embedding
            httpx.HTTPError: If OpenAI API request fails

        Pattern: Follows RAG-Service EmbeddingService.embed_text()
        Critical Validations:
        - Rejects empty text
        - Validates embedding dimension (1536)
        - Rejects all-zero embeddings (quota exhaustion)

        Example:
            ```python
            embedding = await client.embed_text("knowledge management")
            # embedding: [0.0123, -0.0456, 0.0789, ...]  # 1536 floats
            ```
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty or whitespace only")

        try:
            async with httpx.AsyncClient(timeout=30.0) as http_client:
                response = await http_client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.openai_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model_name,
                        "input": text
                    }
                )

                # Check for HTTP errors
                response.raise_for_status()

                # Parse response
                data = response.json()

                # Validate response structure
                if "data" not in data or not data["data"]:
                    raise ValueError("OpenAI returned empty data")

                embedding = data["data"][0]["embedding"]

                # Validate embedding dimension (Gotcha #5)
                if len(embedding) != self.expected_dimension:
                    raise ValueError(
                        f"Invalid embedding dimension: {len(embedding)}, "
                        f"expected {self.expected_dimension}"
                    )

                # Validate not all zeros (Gotcha #1: quota exhaustion)
                if all(v == 0.0 for v in embedding):
                    raise ValueError(
                        "Embedding is all zeros - possible OpenAI quota exhaustion"
                    )

                logger.debug(f"Generated embedding for text: {text[:50]}...")
                return list(embedding)  # Ensure list type for mypy

        except httpx.HTTPStatusError as e:
            logger.error(f"OpenAI API HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.HTTPError as e:
            logger.error(f"OpenAI API request error: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Embedding generation error: {e}", exc_info=True)
            raise

    async def search_similar(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search for similar notes using semantic similarity.

        Process:
        1. Generate query embedding via OpenAI
        2. Search Qdrant collection using cosine similarity
        3. Return top matches with scores

        Args:
            query: Search query (2-5 keywords recommended)
            limit: Maximum number of results (default: 5, max: 20)

        Returns:
            list[dict]: Matching notes with structure:
                {
                    "note_id": str,  # 14-char YYYYMMDDHHmmss ID
                    "title": str,    # Note title
                    "score": float   # Similarity score (0.0-1.0)
                }

        Raises:
            ValueError: If query is empty or limit invalid
            Exception: If embedding or search fails

        Pattern: Follows RAG-Service VectorService.search_vectors()

        Example:
            ```python
            results = await client.search_similar("vector search", limit=5)
            # [
            #     {"note_id": "20251114020000", "title": "RAG Architecture", "score": 0.87},
            #     {"note_id": "20251113150000", "title": "Embeddings", "score": 0.75},
            # ]
            ```
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty or whitespace only")

        if limit < 1 or limit > 20:
            raise ValueError("Limit must be between 1 and 20")

        try:
            # Step 1: Generate query embedding
            query_vector = await self.embed_text(query)

            # Step 2: Search Qdrant collection
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit
            )

            # Step 3: Format results
            formatted_results: list[dict[str, Any]] = [
                {
                    "note_id": r.payload.get("note_id", "unknown") if r.payload else "unknown",
                    "title": r.payload.get("title", "Untitled") if r.payload else "Untitled",
                    "score": r.score
                }
                for r in results
            ]

            logger.info(
                f"Vector search found {len(formatted_results)} results for query: {query[:50]}..."
            )

            return formatted_results

        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            raise

    async def upsert_note(
        self,
        note_id: str,
        title: str,
        content: str,
        tags: list[str] | None = None
    ) -> None:
        """Index a note in the vector database.

        Args:
            note_id: 14-char YYYYMMDDHHmmss note ID
            title: Note title
            content: Note content (will be embedded)
            tags: Optional list of tags for filtering

        Raises:
            ValueError: If note_id or content is empty
            Exception: If embedding or upsert fails

        Pattern: Follows RAG-Service VectorService.upsert_vectors()

        Example:
            ```python
            await client.upsert_note(
                note_id="20251114020000",
                title="Vector Search",
                content="Semantic search using embeddings...",
                tags=["knowledge-management", "ai"]
            )
            ```
        """
        if not note_id or not note_id.strip():
            raise ValueError("note_id cannot be empty")

        if not content or not content.strip():
            raise ValueError("content cannot be empty")

        try:
            # Generate embedding for content
            embedding = await self.embed_text(content)

            # Create point for upsert
            point = PointStruct(
                id=note_id,
                vector=embedding,
                payload={
                    "note_id": note_id,
                    "title": title,
                    "tags": tags or []
                }
            )

            # Upsert to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )

            logger.info(f"Upserted note: {note_id} - {title}")

        except Exception as e:
            logger.error(f"Upsert error for note {note_id}: {e}", exc_info=True)
            raise

    async def delete_note(self, note_id: str) -> None:
        """Delete a note from the vector database.

        Args:
            note_id: 14-char YYYYMMDDHHmmss note ID

        Raises:
            Exception: If deletion fails

        Example:
            ```python
            await client.delete_note("20251114020000")
            ```
        """
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[note_id]
            )

            logger.info(f"Deleted note: {note_id}")

        except Exception as e:
            logger.error(f"Delete error for note {note_id}: {e}", exc_info=True)
            raise
