"""Configuration management for MCP Second Brain Server.

This module provides centralized configuration loading from environment
variables with validation and defaults.

Pattern: Pydantic Settings for type-safe configuration
Critical Gotchas Addressed:
- Missing environment variables (defaults provided)
- Path validation (vault path must exist)
- Port validation (must be valid port number)

Reference: prps/INITIAL_personal_notebook_mcp.md (Task 5.1)
"""

import os
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field, field_validator


class Config(BaseModel):
    """Configuration for MCP Second Brain Server.

    This class loads configuration from environment variables with
    validation and sensible defaults.

    Environment Variables:
        VAULT_PATH: Path to Second Brain vault (default: ./repos/Second Brain)
        QDRANT_URL: URL to Qdrant service (default: http://localhost:6333)
        OPENAI_API_KEY: OpenAI API key for embeddings (required)
        MCP_PORT: Port for MCP server (default: 8053)
        LOG_LEVEL: Logging level (default: INFO)

    Example:
        ```python
        # Load configuration from environment
        config = Config.from_env()

        # Access configuration
        print(config.vault_path)  # Path('/vault')
        print(config.mcp_port)    # 8053
        ```

    Pattern: Follows Pydantic v2 settings pattern with validation
    """

    vault_path: Path = Field(
        description="Path to Second Brain Obsidian vault"
    )
    qdrant_url: str = Field(
        description="URL to Qdrant vector database service"
    )
    openai_api_key: str = Field(
        description="OpenAI API key for embeddings generation"
    )
    mcp_port: int = Field(
        description="Port for MCP server to listen on",
        ge=1024,  # Must be >= 1024 (non-privileged)
        le=65535  # Must be <= 65535 (valid port range)
    )
    log_level: str = Field(
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )

    @field_validator('vault_path')
    @classmethod
    def validate_vault_path(cls, v: Path) -> Path:
        """Validate vault path exists (or log warning if not).

        Note: We don't raise an error if path doesn't exist because
        it might be mounted later in Docker environment.
        """
        if not v.exists():
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Vault path does not exist: {v} "
                f"(this is OK if running in Docker and path will be mounted)"
            )
        return v

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(
                f"Invalid log level: {v}. Must be one of {valid_levels}"
            )
        return v_upper

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables.

        This is the primary way to instantiate Config. It reads from
        environment variables with sensible defaults.

        Returns:
            Config: Configuration instance

        Example:
            ```python
            # Load configuration
            config = Config.from_env()

            # Use configuration
            vault = VaultManager(str(config.vault_path))
            ```

        Pattern: Factory method for environment-based configuration
        """
        return cls(
            vault_path=Path(os.getenv("VAULT_PATH", "./repos/Second Brain")),
            qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            mcp_port=int(os.getenv("MCP_PORT", "8053")),
            log_level=os.getenv("LOG_LEVEL", "INFO")
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary (for logging/debugging).

        Returns:
            dict: Configuration as dictionary

        Example:
            ```python
            config = Config.from_env()
            print(config.to_dict())
            # {
            #     "vault_path": "/vault",
            #     "qdrant_url": "http://localhost:6333",
            #     "openai_api_key": "sk-...",  # Redacted in actual implementation
            #     "mcp_port": 8053,
            #     "log_level": "INFO"
            # }
            ```
        """
        return {
            "vault_path": str(self.vault_path),
            "qdrant_url": self.qdrant_url,
            "openai_api_key": "***" if self.openai_api_key else "",  # Redact API key
            "mcp_port": self.mcp_port,
            "log_level": self.log_level
        }
