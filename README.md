# Personal Notebook MCP Server

A custom Model Context Protocol (MCP) server that provides intelligent knowledge management for the Second Brain Obsidian vault with automatic convention enforcement.

## Overview

This MCP server replaces basic-memory with a specialized solution that:
- Enforces Second Brain conventions (14-char IDs, folder structure, frontmatter format)
- Provides auto-tagging based on content analysis
- Automatically generates MOCs when tag clusters reach threshold
- Integrates vector search for semantic knowledge discovery
- Processes inbox items with intelligent routing

## Features

### Phase 1 MVP
- **Convention Enforcement**: YYYYMMDDHHmmss IDs, 00-05 folder structure, lowercase-hyphenated tags
- **Vault Management**: CRUD operations with validation
- **Auto-Tagging**: Content-based tag suggestions using existing vocabulary
- **Auto-MOC Generation**: Automatic Map of Content creation when tag clusters exceed threshold
- **Vector Search**: Semantic search integration via Qdrant
- **Inbox Processing**: Smart routing and tag suggestion for inbox items

## Architecture

```
notebook-mcp/
├── src/
│   ├── server.py              # MCP server implementation
│   ├── models.py              # Pydantic models (NoteFrontmatter, etc.)
│   ├── vault/
│   │   ├── manager.py         # CRUD with convention enforcement
│   │   ├── tag_analyzer.py    # Auto-tagging logic
│   │   └── moc_generator.py   # MOC creation
│   ├── inbox/
│   │   ├── processor.py       # Inbox automation
│   │   └── router.py          # Smart routing logic
│   └── vector/
│       └── qdrant_client.py   # Vector storage/search
├── tests/                     # Unit and integration tests
├── config/                    # Configuration files
└── docker-compose.yml         # Docker services
```

## Requirements

- Python 3.12+
- Docker & Docker Compose
- OpenAI API key (for embeddings)
- Second Brain Obsidian vault

## Installation

1. Clone the repository
2. Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   ```

4. Start services:
   ```bash
   docker-compose up -d
   ```

## Configuration

### Environment Variables

- `VAULT_PATH`: Path to Second Brain vault (default: `./repos/Second Brain`)
- `QDRANT_URL`: Qdrant service URL (default: `http://localhost:6333`)
- `OPENAI_API_KEY`: OpenAI API key for embeddings
- `MCP_PORT`: MCP server port (default: `8053`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

## Second Brain Conventions

This server enforces the following conventions:

### File IDs
- Format: `YYYYMMDDHHmmss` (14 characters)
- Example: `20251114020000`

### Folder Structure
- `00 - Inbox`: Temporary storage, processing queue
- `01 - Notes`: Permanent notes, references
- `02 - MOCs`: Maps of Content (topic aggregations)
- `03 - Projects`: Active projects
- `04 - Areas`: Ongoing areas of responsibility
- `05 - Resources`: Reference materials, clippings

### Frontmatter
Required fields:
```yaml
id: "20251114020000"
type: "note"
tags: ["knowledge-management", "automation"]
created: "2025-11-14T02:00:00"
updated: "2025-11-14T02:00:00"
permalink: "my-note-title"
```

### Tags
- Format: lowercase-hyphenated
- Valid: `knowledge-management`, `python-programming`
- Invalid: `Knowledge Management`, `Python_Programming`

## MCP Tools

### Core Tools
- `write_note`: Create note with convention validation
- `read_note`: Read note by ID or permalink
- `search_knowledge_base`: Vector-based semantic search
- `process_inbox_item`: Route and tag inbox items
- `create_moc`: Generate MOC for tag cluster
- `list_tags`: Get existing tag vocabulary
- `suggest_tags`: Get tag suggestions for content

## Development

### Running Tests
```bash
# All tests with coverage
pytest --cov=src --cov-report=term-missing

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/
```

### Code Quality
```bash
# Linting
ruff check src/ tests/

# Type checking
mypy src/

# Format code
ruff format src/ tests/
```

## Deployment

### Docker Compose
```bash
docker-compose up --build -d
```

### Claude Desktop Integration
Add to `~/.config/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "second-brain": {
      "command": "npx",
      "args": ["mcp-remote", "http://localhost:8053/mcp"]
    }
  }
}
```

## Success Criteria

- Zero broken links created
- 100% frontmatter validation compliance
- >80% auto-tagging accuracy
- >90% inbox processing routing accuracy
- >85% vector search precision
- MOC generation at threshold (12+ notes)

## License

Private project - All rights reserved

## References

- **PRP**: `prps/INITIAL_personal_notebook_mcp.md`
- **basic-memory**: Reference MCP implementation
- **RAG-Service**: Vector search infrastructure
- **Second Brain**: Obsidian vault conventions
