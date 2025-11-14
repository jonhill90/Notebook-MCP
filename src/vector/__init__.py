"""Vector search module for Second Brain vault.

This module provides Qdrant integration for semantic search over vault notes.
It connects to Qdrant vector database, generates embeddings via OpenAI,
and performs cosine similarity search.

Key Components:
- VaultQdrantClient: Main client for vector operations
- Embedding generation via OpenAI text-embedding-3-small
- Collection management for second_brain_notes

Pattern: Follows RAG-Service vector service patterns
"""

from .qdrant_client import VaultQdrantClient

__all__ = ["VaultQdrantClient"]
