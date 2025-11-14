# MCP Tools for Second Brain Vault Operations

This directory contains MCP-compatible tool functions that expose Second Brain vault operations via the Model Context Protocol (MCP). All tools enforce Second Brain conventions and integrate with the vault's knowledge management system.

## Overview

The Second Brain MCP server provides 5 core tools for vault management:

1. **`write_note`** - Create notes with convention enforcement
2. **`read_note`** - Read notes by ID or permalink
3. **`search_knowledge_base`** - Semantic search via vector similarity
4. **`process_inbox_item`** - Route and tag inbox items automatically
5. **`create_moc`** - Generate Maps of Content for tag clusters

All tools are async functions that return structured dictionaries for MCP compatibility.

---

## Tool Reference

### 1. `write_note`

Create a new note in the vault with automatic ID generation and convention enforcement.

**Signature:**
```python
async def write_note(
    title: str,
    content: str,
    folder: str,
    note_type: str,
    tags: list[str]
) -> dict[str, Any]
```

**Parameters:**
- `title` (str): Note title (converted to lowercase-hyphenated permalink)
- `content` (str): Markdown content body
- `folder` (str): Folder path following Second Brain structure (see Folder Structure below)
- `note_type` (str): Note type that must match folder conventions (see Note Types below)
- `tags` (list[str]): Tags (automatically normalized to lowercase-hyphenated)

**Returns:**
```python
{
    "note_id": str,         # Auto-generated 14-char ID (YYYYMMDDHHmmss)
    "file_path": str,       # Full path to created file
    "folder": str,          # Folder location
    "permalink": str,       # Generated permalink
    "tags": list[str]       # Normalized tags
}
```

**Example:**
```python
result = await write_note(
    title="Vector Search Implementation",
    content="# Vector Search\n\nImplementation notes for RAG...",
    folder="01 - Notes",
    note_type="note",
    tags=["vector-search", "rag", "embeddings"]
)

# Returns:
# {
#     "note_id": "20251114153000",
#     "file_path": "/vault/01 - Notes/20251114153000.md",
#     "folder": "01 - Notes",
#     "permalink": "vector-search-implementation",
#     "tags": ["vector-search", "rag", "embeddings"]
# }
```

**Convention Enforcement:**
- ✅ Validates folder/type compatibility
- ✅ Generates unique 14-char ID (YYYYMMDDHHmmss)
- ✅ Normalizes tags to lowercase-hyphenated
- ✅ Creates valid frontmatter with all required fields
- ✅ Handles ID collision detection

**Raises:**
- `ValueError`: If title/content empty, folder/type mismatch, or invalid data
- `RuntimeError`: If VAULT_PATH environment variable not set

---

### 2. `read_note`

Read a note by its 14-char ID or permalink.

**Signature:**
```python
async def read_note(
    note_id: str
) -> dict[str, Any]
```

**Parameters:**
- `note_id` (str): 14-char note ID (YYYYMMDDHHmmss) or permalink

**Returns:**
```python
{
    "note_id": str,          # 14-char ID
    "title": str,            # Note title (from first H1 or filename)
    "content": str,          # Markdown content body
    "frontmatter": dict,     # Parsed frontmatter data
    "file_path": str         # Full path to file
}
```

**Example:**
```python
result = await read_note(note_id="20251114153000")

# Returns:
# {
#     "note_id": "20251114153000",
#     "title": "Vector Search Implementation",
#     "content": "# Vector Search\n\nImplementation notes...",
#     "frontmatter": {
#         "id": "20251114153000",
#         "type": "note",
#         "tags": ["vector-search", "rag", "embeddings"],
#         "created": "2025-11-14T15:30:00",
#         "updated": "2025-11-14T15:30:00",
#         "permalink": "vector-search-implementation"
#     },
#     "file_path": "/vault/01 - Notes/20251114153000.md"
# }
```

**Raises:**
- `ValueError`: If note_id is empty or invalid format
- `FileNotFoundError`: If note does not exist
- `RuntimeError`: If VAULT_PATH environment variable not set

---

### 3. `search_knowledge_base`

Search vault notes using semantic vector similarity via OpenAI embeddings and Qdrant.

**Signature:**
```python
async def search_knowledge_base(
    query: str,
    source_id: Optional[str] = None,
    match_count: int = 5
) -> dict[str, Any]
```

**Parameters:**
- `query` (str): Search query (2-5 keywords recommended for best results)
- `source_id` (Optional[str]): Filter to specific folder (NOT IMPLEMENTED YET - reserved for Phase 2)
- `match_count` (int): Number of results to return (max 20, default: 5)

**Returns:**
```python
{
    "query": str,           # Original search query
    "match_count": int,     # Number of results returned
    "results": [            # List of matching notes
        {
            "note_id": str,  # 14-char YYYYMMDDHHmmss ID
            "title": str,    # Note title
            "score": float   # Similarity score (0.0-1.0, higher is better)
        },
        ...
    ]
}
```

**Example:**
```python
results = await search_knowledge_base(
    query="vector search embeddings",
    match_count=5
)

# Returns:
# {
#     "query": "vector search embeddings",
#     "match_count": 3,
#     "results": [
#         {"note_id": "20251114020000", "title": "RAG Architecture", "score": 0.87},
#         {"note_id": "20251113150000", "title": "Embeddings Guide", "score": 0.75},
#         {"note_id": "20251112100000", "title": "Qdrant Setup", "score": 0.68}
#     ]
# }
```

**Best Practices:**
- Use 2-5 keywords for optimal results
- Results sorted by similarity score (descending)
- Scores range from 0.0 (no similarity) to 1.0 (perfect match)
- Typical good matches: score > 0.7

**Raises:**
- `ValueError`: If query empty or match_count invalid (must be 1-20)
- `RuntimeError`: If QDRANT_URL or OPENAI_API_KEY environment variables not set

---

### 4. `process_inbox_item`

Process an inbox item with automatic content classification, folder routing, and tag suggestion.

**Signature:**
```python
async def process_inbox_item(
    title: str,
    content: str
) -> dict[str, Any]
```

**Parameters:**
- `title` (str): Item title
- `content` (str): Item content (markdown, URL, code snippet, etc.)

**Returns:**
```python
{
    "note_id": str,         # Generated 14-char ID
    "file_path": str,       # Full path to created file
    "folder": str,          # Auto-routed folder
    "source_type": str,     # Detected type: "url" | "code" | "thought"
    "tags": list[str],      # Auto-suggested tags
    "note_type": str        # Note type: "clipping" | "note"
}
```

**Content Classification:**
- **URL**: Detected by `https?://` pattern → Routed to `05 - Resources` → Type: `clipping`
- **Code**: Detected by code blocks or programming keywords → Routed to `05 - Resources` → Type: `note`
- **Thought**: Default for plain text → Routed to `01 - Notes` → Type: `note`

**Example 1: URL Clipping**
```python
result = await process_inbox_item(
    title="RAG Architecture Guide",
    content="https://docs.anthropic.com/rag\n\nGreat explanation of RAG patterns..."
)

# Returns:
# {
#     "note_id": "20251114153500",
#     "file_path": "/vault/05 - Resources/20251114153500.md",
#     "folder": "05 - Resources",
#     "source_type": "url",
#     "tags": ["rag", "architecture", "documentation"],
#     "note_type": "clipping"
# }
```

**Example 2: Code Snippet**
```python
result = await process_inbox_item(
    title="Async Context Manager Pattern",
    content="```python\nasync def get_client():\n    async with client:\n        yield client\n```"
)

# Returns:
# {
#     "note_id": "20251114153600",
#     "file_path": "/vault/05 - Resources/20251114153600.md",
#     "folder": "05 - Resources",
#     "source_type": "code",
#     "tags": ["python", "async", "patterns"],
#     "note_type": "note"
# }
```

**Example 3: Thought/Note**
```python
result = await process_inbox_item(
    title="Vector Search Insights",
    content="Vector search enables semantic similarity by converting text to embeddings..."
)

# Returns:
# {
#     "note_id": "20251114153700",
#     "file_path": "/vault/01 - Notes/20251114153700.md",
#     "folder": "01 - Notes",
#     "source_type": "thought",
#     "tags": ["vector-search", "embeddings", "semantic-search"],
#     "note_type": "note"
# }
```

**Tag Suggestion:**
- Tags suggested from existing vault vocabulary (prevents tag fragmentation)
- Content analysis finds matches in existing tags
- Title-based tags boosted (10x weight)
- Returns top 5 most relevant tags

**Raises:**
- `ValueError`: If title or content empty
- `RuntimeError`: If VAULT_PATH environment variable not set

---

### 5. `create_moc`

Create a Map of Content (MOC) for a tag cluster when note count reaches threshold.

**Signature:**
```python
async def create_moc(
    tag: str,
    threshold: Optional[int] = None,
    dry_run: bool = False
) -> dict[str, Any]
```

**Parameters:**
- `tag` (str): Tag to create MOC for (automatically normalized to lowercase-hyphenated)
- `threshold` (Optional[int]): Minimum note count to create MOC (default: 12)
- `dry_run` (bool): If True, returns preview without creating file (default: False)

**Returns:**
```python
{
    "tag": str,              # Normalized tag name
    "note_count": int,       # Number of notes with this tag
    "threshold": int,        # Threshold used
    "should_create": bool,   # Whether note count >= threshold
    "moc_created": bool,     # Whether MOC was actually created
    "note_id": str,          # MOC note ID (only if created)
    "file_path": str,        # Path to MOC file (only if created)
    "preview": str           # Preview of MOC content (only if dry_run=True)
}
```

**Example 1: Dry Run (Threshold Not Met)**
```python
result = await create_moc(tag="vector-search", dry_run=True)

# Returns:
# {
#     "tag": "vector-search",
#     "note_count": 8,
#     "threshold": 12,
#     "should_create": False,
#     "moc_created": False,
#     "preview": "Would create MOC with 8 notes (threshold: 12)"
# }
```

**Example 2: Dry Run (Threshold Met)**
```python
result = await create_moc(tag="python", dry_run=True)

# Returns:
# {
#     "tag": "python",
#     "note_count": 15,
#     "threshold": 12,
#     "should_create": True,
#     "moc_created": False,
#     "preview": "# Python MOC\n\nCollection of 15 notes about python\n\n## Notes\n\n- [[20251114...]]\n- [[20251113...]]\n..."
# }
```

**Example 3: Create MOC (For Real)**
```python
result = await create_moc(tag="python")

# Returns:
# {
#     "tag": "python",
#     "note_count": 15,
#     "threshold": 12,
#     "should_create": True,
#     "moc_created": True,
#     "note_id": "20251114154000",
#     "file_path": "/vault/02 - MOCs/20251114154000.md"
# }
```

**Example 4: Custom Threshold**
```python
result = await create_moc(tag="experimental-ideas", threshold=5)

# Creates MOC when only 5 notes exist (instead of default 12)
```

**MOC Structure:**
- **Title**: Tag name converted to title case with " MOC" suffix
- **Content**: Summary + list of all note links using wiki-link syntax `[[note_id]]`
- **Location**: Always placed in `02 - MOCs` folder
- **Type**: `moc`
- **Tags**: Includes the cluster tag + `moc` tag

**Threshold Guidelines:**
- Default: 12 notes (prevents premature MOC creation)
- Adjust threshold per tag based on domain specificity
- Use dry_run mode to preview before committing

**Raises:**
- `ValueError`: If tag is empty or threshold < 1
- `RuntimeError`: If VAULT_PATH environment variable not set

---

## Second Brain Conventions Reference

All MCP tools enforce the following Second Brain conventions:

### Folder Structure (00-05 System)

```
00 - Inbox         → Clippings, thoughts, unprocessed items
01 - Notes         → Processed notes and references
02 - MOCs          → Maps of Content (knowledge hubs)
03 - Projects      → Active projects
04 - Areas         → Ongoing responsibilities
05 - Resources     → Reference materials, code snippets
```

### Note Types and Folder Compatibility

| Folder | Allowed Note Types |
|--------|-------------------|
| `00 - Inbox` | clipping, thought, todo |
| `01 - Notes` | note, reference |
| `02 - MOCs` | moc |
| `03 - Projects` | project |
| `04 - Areas` | area |
| `05 - Resources` | resource, clipping |

**Validation**: All `write_note` calls validate that `note_type` matches the target `folder`.

### ID Format

- **Format**: `YYYYMMDDHHmmss` (14 characters)
- **Example**: `20251114153045` (November 14, 2025 at 15:30:45)
- **Generation**: Auto-generated by `VaultManager.generate_id()`
- **Collision Detection**: If ID exists, waits 1 second and retries

### Tag Normalization

- **Format**: lowercase-hyphenated (no spaces, underscores, or uppercase)
- **Valid**: `vector-search`, `knowledge-management`, `python-async`
- **Invalid**: `Vector Search`, `knowledge_management`, `PythonAsync`
- **Auto-normalization**: All tags automatically converted via `normalize_tag()`

### Frontmatter Structure

All notes include YAML frontmatter with required fields:

```yaml
---
id: "20251114153000"
type: "note"
tags:
  - vector-search
  - embeddings
created: "2025-11-14T15:30:00"
updated: "2025-11-14T15:30:00"
permalink: "vector-search-implementation"
status: "active"  # Optional, for projects/tasks
---
```

**Required Fields**:
- `id`: 14-char timestamp ID
- `type`: Note type (must match folder)
- `tags`: List of lowercase-hyphenated tags
- `created`: ISO 8601 timestamp
- `updated`: ISO 8601 timestamp
- `permalink`: Lowercase-hyphenated slug

**Validation**: `NoteFrontmatter` Pydantic model enforces all conventions at write time.

---

## Architecture Patterns

### Async Context Pattern

All tools follow the basic-memory async pattern:

```python
async def tool_function(...):
    # 1. Validate inputs
    if not title or not title.strip():
        raise ValueError("Title cannot be empty")

    # 2. Get environment config
    vault_path = os.getenv("VAULT_PATH")
    if not vault_path:
        raise RuntimeError("VAULT_PATH not set")

    # 3. Initialize manager/client
    manager = VaultManager(vault_path)

    # 4. Execute operation
    result = await manager.operation(...)

    # 5. Return structured response
    return {"key": "value", ...}
```

### Structured Returns

All tools return dictionaries (not objects) for MCP serialization:

```python
# ✅ CORRECT - MCP-compatible
return {
    "note_id": "20251114153000",
    "file_path": "/vault/01 - Notes/20251114153000.md",
    "tags": ["vector-search"]
}

# ❌ WRONG - Objects not MCP-serializable
return NoteFrontmatter(id="20251114153000", ...)
```

### Error Handling

Tools use exceptions for validation and runtime errors:

```python
# Validation errors (client mistakes)
raise ValueError("Title cannot be empty")
raise ValueError("match_count must be between 1 and 20")

# Configuration errors (server setup issues)
raise RuntimeError("VAULT_PATH environment variable not set")

# Not found errors
raise FileNotFoundError(f"Note {note_id} does not exist")
```

### Logging

All tools log operations for debugging and monitoring:

```python
logger.info(f"MCP write_note: created note '{note_id}' in '{folder}'")
logger.error(f"MCP search_knowledge_base error: {e}", exc_info=True)
```

---

## Environment Variables

All tools require the following environment variables (configured in `.env`):

| Variable | Description | Required By |
|----------|-------------|-------------|
| `VAULT_PATH` | Path to Second Brain vault | All tools |
| `QDRANT_URL` | Qdrant vector DB URL | `search_knowledge_base` |
| `OPENAI_API_KEY` | OpenAI API key for embeddings | `search_knowledge_base` |

**Example `.env`**:
```bash
VAULT_PATH=/Users/username/repos/Second Brain
QDRANT_URL=http://localhost:6333
OPENAI_API_KEY=sk-proj-...
```

---

## Testing

### Unit Tests

Each tool has comprehensive unit tests in `tests/test_mcp_tools_*.py`:

```bash
# Test all tools
pytest tests/test_mcp_tools_*.py -v

# Test specific tool
pytest tests/test_mcp_tools_vault.py::test_write_note -v
```

### Integration Tests

Full workflow tests in `tests/integration/test_mcp_workflow.py`:

```bash
# Test complete inbox → note → MOC workflow
pytest tests/integration/test_mcp_workflow.py -v
```

### Manual Testing via MCP Inspector

```bash
# Start MCP server
docker-compose up -d

# Connect inspector
npx mcp-remote http://localhost:8053/mcp

# Test tools interactively
write_note(
    title="Test Note",
    content="Test content",
    folder="01 - Notes",
    note_type="note",
    tags=["test"]
)
```

---

## Related Documentation

- **PRP**: `prps/INITIAL_personal_notebook_mcp.md` (Complete project specification)
- **Architecture**: Second Brain vault conventions and folder structure
- **VaultManager**: `src/vault/manager.py` (Core CRUD operations)
- **Models**: `src/models.py` (Pydantic models for validation)
- **MCP Server**: `src/server.py` (Tool registration)

---

## Usage in Claude Desktop

Once the MCP server is running, these tools are available in Claude Desktop:

```json
// ~/.config/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "second-brain": {
      "command": "npx",
      "args": ["mcp-remote", "http://localhost:8053/mcp"]
    }
  }
}
```

**Example interactions:**

> **User**: "Create a note about vector search in my Second Brain"
>
> **Claude**: [Calls `write_note` with appropriate parameters]

> **User**: "Find notes related to RAG architecture"
>
> **Claude**: [Calls `search_knowledge_base` with query="RAG architecture"]

> **User**: "Process this article I saved: https://..."
>
> **Claude**: [Calls `process_inbox_item` with URL content]

---

## Future Enhancements (Phase 2+)

**Planned Tools**:
- `list_tags` - Get complete tag vocabulary
- `suggest_tags` - Get tag suggestions for content (without creating note)
- `validate_note` - Check frontmatter compliance
- `get_cluster_status` - Check MOC threshold status for all tags
- `check_staleness` - Identify notes not updated in N days
- `fact_check` - Validate claims against trusted sources
- `propose_archive` - Suggest archival candidates
- `sync_github_stars` - Import GitHub starred repos

**Folder Filtering**:
- `search_knowledge_base` will support `source_id` filtering by folder
- Maps source IDs to folder names for scoped search

---

## Gotchas & Best Practices

### ID Collision (Agents Create Notes Fast)

**Problem**: Multiple notes per second can cause ID collisions (same YYYYMMDDHHmmss timestamp)

**Solution**: `VaultManager.generate_unique_id()` includes collision detection:
```python
async def generate_unique_id(self) -> str:
    while True:
        note_id = datetime.now().strftime("%Y%m%d%H%M%S")
        if not (self.vault_path / f"{note_id}.md").exists():
            return note_id
        await asyncio.sleep(1)  # Wait 1 second and retry
```

### Tag Fragmentation

**Problem**: Similar tags created (`ai`, `AI`, `artificial-intelligence`, `Artificial Intelligence`)

**Solution**: All tags normalized via `normalize_tag()`:
```python
def normalize_tag(tag: str) -> str:
    return tag.lower().replace(" ", "-").replace("_", "-")
```

Tag suggestion uses existing vocabulary first to prevent fragmentation.

### MOC Timing

**Problem**: MOC created too early with unrelated notes

**Solution**:
- Default threshold: 12 notes (prevents premature creation)
- Use `dry_run=True` to preview before creating
- Adjust threshold per tag based on domain specificity

### Folder/Type Mismatch

**Problem**: Trying to create incompatible folder/type combinations

**Solution**: `VaultManager.validate_folder_type()` enforces compatibility:
```python
# ✅ VALID
write_note(..., folder="01 - Notes", note_type="note")

# ❌ INVALID - Raises ValueError
write_note(..., folder="01 - Notes", note_type="moc")
```

---

**Last Updated**: Task 5.2 (November 14, 2025)
**Reference**: prps/INITIAL_personal_notebook_mcp.md (Phase 5: MCP Server Integration)
