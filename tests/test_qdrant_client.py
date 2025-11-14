"""Tests for VaultQdrantClient (vector search).

This module tests:
1. Collection creation on initialization
2. Embedding generation via OpenAI
3. Semantic search functionality
4. Note upsert/delete operations
5. Error handling and validation

Pattern: Follows RAG-Service test patterns with mocking
Reference: prps/INITIAL_personal_notebook_mcp.md (Task 3.1)
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from qdrant_client.models import Distance
import httpx

from src.vector.qdrant_client import VaultQdrantClient


@pytest.fixture
def mock_qdrant_client():
    """Mock QdrantClient for testing without real Qdrant instance."""
    with patch("src.vector.qdrant_client.QdrantClient") as mock_client_class:
        mock_client = Mock()

        # Mock get_collections to return empty list initially
        mock_collections = Mock()
        mock_collections.collections = []
        mock_client.get_collections.return_value = mock_collections

        # Mock create_collection
        mock_client.create_collection.return_value = None

        # Return mock client instance
        mock_client_class.return_value = mock_client

        yield mock_client


@pytest.fixture
def vault_client(mock_qdrant_client):
    """Create VaultQdrantClient with mocked dependencies."""
    return VaultQdrantClient(
        qdrant_url="http://localhost:6333",
        openai_api_key="sk-test-key"
    )


class TestCollectionManagement:
    """Test collection creation and validation."""

    def test_collection_created_on_init(self, vault_client, mock_qdrant_client):
        """Test that collection is created during initialization."""
        # Verify get_collections was called
        assert mock_qdrant_client.get_collections.called

        # Verify create_collection was called with correct params
        mock_qdrant_client.create_collection.assert_called_once()
        call_args = mock_qdrant_client.create_collection.call_args

        assert call_args.kwargs["collection_name"] == "second_brain_notes"
        assert call_args.kwargs["vectors_config"].size == 1536
        assert call_args.kwargs["vectors_config"].distance == Distance.COSINE

    def test_collection_not_recreated_if_exists(self, mock_qdrant_client):
        """Test that existing collection is not recreated."""
        # Mock collection already exists
        mock_collection = Mock()
        mock_collection.name = "second_brain_notes"
        mock_collections = Mock()
        mock_collections.collections = [mock_collection]
        mock_qdrant_client.get_collections.return_value = mock_collections

        # Create client
        VaultQdrantClient(
            qdrant_url="http://localhost:6333",
            openai_api_key="sk-test-key"
        )

        # Verify create_collection was NOT called
        mock_qdrant_client.create_collection.assert_not_called()


class TestEmbeddingGeneration:
    """Test OpenAI embedding generation."""

    @pytest.mark.asyncio
    async def test_embed_text_success(self, vault_client):
        """Test successful embedding generation."""
        # Mock OpenAI API response
        mock_embedding = [0.1] * 1536  # Valid 1536-dimension vector

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"embedding": mock_embedding}]
        }
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            # Generate embedding
            result = await vault_client.embed_text("test content")

            # Verify result
            assert result == mock_embedding
            assert len(result) == 1536

            # Verify API call
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert "https://api.openai.com/v1/embeddings" in call_args[0]
            assert call_args.kwargs["json"]["model"] == "text-embedding-3-small"
            assert call_args.kwargs["json"]["input"] == "test content"

    @pytest.mark.asyncio
    async def test_embed_text_empty_input(self, vault_client):
        """Test that empty text raises ValueError."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            await vault_client.embed_text("")

        with pytest.raises(ValueError, match="Text cannot be empty"):
            await vault_client.embed_text("   ")

    @pytest.mark.asyncio
    async def test_embed_text_invalid_dimension(self, vault_client):
        """Test that invalid embedding dimension raises ValueError."""
        # Mock OpenAI API response with wrong dimension
        mock_embedding = [0.1] * 512  # Wrong dimension (should be 1536)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"embedding": mock_embedding}]
        }
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            # Should raise ValueError
            with pytest.raises(ValueError, match="Invalid embedding dimension"):
                await vault_client.embed_text("test content")

    @pytest.mark.asyncio
    async def test_embed_text_all_zeros(self, vault_client):
        """Test that all-zero embedding raises ValueError (quota exhaustion)."""
        # Mock OpenAI API response with all zeros
        mock_embedding = [0.0] * 1536  # All zeros indicates quota exhaustion

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"embedding": mock_embedding}]
        }
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            # Should raise ValueError
            with pytest.raises(ValueError, match="all zeros"):
                await vault_client.embed_text("test content")

    @pytest.mark.asyncio
    async def test_embed_text_api_error(self, vault_client):
        """Test that API errors are properly raised."""
        mock_response = Mock()
        mock_response.status_code = 429  # Rate limit
        mock_response.text = "Rate limit exceeded"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Rate limit exceeded",
            request=Mock(),
            response=mock_response
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            # Should raise HTTPStatusError
            with pytest.raises(httpx.HTTPStatusError):
                await vault_client.embed_text("test content")


class TestSearch:
    """Test semantic search functionality."""

    @pytest.mark.asyncio
    async def test_search_similar_success(self, vault_client, mock_qdrant_client):
        """Test successful semantic search."""
        # Mock embedding generation
        mock_embedding = [0.1] * 1536

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"embedding": mock_embedding}]
        }
        mock_response.raise_for_status = Mock()

        # Mock Qdrant search results
        mock_results = [
            Mock(
                id="20251114020000",
                score=0.87,
                payload={"note_id": "20251114020000", "title": "Test Note 1"}
            ),
            Mock(
                id="20251114020100",
                score=0.75,
                payload={"note_id": "20251114020100", "title": "Test Note 2"}
            )
        ]
        mock_qdrant_client.search.return_value = mock_results

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            # Perform search
            results = await vault_client.search_similar("test query", limit=5)

            # Verify results
            assert len(results) == 2
            assert results[0]["note_id"] == "20251114020000"
            assert results[0]["title"] == "Test Note 1"
            assert results[0]["score"] == 0.87
            assert results[1]["note_id"] == "20251114020100"
            assert results[1]["title"] == "Test Note 2"
            assert results[1]["score"] == 0.75

            # Verify Qdrant search was called
            mock_qdrant_client.search.assert_called_once()
            call_args = mock_qdrant_client.search.call_args
            assert call_args.kwargs["collection_name"] == "second_brain_notes"
            assert call_args.kwargs["query_vector"] == mock_embedding
            assert call_args.kwargs["limit"] == 5

    @pytest.mark.asyncio
    async def test_search_similar_empty_query(self, vault_client):
        """Test that empty query raises ValueError."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await vault_client.search_similar("")

        with pytest.raises(ValueError, match="Query cannot be empty"):
            await vault_client.search_similar("   ")

    @pytest.mark.asyncio
    async def test_search_similar_invalid_limit(self, vault_client):
        """Test that invalid limit raises ValueError."""
        with pytest.raises(ValueError, match="Limit must be between 1 and 20"):
            await vault_client.search_similar("test", limit=0)

        with pytest.raises(ValueError, match="Limit must be between 1 and 20"):
            await vault_client.search_similar("test", limit=21)

    @pytest.mark.asyncio
    async def test_search_similar_no_results(self, vault_client, mock_qdrant_client):
        """Test search with no results."""
        # Mock embedding generation
        mock_embedding = [0.1] * 1536

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"embedding": mock_embedding}]
        }
        mock_response.raise_for_status = Mock()

        # Mock empty Qdrant results
        mock_qdrant_client.search.return_value = []

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            # Perform search
            results = await vault_client.search_similar("test query", limit=5)

            # Verify empty results
            assert len(results) == 0
            assert isinstance(results, list)


class TestNoteOperations:
    """Test note upsert and delete operations."""

    @pytest.mark.asyncio
    async def test_upsert_note_success(self, vault_client, mock_qdrant_client):
        """Test successful note upsert."""
        # Mock embedding generation
        mock_embedding = [0.1] * 1536

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"embedding": mock_embedding}]
        }
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            # Upsert note
            await vault_client.upsert_note(
                note_id="20251114020000",
                title="Test Note",
                content="Test content",
                tags=["test", "knowledge-management"]
            )

            # Verify upsert was called
            mock_qdrant_client.upsert.assert_called_once()
            call_args = mock_qdrant_client.upsert.call_args

            assert call_args.kwargs["collection_name"] == "second_brain_notes"
            points = call_args.kwargs["points"]
            assert len(points) == 1
            assert points[0].id == "20251114020000"
            assert points[0].vector == mock_embedding
            assert points[0].payload["note_id"] == "20251114020000"
            assert points[0].payload["title"] == "Test Note"
            assert points[0].payload["tags"] == ["test", "knowledge-management"]

    @pytest.mark.asyncio
    async def test_upsert_note_empty_note_id(self, vault_client):
        """Test that empty note_id raises ValueError."""
        with pytest.raises(ValueError, match="note_id cannot be empty"):
            await vault_client.upsert_note(
                note_id="",
                title="Test",
                content="Test content"
            )

    @pytest.mark.asyncio
    async def test_upsert_note_empty_content(self, vault_client):
        """Test that empty content raises ValueError."""
        with pytest.raises(ValueError, match="content cannot be empty"):
            await vault_client.upsert_note(
                note_id="20251114020000",
                title="Test",
                content=""
            )

    @pytest.mark.asyncio
    async def test_delete_note_success(self, vault_client, mock_qdrant_client):
        """Test successful note deletion."""
        # Delete note
        await vault_client.delete_note("20251114020000")

        # Verify delete was called
        mock_qdrant_client.delete.assert_called_once()
        call_args = mock_qdrant_client.delete.call_args

        assert call_args.kwargs["collection_name"] == "second_brain_notes"
        assert call_args.kwargs["points_selector"] == ["20251114020000"]


class TestClientConfiguration:
    """Test client initialization and configuration."""

    def test_client_initialization(self, vault_client):
        """Test that client is initialized with correct config."""
        assert vault_client.collection_name == "second_brain_notes"
        assert vault_client.model_name == "text-embedding-3-small"
        assert vault_client.expected_dimension == 1536
        assert vault_client.openai_key == "sk-test-key"

    def test_client_validates_params(self):
        """Test that client validates initialization params."""
        # Should not raise - valid params
        with patch("src.vector.qdrant_client.QdrantClient"):
            client = VaultQdrantClient(
                qdrant_url="http://localhost:6333",
                openai_api_key="sk-test-key"
            )
            assert client is not None
