# MCP Second Brain Server - Docker Image
# Convention-enforcing MCP server for Obsidian Second Brain vault
# Python 3.12+ with uv package manager for fast dependency installation

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager (faster than pip)
RUN pip install --no-cache-dir uv

# Copy dependency files first for better Docker layer caching
COPY pyproject.toml .
COPY requirements.txt .

# Install Python dependencies using uv
# --system flag installs to system Python (no virtual env in container)
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application source code
COPY src/ ./src/

# Copy configuration files
COPY config/ ./config/

# Expose MCP server port (default 8053, overridable via MCP_PORT env var)
EXPOSE 8053

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${MCP_PORT:-8053}/health || exit 1

# Run MCP server
# Port configurable via MCP_PORT environment variable
CMD ["python", "-m", "src.server"]
