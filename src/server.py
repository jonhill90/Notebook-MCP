"""
MCP Second Brain Server - Main Application

This module implements the MCP server using FastAPI that exposes all MCP tools
for Second Brain vault management.

Pattern: FastAPI-based MCP server following basic-memory patterns
Critical Gotchas Addressed:
- Environment variable validation on startup
- Proper logging configuration
- Health check endpoint for Docker
- Tool registration in /mcp/tools endpoint

Reference: prps/INITIAL_personal_notebook_mcp.md (Task 5.1)
"""

from typing import Any
from fastapi import FastAPI, HTTPException
from loguru import logger

from .config import Config
from .mcp.tools import (
    write_note,
    read_note,
    search_knowledge_base,
    process_inbox_item,
    create_moc
)

# Load configuration
try:
    config = Config.from_env()
except Exception as e:
    # Fallback to basic logging if config fails
    print(f"ERROR: Failed to load configuration: {e}")
    raise

# Configure logging
logger.remove()  # Remove default handler
logger.add(
    lambda msg: print(msg, end=""),
    level=config.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
)

# Initialize FastAPI app
app = FastAPI(
    title="MCP Second Brain Server",
    description="Convention-enforcing MCP server for Obsidian Second Brain vault",
    version="0.1.0"
)


@app.on_event("startup")
async def startup_event() -> None:
    """Log startup information and validate environment"""
    logger.info("=" * 60)
    logger.info("MCP Second Brain Server - Starting")
    logger.info("=" * 60)
    logger.info("Configuration:")
    for key, value in config.to_dict().items():
        logger.info(f"  {key}: {value}")
    logger.info("=" * 60)

    # Validate critical configuration
    if not config.openai_api_key:
        logger.warning("OPENAI_API_KEY not set - vector search will fail!")

    logger.info("MCP tools registered:")
    logger.info("  - write_note")
    logger.info("  - read_note")
    logger.info("  - search_knowledge_base")
    logger.info("  - process_inbox_item")
    logger.info("  - create_moc")
    logger.info("=" * 60)
    logger.info("Server ready on port {}".format(config.mcp_port))


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint - provides server information"""
    return {
        "service": "mcp-second-brain-server",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "mcp_tools": "/mcp/tools"
    }


@app.get("/health")
async def health() -> dict[str, Any]:
    """Health check endpoint for Docker healthcheck and monitoring"""
    return {
        "status": "healthy",
        "service": "mcp-second-brain-server",
        "version": "0.1.0",
        "config": config.to_dict()
    }


@app.get("/mcp/tools")
async def list_mcp_tools() -> dict[str, Any]:
    """List all available MCP tools with descriptions

    This endpoint provides documentation for all registered MCP tools.
    Useful for MCP clients and debugging.
    """
    return {
        "tools": [
            {
                "name": "write_note",
                "description": "Create a new note with convention enforcement",
                "parameters": {
                    "title": "Note title",
                    "content": "Markdown content",
                    "folder": "Folder path (e.g., '01 - Notes')",
                    "note_type": "Note type (must match folder)",
                    "tags": "List of tags (lowercase-hyphenated)"
                }
            },
            {
                "name": "read_note",
                "description": "Read a note by its ID",
                "parameters": {
                    "note_id": "14-char note ID (YYYYMMDDHHmmss) or permalink"
                }
            },
            {
                "name": "search_knowledge_base",
                "description": "Search vault using vector similarity",
                "parameters": {
                    "query": "Search query (2-5 keywords recommended)",
                    "source_id": "Optional filter to specific folder",
                    "match_count": "Number of results (max 20, default: 5)"
                }
            },
            {
                "name": "process_inbox_item",
                "description": "Process inbox item with automatic routing and tagging",
                "parameters": {
                    "title": "Item title",
                    "content": "Item content"
                }
            },
            {
                "name": "create_moc",
                "description": "Create a Map of Content (MOC) for a tag cluster",
                "parameters": {
                    "tag": "Tag to create MOC for",
                    "threshold": "Minimum note count (default: 12)",
                    "dry_run": "If True, return preview without creating"
                }
            }
        ]
    }


@app.post("/mcp/tools/write_note")
async def mcp_write_note(
    title: str,
    content: str,
    folder: str,
    note_type: str,
    tags: list[str]
) -> dict[str, Any]:
    """MCP tool endpoint: Create a new note"""
    try:
        result = await write_note(title, content, folder, note_type, tags)
        return result
    except Exception as e:
        logger.error(f"write_note failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/tools/read_note")
async def mcp_read_note(note_id: str) -> dict[str, Any]:
    """MCP tool endpoint: Read a note"""
    try:
        result = await read_note(note_id)
        if result is None:
            raise FileNotFoundError(f"Note not found: {note_id}")
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"read_note failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/tools/search_knowledge_base")
async def mcp_search_knowledge_base(
    query: str,
    source_id: str | None = None,
    match_count: int = 5
) -> dict[str, Any]:
    """MCP tool endpoint: Search vault using vector similarity"""
    try:
        result = await search_knowledge_base(query, source_id, match_count)
        return result
    except Exception as e:
        logger.error(f"search_knowledge_base failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/tools/process_inbox_item")
async def mcp_process_inbox_item(
    title: str,
    content: str
) -> dict[str, Any]:
    """MCP tool endpoint: Process inbox item with automatic routing"""
    try:
        result = await process_inbox_item(title, content)
        return result
    except Exception as e:
        logger.error(f"process_inbox_item failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/tools/create_moc")
async def mcp_create_moc(
    tag: str,
    threshold: int | None = None,
    dry_run: bool = False
) -> dict[str, Any]:
    """MCP tool endpoint: Create MOC for tag cluster"""
    try:
        result = await create_moc(tag, threshold, dry_run)
        return result
    except Exception as e:
        logger.error(f"create_moc failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting MCP Second Brain Server on port {config.mcp_port}")
    uvicorn.run(app, host="0.0.0.0", port=config.mcp_port)
