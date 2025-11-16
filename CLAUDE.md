# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## CRITICAL: Vault Separation (READ THIS FIRST!)

There are **TWO SEPARATE VAULT SYSTEMS** in this project. Understanding this distinction is critical:

### Production Vault (Real Notebook)
- **Access Method**: Only via `mcp__basic-memory__*` MCP tools
- **Location**: Managed by basic-memory MCP server (NOT in this repository)
- **Purpose**: User's REAL personal knowledge base
- **IMPORTANT**: Only edit when user explicitly asks
- **Available Tools**:
  - `mcp__basic-memory__read_note` - Read notes by ID/permalink
  - `mcp__basic-memory__edit_note` - Edit existing notes
  - `mcp__basic-memory__write_note` - Create new notes
  - `mcp__basic-memory__search_notes` - Search knowledge base
  - `mcp__basic-memory__view_note` - View formatted notes

### Test Vaults (In Repository)
- **Location 1**: `./vault/Second Brain/` - Working test copy for development
- **Location 2**: `./vault/Second Brain - Copy/` - Pristine backup for restoration
- **Purpose**: Used by pytest, Docker, and local development
- **Safe to modify freely** - These are test copies
- **Accessed By**: Python code (VaultManager), test suite, Docker containers

### Golden Rule
- **basic-memory MCP tools** = Production vault (user's real data - be careful!)
- **./vault/ directories** = Test copies (safe to modify during development)
- **NEVER confuse the two systems**
- **NEVER use basic-memory tools for testing or development work**
- **ALWAYS use basic-memory tools to update project progress notes**

### When to Use Basic-Memory Tools
- Updating project tracking notes (e.g., `03-projects/03b-personal/project-personal-notebook-mcp`)
- Updating session handoff notes (e.g., `01-notes/01r-research/202511152142`)
- Reading research notes from user's vault for context
- When user explicitly asks to create/edit notes in their real vault
- Follow tagging guide: `~/source/vibes/.vibes/user-config/basic-memory-tagging-guide.md`

## Project Overview

**Personal Notebook MCP Server** - A Model Context Protocol (MCP) server that enforces Second Brain conventions for Obsidian vault management with auto-tagging, semantic search, and intelligent inbox processing.

**Language**: Python 3.12+
**Framework**: FastAPI (async MCP server)
**Key Dependencies**: Pydantic v2, Qdrant (vector DB), OpenAI (embeddings)

## Development Commands

### Testing
```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_vault_manager.py -v

# Run specific test
pytest tests/test_vault_manager.py::test_create_note_success -v

# Run tests without coverage report
pytest --no-cov
```

### Code Quality
```bash
# Type checking (strict mode enabled)
mypy src/

# Linting
ruff check src/ tests/

# Format code
ruff format src/ tests/
```

### Docker Operations
```bash
# Start services (MCP server + Qdrant)
docker-compose up -d

# View logs
docker-compose logs -f mcp-server

# Check service status
docker-compose ps

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up --build -d
```

### Local Development
```bash
# Install dependencies
pip install -e .

# Install dev dependencies
pip install -e ".[dev]"

# Run server locally (without Docker)
python -m src.server
```

## High-Level Architecture

### Core Data Flow
```
Claude Desktop → MCP Server (FastAPI) → MCP Tools → Core Components → Obsidian Vault
                                    ↘ Vector Search → Qdrant + OpenAI
```

### Component Structure

**Server Layer** (`src/server.py`)
- FastAPI-based MCP server exposing 5 async tools
- Health checks at `/health` and `/health/qdrant`
- Runs on port 8053 (configurable via MCP_PORT)

**MCP Tools Layer** (`src/mcp/tools/`)
- `write_note` - Create notes with convention enforcement
- `read_note` - Retrieve notes by ID/permalink
- `search_knowledge_base` - Semantic vector search
- `process_inbox_item` - Auto-route and auto-tag inbox items
- `create_moc` - Generate Maps of Content for tag clusters

**Core Components** (`src/vault/`, `src/inbox/`, `src/vector/`)
- **VaultManager** - CRUD operations with strict validation (folder/type compatibility, ID uniqueness, frontmatter compliance)
- **TagAnalyzer** - Builds vocabulary from existing vault, suggests tags to prevent fragmentation
- **MOCGenerator** - Creates Maps of Content when tag clusters reach threshold (default: 12 notes)
- **InboxRouter** - Classifies content as URL/code/thought and routes to appropriate folder
- **InboxProcessor** - Orchestrates inbox workflow (route → tag → create)
- **VaultQdrantClient** - Vector operations using OpenAI embeddings (text-embedding-3-small, 1536-dim)

**Data Models** (`src/models.py`)
- **NoteFrontmatter** - Pydantic model enforcing ID format, tag normalization, permalink format
- **TagCluster** - Tracks tag usage for MOC generation

### Convention Enforcement System

This codebase enforces strict Second Brain conventions at multiple layers:

1. **Pydantic Validators** (NoteFrontmatter model)
   - ID format: exactly 14 chars (YYYYMMDDHHmmss)
   - Tag format: lowercase-hyphenated only
   - Permalink format: lowercase-hyphenated

2. **VaultManager Validation**
   - Folder/type compatibility (e.g., `moc` type only in `02 - MOCs`)
   - ID uniqueness with collision detection
   - Frontmatter required fields

3. **Tag Vocabulary** (TagAnalyzer)
   - Suggests from existing tags first
   - Prevents fragmentation (ai, AI, artificial-intelligence)

4. **Folder Structure** (00-05 System)
   ```
   00 - Inbox      → clipping, thought, todo
   01 - Notes      → note, reference
   02 - MOCs       → moc
   03 - Projects   → project
   04 - Areas      → area
   05 - Resources  → resource, clipping
   ```

### Key Design Patterns

**Async Context Pattern**
- All MCP tools are async functions
- Return dictionaries (not objects) for MCP serialization
- Environment-based configuration with validation

**ID Collision Handling**
- `VaultManager.generate_unique_id()` includes retry logic
- Waits 1 second and regenerates if ID exists (handles multiple notes per second)

**Tag Normalization**
- All tags normalized via `normalize_tag()` before storage
- Converts spaces/underscores to hyphens, lowercase
- Prevents duplicate tags with different formats

**MOC Threshold Logic**
- Default: 12 notes minimum before creating MOC
- Prevents premature aggregation
- Supports `dry_run` mode for preview

## Configuration

### Environment Variables (`.env`)
```bash
VAULT_PATH=./repos/Second Brain        # Obsidian vault location
QDRANT_URL=http://localhost:6333       # Vector DB URL (Docker: http://qdrant:6333)
OPENAI_API_KEY=sk-proj-...             # Embeddings API key
MCP_PORT=8053                          # Server port
LOG_LEVEL=INFO                         # Logging verbosity
```

### Docker Volumes
- Vault mounted at `/vault` (read-write for note creation)
- Source code mounted at `/app/src` (read-only for hot reload)
- Qdrant storage persisted in named volume `second_brain_qdrant_data`

### Network
- Uses external network `vibes-network` for integration with other services
- Qdrant accessible at `http://qdrant:6333` internally, `http://localhost:6334` from host

## Testing Architecture

**Test Coverage**: 3,767 lines across 8 test suites

**Test Organization**:
- `tests/test_models.py` - Pydantic validation (frontmatter, tags, IDs)
- `tests/test_vault_manager.py` - CRUD operations, collision detection
- `tests/test_tag_analyzer.py` - Vocabulary building, tag suggestions
- `tests/test_moc_generator.py` - MOC creation, threshold logic
- `tests/test_inbox_router.py` - Content classification (URL/code/thought)
- `tests/test_inbox_processor.py` - End-to-end inbox workflow
- `tests/test_qdrant_client.py` - Vector operations, embeddings

**pytest Configuration** (`pyproject.toml`):
- `pythonpath = ["src", "tests"]` - Enables direct imports
- `asyncio_mode = "strict"` - Enforces proper async test patterns
- `--cov=src --cov-report term-missing` - Coverage with missing lines

**Common Test Patterns**:
- Use `tmp_path` fixture for isolated vault testing
- Mock `VaultQdrantClient` for tests not requiring vector search
- Test both success and error paths (validation failures, missing env vars)
- Async tests use `@pytest.mark.asyncio` decorator

## Important Implementation Details

### Frontmatter Parsing
- Uses `python-frontmatter` library for YAML parsing
- All notes MUST have frontmatter with required fields
- Pydantic validation occurs after frontmatter extraction

### Vector Search Configuration
- **Embedding Model**: `text-embedding-3-small` (1536 dimensions)
- **Similarity Metric**: Cosine similarity
- **Collection Name**: `second_brain_notes`
- **WARNING**: Dimension is hardcoded - changing model breaks existing vectors

### ID Generation
- Uses `datetime.now().strftime("%Y%m%d%H%M%S")`
- Collision detection checks filesystem before returning ID
- Retry logic includes 1-second sleep to ensure uniqueness

### Folder/Type Validation
```python
# Valid combinations (enforced by VaultManager.validate_folder_type())
FOLDER_TYPE_MAP = {
    "00 - Inbox": ["clipping", "thought", "todo"],
    "01 - Notes": ["note", "reference"],
    "02 - MOCs": ["moc"],
    "03 - Projects": ["project"],
    "04 - Areas": ["area"],
    "05 - Resources": ["resource", "clipping"],
}
```

### Tag Suggestion Algorithm
- Content analysis finds term matches in existing tag vocabulary
- Title-based matches boosted 10x
- Returns top 5 most relevant tags
- Fallback: generic tags if no vocabulary matches

## Success Criteria

Defined metrics from project spec:
- Zero broken links created
- 100% frontmatter validation compliance
- >80% auto-tagging accuracy
- >90% inbox processing routing accuracy
- >85% vector search precision
- MOC generation at threshold (12+ notes)

## Claude Desktop Integration

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

## Additional Documentation

- **Tool Reference**: `src/mcp/tools/README.md` (726 lines of comprehensive tool documentation)
- **Project Spec**: `prps/INITIAL_personal_notebook_mcp.md` (complete requirements and architecture)
- **README**: Project overview, installation, and configuration
