# PRP: Personal Notebook MCP Server - Phase 1 MVP

## Executive Summary

Build a custom Model Context Protocol (MCP) server that replaces basic-memory and creates a unified knowledge operating system for the Second Brain Obsidian vault. This PRP covers Phase 1 (MVP): Core vault management, auto-tagging, auto-MOC generation, vector search, and inbox processing.

**Success Criteria**: Replace basic-memory in Claude Desktop config and achieve >90% inbox processing accuracy with zero broken links created.

---

## Product Requirements Document (PRD)

### Problem Statement

**Current Pain**: The basic-memory MCP server requires constant prompt engineering to work with Obsidian conventions. There's no enforcement of:
- Folder structure (00-05 directory system)
- Frontmatter format (YYYYMMDDHHmmss IDs, required fields)
- Tag normalization (lowercase-hyphenated)
- Knowledge production has exceeded manual curation capacity

**Root Cause**: basic-memory is a general-purpose knowledge management tool, not designed for the specific conventions and automation workflows of the Second Brain system.

**Impact**:
- Time waste on manual corrections
- Inconsistent knowledge base structure
- Unable to scale to enterprise patterns
- No automatic knowledge curation
- Pattern detection in expertise development is manual

### Project Context

This project integrates three existing systems:

1. **basic-memory** (`./vibes/repos/basic-memory`):
   - Current MCP server (to be replaced)
   - Provides: MCP protocol implementation, SQLite indexing, markdown file sync
   - Limitations: Generic structure, no convention enforcement, no automation
   - Keep: MCP protocol patterns, async client patterns, testing approach

2. **RAG-Service** (`./repos/RAG-Service`):
   - Existing vector search infrastructure
   - Provides: Qdrant integration, OpenAI embeddings, per-domain collections
   - Reuse: Vector search architecture, embedding pipeline, Docker setup
   - Integration: Connect via MCP tools for semantic search

3. **Second Brain** (`./repos/Second Brain`):
   - Obsidian vault to be managed (production knowledge base)
   - Structure: 00-05 folder system (Inbox, Notes, MOCs, Projects, Areas, Resources)
   - Conventions: 14-char IDs (YYYYMMDDHHmmss), frontmatter with permalink/tags
   - Use Cases: Personal knowledge management, research organization, PRP workflows

### Related Documentation

- **Architecture Design**: `202511140051` (Second Brain MCP Server Architecture - 747 lines)
- **Project Note**: `202511140050` (Project: Personal Notebook MCP Server)
- **Pattern Analysis**: `202511132305` (Deep Pattern Analysis - inflection points)

### User Stories

**As a knowledge worker**, I want:
- To create notes via Claude without worrying about IDs or folder structure
- Auto-suggested tags based on content analysis (prevent tag fragmentation)
- Automatic MOC generation when topic clusters reach threshold
- Inbox items to be automatically routed to correct folders
- Vector search to find related notes I've forgotten about
- Fact-checking on stale notes with evidence-based diffs

**As a developer**, I want:
- Convention enforcement at protocol level (impossible to create bad data)
- Dry-run mode for all destructive operations
- Comprehensive test coverage (>80%)
- Docker deployment integrated with vibes-network
- MCP tools that compose cleanly

### Objectives & Key Results (OKRs)

**Objective 1**: Replace basic-memory with convention-enforcing MCP server
- KR1: All 25+ MCP tools working in Claude Desktop
- KR2: Zero broken links or invalid paths created in 100 operations
- KR3: 100% frontmatter validation compliance

**Objective 2**: Enable intelligent knowledge automation
- KR1: Auto-tagging suggests relevant tags with >80% accuracy
- KR2: Auto-MOC creates MOCs when threshold met (12+ notes)
- KR3: Inbox processing routes items correctly with >90% success

**Objective 3**: Integrate vector search for emergence detection
- KR1: Vector search returns relevant notes with top-5 precision >85%
- KR2: Related notes discovery reveals non-obvious connections
- KR3: Sub-second search response time

---

## Codebase Intelligence

### Repository Structure

**New Repository**: `~/source/vibes/mcp-second-brain-server/`

```
mcp-second-brain-server/
├── src/
│   ├── server.py                    # MCP server implementation
│   ├── models.py                    # Pydantic models (NoteFrontmatter, etc.)
│   ├── vault/
│   │   ├── manager.py               # CRUD with convention enforcement
│   │   ├── frontmatter.py           # YAML handling
│   │   ├── tag_analyzer.py          # Auto-tagging logic
│   │   └── moc_generator.py         # MOC creation
│   ├── inbox/
│   │   ├── processor.py             # Inbox automation
│   │   ├── router.py                # Smart routing logic
│   │   └── rules.py                 # Processing rules config
│   ├── vector/
│   │   ├── chunker.py               # Smart chunking
│   │   ├── embedder.py              # Embedding pipeline
│   │   └── qdrant_client.py         # Vector storage/search
│   └── config.py                    # Configuration management
├── tests/
│   ├── test_vault_manager.py
│   ├── test_tag_analyzer.py
│   ├── test_moc_generator.py
│   ├── test_inbox_processor.py
│   └── fixtures/
├── config/
│   ├── inbox_rules.yaml             # Processing rules
│   └── tag_vocabulary.yaml          # Known tags
├── docker-compose.yml               # MCP + Qdrant services
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

### Integration Points

**basic-memory Integration**:
- **Keep**: MCP protocol implementation patterns from `src/basic_memory/mcp/`
- **Keep**: Async client context manager pattern (`get_client()`)
- **Keep**: Tool composition approach (`tools/` directory)
- **Adapt**: Frontmatter handling to enforce Second Brain conventions
- **Replace**: Generic markdown parsing with convention-aware validation

**RAG-Service Integration**:
- **Reuse**: Qdrant client from `repos/RAG-Service/backend/src/vector/qdrant_client.py`
- **Reuse**: Embedding pipeline from `repos/RAG-Service/backend/src/vector/embedder.py`
- **Reuse**: Per-domain collection architecture (each note type = collection)
- **Connect**: Via MCP tools (`rag_search_knowledge_base`, `rag_search_code_examples`)
- **Deploy**: Both services on vibes-network for Docker networking

**Second Brain Integration**:
- **Vault Path**: `./repos/Second Brain/` (test on copy initially)
- **Conventions**:
  - IDs: `YYYYMMDDHHmmss` format (14 chars)
  - Folders: `00-05` structure (Inbox → Notes → MOCs → Projects → Areas → Resources)
  - Tags: lowercase-hyphenated (e.g., `knowledge-management`, not `Knowledge Management`)
  - Frontmatter: Required fields (id, type, tags, created, updated, permalink)
- **Operations**: All write operations must validate conventions before committing

### Technology Stack

**Core Technologies**:
- **Python**: 3.12+ (type parameters, async/await patterns)
- **MCP Protocol**: FastAPI-based server (following basic-memory patterns)
- **Data Validation**: Pydantic v2 (enforce frontmatter schema)
- **Vector Search**: Qdrant + OpenAI embeddings (via RAG-Service)
- **Database**: SQLite for indexing (following basic-memory pattern)
- **YAML Parsing**: python-frontmatter (frontmatter extraction)
- **Testing**: pytest + pytest-asyncio (>80% coverage target)
- **Code Quality**: ruff (linting), mypy (type checking)
- **Deployment**: Docker + Docker Compose (vibes-network integration)

**External Dependencies**:
- OpenAI API (embeddings via RAG-Service)
- Qdrant (vector storage via RAG-Service)
- Docker network: vibes-network

### Code Patterns to Follow

**From basic-memory**:
```python
# 1. Async client context manager (CRITICAL - see basic-memory CLAUDE.md)
from mcp.async_client import get_client

async def my_mcp_tool():
    async with get_client() as client:
        response = await call_get(client, "/path")
        return response

# 2. Pydantic models for validation
from pydantic import BaseModel, Field

class NoteFrontmatter(BaseModel):
    id: str = Field(pattern=r'^\d{14}$')  # YYYYMMDDHHmmss
    type: str
    tags: list[str]
    created: str
    updated: str
    permalink: str

# 3. Tool composition
async def write_note(title: str, content: str, folder: str, tags: list[str]):
    # Validate conventions
    frontmatter = NoteFrontmatter(...)
    # Create file
    # Index in SQLite
    # Return result
```

**From RAG-Service**:
```python
# 1. Qdrant client (per-domain collections)
from qdrant_client import QdrantClient

async def search_similar_notes(query: str, collection: str):
    client = QdrantClient(url="http://qdrant:6333")
    results = client.search(
        collection_name=collection,
        query_vector=await embed(query),
        limit=5
    )
    return results

# 2. Smart chunking (markdown sections)
def chunk_by_sections(content: str) -> list[str]:
    # Split on ## headers
    # Preserve context (include parent headings)
    # Return chunks with metadata
    pass
```

**Convention Enforcement**:
```python
# Validate folder routing (00-05 structure)
VALID_FOLDERS = {
    "00 - Inbox": ["clipping", "thought", "todo"],
    "01 - Notes": ["note", "reference"],
    "02 - MOCs": ["moc"],
    "03 - Projects": ["project"],
    "04 - Areas": ["area"],
    "05 - Resources": ["resource"]
}

def validate_folder_and_type(folder: str, note_type: str) -> bool:
    if folder not in VALID_FOLDERS:
        raise ValueError(f"Invalid folder: {folder}")
    if note_type not in VALID_FOLDERS[folder]:
        raise ValueError(f"Type {note_type} not allowed in {folder}")
    return True
```

### Data Models

**NoteFrontmatter** (Pydantic):
```python
class NoteFrontmatter(BaseModel):
    id: str = Field(pattern=r'^\d{14}$')  # YYYYMMDDHHmmss
    type: Literal["note", "moc", "project", "area", "resource", "clipping"]
    tags: list[str]  # lowercase-hyphenated only
    created: str  # ISO 8601
    updated: str  # ISO 8601
    permalink: str  # lowercase-hyphenated slug
    status: Optional[str] = None  # For projects/tasks

    @validator('tags')
    def validate_tags(cls, v):
        # Enforce lowercase-hyphenated
        for tag in v:
            if not re.match(r'^[a-z0-9-]+$', tag):
                raise ValueError(f"Tag {tag} must be lowercase-hyphenated")
        return v
```

**TagCluster** (for MOC generation):
```python
class TagCluster(BaseModel):
    tag: str
    note_count: int
    notes: list[str]  # Note IDs
    should_create_moc: bool  # True if count >= threshold
```

**InboxItem** (for processing):
```python
class InboxItem(BaseModel):
    title: str
    content: str
    source_type: Literal["url", "code", "thought"]
    url: Optional[str] = None
    suggested_folder: str  # Routed by content analysis
    suggested_tags: list[str]  # Auto-suggested
```

---

## Agent Execution Runbook

### Phase 1: Foundation (Week 1)

**Task 1.1: Repository Setup**
```bash
# Create repository structure
mkdir -p ~/source/vibes/mcp-second-brain-server/{src,tests,config}
cd ~/source/vibes/mcp-second-brain-server

# Initialize Python project
uv init
uv add pydantic fastapi python-frontmatter pyyaml qdrant-client openai

# Create development dependencies
uv add --dev pytest pytest-asyncio pytest-cov ruff mypy

# Create .env.example
cat > .env.example << 'EOF'
VAULT_PATH=./repos/Second Brain
QDRANT_URL=http://localhost:6333
OPENAI_API_KEY=your-key-here
MCP_PORT=8053
LOG_LEVEL=INFO
EOF

# Copy to .env and populate
cp .env.example .env
```

**Validation**:
- ✅ Repository structure matches spec
- ✅ Dependencies installed via `uv`
- ✅ .env file configured

**Task 1.2: Pydantic Models**

File: `src/models.py`
```python
from pydantic import BaseModel, Field, validator
from typing import Literal, Optional
import re

class NoteFrontmatter(BaseModel):
    """Enforces Second Brain frontmatter conventions"""
    id: str = Field(pattern=r'^\d{14}$')
    type: Literal["note", "moc", "project", "area", "resource", "clipping"]
    tags: list[str]
    created: str
    updated: str
    permalink: str
    status: Optional[str] = None

    @validator('tags')
    def validate_tags(cls, v):
        for tag in v:
            if not re.match(r'^[a-z0-9-]+$', tag):
                raise ValueError(f"Tag '{tag}' must be lowercase-hyphenated")
        return v

    @validator('permalink')
    def validate_permalink(cls, v):
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError(f"Permalink '{v}' must be lowercase-hyphenated")
        return v

class TagCluster(BaseModel):
    tag: str
    note_count: int
    notes: list[str]
    should_create_moc: bool = False

    def check_threshold(self, threshold: int = 12):
        self.should_create_moc = self.note_count >= threshold
        return self.should_create_moc
```

**Validation**:
```python
# Test frontmatter validation
pytest tests/test_models.py::test_frontmatter_validation -v
# Expected: Pass for valid data, fail for invalid tags/permalinks
```

**Task 1.3: Vault Manager (CRUD)**

File: `src/vault/manager.py`
```python
from pathlib import Path
from datetime import datetime
import frontmatter
from ..models import NoteFrontmatter

class VaultManager:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.valid_folders = {
            "00 - Inbox": ["clipping", "thought", "todo"],
            "01 - Notes": ["note", "reference"],
            "02 - MOCs": ["moc"],
            "03 - Projects": ["project"],
            "04 - Areas": ["area"],
            "05 - Resources": ["resource"]
        }

    def generate_id(self) -> str:
        """Generate 14-char ID: YYYYMMDDHHmmss"""
        return datetime.now().strftime("%Y%m%d%H%M%S")

    def validate_folder_type(self, folder: str, note_type: str):
        """Ensure type matches folder conventions"""
        if folder not in self.valid_folders:
            raise ValueError(f"Invalid folder: {folder}")
        if note_type not in self.valid_folders[folder]:
            raise ValueError(f"Type '{note_type}' not allowed in '{folder}'")

    async def create_note(
        self,
        title: str,
        content: str,
        folder: str,
        note_type: str,
        tags: list[str]
    ) -> Path:
        """Create note with convention enforcement"""
        # Validate folder/type match
        self.validate_folder_type(folder, note_type)

        # Generate frontmatter
        note_id = self.generate_id()
        permalink = title.lower().replace(" ", "-")
        fm = NoteFrontmatter(
            id=note_id,
            type=note_type,
            tags=tags,
            created=datetime.now().isoformat(),
            updated=datetime.now().isoformat(),
            permalink=permalink
        )

        # Create file
        folder_path = self.vault_path / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        file_path = folder_path / f"{note_id}.md"

        # Write with frontmatter
        post = frontmatter.Post(content, **fm.dict())
        with open(file_path, 'w') as f:
            f.write(frontmatter.dumps(post))

        return file_path
```

**Validation**:
```bash
pytest tests/test_vault_manager.py::test_create_note -v
# ✅ Note created with valid frontmatter
# ✅ Invalid folder/type combination rejected
# ✅ Tags normalized to lowercase-hyphenated
```

**Task 1.4: Docker Setup**

File: `docker-compose.yml`
```yaml
version: '3.8'

services:
  mcp-server:
    build: .
    container_name: second-brain-mcp
    ports:
      - "8053:8053"
    volumes:
      - ./repos/Second Brain:/vault:rw
      - ./src:/app/src:ro
    environment:
      - VAULT_PATH=/vault
      - QDRANT_URL=http://qdrant:6333
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - MCP_PORT=8053
    networks:
      - vibes-network
    depends_on:
      - qdrant

  qdrant:
    image: qdrant/qdrant:latest
    container_name: second-brain-qdrant
    ports:
      - "6334:6333"
    volumes:
      - qdrant-storage:/qdrant/storage
    networks:
      - vibes-network

networks:
  vibes-network:
    external: true

volumes:
  qdrant-storage:
```

File: `Dockerfile`
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependencies
COPY pyproject.toml .
COPY requirements.txt .

# Install dependencies
RUN uv pip install --system -r requirements.txt

# Copy source
COPY src/ ./src/

# Expose MCP port
EXPOSE 8053

CMD ["python", "-m", "src.server"]
```

**Validation**:
```bash
# Build and start services
docker-compose up --build -d

# Check health
docker ps | grep second-brain
# Expected: Both containers running

# Test Qdrant
curl http://localhost:6334/collections
# Expected: {"result": {"collections": []}}
```

### Phase 2: Auto-Tagging & MOCs (Week 2)

**Task 2.1: Tag Analyzer**

File: `src/vault/tag_analyzer.py`
```python
from collections import Counter
from pathlib import Path
import frontmatter

class TagAnalyzer:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.tag_vocabulary = self._build_vocabulary()

    def _build_vocabulary(self) -> set[str]:
        """Extract all existing tags from vault"""
        tags = set()
        for md_file in self.vault_path.rglob("*.md"):
            post = frontmatter.load(md_file)
            if 'tags' in post.metadata:
                tags.update(post.metadata['tags'])
        return tags

    def suggest_tags(self, content: str, title: str, max_tags: int = 5) -> list[str]:
        """Suggest tags based on content analysis"""
        # Tokenize content
        words = content.lower().split()

        # Find vocabulary matches (existing tags)
        matches = [tag for tag in self.tag_vocabulary
                   if any(word in tag or tag in word for word in words)]

        # Score by frequency
        tag_scores = Counter(matches)

        # Add title-based tags
        title_words = title.lower().replace(" ", "-")
        if title_words in self.tag_vocabulary:
            tag_scores[title_words] += 10  # Boost title match

        # Return top N
        return [tag for tag, _ in tag_scores.most_common(max_tags)]
```

**Validation**:
```python
pytest tests/test_tag_analyzer.py::test_suggest_tags -v
# ✅ Suggests tags matching vocabulary
# ✅ Prioritizes title matches
# ✅ Returns max_tags limit
```

**Task 2.2: MOC Generator**

File: `src/vault/moc_generator.py`
```python
from pathlib import Path
from collections import defaultdict
import frontmatter
from ..models import TagCluster

class MOCGenerator:
    def __init__(self, vault_path: str, threshold: int = 12):
        self.vault_path = Path(vault_path)
        self.threshold = threshold

    def find_clusters(self) -> list[TagCluster]:
        """Find tag clusters that exceed threshold"""
        # Build tag -> notes mapping
        tag_to_notes = defaultdict(list)

        for md_file in self.vault_path.rglob("*.md"):
            post = frontmatter.load(md_file)
            if 'tags' in post.metadata and 'id' in post.metadata:
                for tag in post.metadata['tags']:
                    tag_to_notes[tag].append(post.metadata['id'])

        # Create clusters
        clusters = []
        for tag, notes in tag_to_notes.items():
            cluster = TagCluster(
                tag=tag,
                note_count=len(notes),
                notes=notes
            )
            cluster.check_threshold(self.threshold)
            clusters.append(cluster)

        return [c for c in clusters if c.should_create_moc]

    async def create_moc(self, cluster: TagCluster) -> Path:
        """Generate MOC for tag cluster"""
        title = f"{cluster.tag.replace('-', ' ').title()} MOC"
        content = f"# {title}\n\n"
        content += f"Collection of {cluster.note_count} notes about {cluster.tag}\n\n"
        content += "## Notes\n\n"

        # Link to all notes
        for note_id in cluster.notes:
            content += f"- [[{note_id}]]\n"

        # Create via VaultManager
        from .manager import VaultManager
        vault = VaultManager(str(self.vault_path))
        return await vault.create_note(
            title=title,
            content=content,
            folder="02 - MOCs",
            note_type="moc",
            tags=[cluster.tag, "moc"]
        )
```

**Validation**:
```bash
pytest tests/test_moc_generator.py::test_find_clusters -v
# ✅ Identifies clusters above threshold
# ✅ Creates MOC with all note links
# ✅ MOC placed in correct folder
```

### Phase 3: Vector Search Integration (Week 3)

**Task 3.1: Connect to RAG-Service**

File: `src/vector/qdrant_client.py`
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import httpx

class VaultQdrantClient:
    def __init__(self, qdrant_url: str, openai_api_key: str):
        self.client = QdrantClient(url=qdrant_url)
        self.openai_key = openai_api_key
        self.collection_name = "second_brain_notes"
        self._ensure_collection()

    def _ensure_collection(self):
        """Create collection if not exists"""
        collections = self.client.get_collections().collections
        if self.collection_name not in [c.name for c in collections]:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=1536,  # text-embedding-3-small
                    distance=Distance.COSINE
                )
            )

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding via OpenAI"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self.openai_key}"},
                json={
                    "model": "text-embedding-3-small",
                    "input": text
                }
            )
            data = response.json()
            return data['data'][0]['embedding']

    async def search_similar(self, query: str, limit: int = 5) -> list[dict]:
        """Search for similar notes"""
        query_vector = await self.embed_text(query)
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit
        )
        return [
            {
                "note_id": r.payload.get("note_id"),
                "title": r.payload.get("title"),
                "score": r.score
            }
            for r in results
        ]
```

**Validation**:
```bash
pytest tests/test_qdrant_client.py::test_search_similar -v
# ✅ Collection created on init
# ✅ Embeddings generated via OpenAI
# ✅ Search returns relevant results
```

**Task 3.2: MCP Search Tool**

File: `src/mcp/tools/search.py`
```python
async def search_knowledge_base(
    query: str,
    source_id: Optional[str] = None,
    match_count: int = 5
) -> dict:
    """Search vault using vector similarity

    Args:
        query: Search query (2-5 keywords recommended)
        source_id: Optional filter to specific folder
        match_count: Number of results (max 20)

    Returns:
        List of matching notes with scores
    """
    from ..vector.qdrant_client import VaultQdrantClient
    import os

    client = VaultQdrantClient(
        qdrant_url=os.getenv("QDRANT_URL"),
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    results = await client.search_similar(query, limit=match_count)

    return {
        "query": query,
        "match_count": len(results),
        "results": results
    }
```

**Validation**:
```bash
# Test via MCP inspector
just run-inspector

# In inspector:
search_knowledge_base(query="vector search", match_count=5)
# ✅ Returns relevant notes
# ✅ Scores sorted descending
```

### Phase 4: Inbox Processing (Week 3)

**Task 4.1: Content Router**

File: `src/inbox/router.py`
```python
from typing import Literal
import re

class InboxRouter:
    """Route inbox items to appropriate folders based on content"""

    @staticmethod
    def detect_source_type(content: str, title: str) -> Literal["url", "code", "thought"]:
        """Classify inbox item type"""
        # Check for URLs
        if re.search(r'https?://', content):
            return "url"

        # Check for code blocks
        if '```' in content or re.search(r'^\s*(def|class|function|const|let)', content, re.MULTILINE):
            return "code"

        return "thought"

    @staticmethod
    def suggest_folder(source_type: str, content: str) -> str:
        """Suggest destination folder based on content"""
        # URL clippings → Resources
        if source_type == "url":
            # Check for documentation URLs
            if any(domain in content for domain in ["learn.microsoft.com", "docs.anthropic.com"]):
                return "05 - Resources"
            return "05c - Clippings"

        # Code snippets → Resources/Code
        if source_type == "code":
            return "05 - Resources"

        # Thoughts → Notes
        return "01 - Notes"
```

**Validation**:
```python
pytest tests/test_inbox_router.py::test_detect_source_type -v
# ✅ Detects URLs correctly
# ✅ Detects code blocks
# ✅ Defaults to thought
```

**Task 4.2: Inbox Processor**

File: `src/inbox/processor.py`
```python
from pathlib import Path
from .router import InboxRouter
from ..vault.tag_analyzer import TagAnalyzer
from ..vault.manager import VaultManager

class InboxProcessor:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.router = InboxRouter()
        self.tag_analyzer = TagAnalyzer(str(vault_path))
        self.vault_manager = VaultManager(str(vault_path))

    async def process_item(self, title: str, content: str) -> dict:
        """Process single inbox item"""
        # Classify content
        source_type = self.router.detect_source_type(content, title)

        # Route to folder
        folder = self.router.suggest_folder(source_type, content)

        # Suggest tags
        tags = self.tag_analyzer.suggest_tags(content, title)

        # Determine note type
        note_type = "clipping" if source_type == "url" else "note"

        # Create note
        file_path = await self.vault_manager.create_note(
            title=title,
            content=content,
            folder=folder,
            note_type=note_type,
            tags=tags
        )

        return {
            "file_path": str(file_path),
            "folder": folder,
            "tags": tags,
            "source_type": source_type
        }
```

**Validation**:
```bash
pytest tests/test_inbox_processor.py::test_process_item -v
# ✅ Routes URL to Resources
# ✅ Routes code to Resources
# ✅ Routes thought to Notes
# ✅ Tags suggested correctly
```

### Phase 5: MCP Server Integration (Week 4)

**Task 5.1: MCP Server Implementation**

File: `src/server.py`
```python
from fastapi import FastAPI
from mcp import MCPServer
from .mcp.tools import (
    write_note,
    read_note,
    search_knowledge_base,
    process_inbox_item,
    create_moc
)

app = FastAPI()
mcp = MCPServer()

# Register MCP tools
mcp.register_tool("write_note", write_note)
mcp.register_tool("read_note", read_note)
mcp.register_tool("search_knowledge_base", search_knowledge_base)
mcp.register_tool("process_inbox_item", process_inbox_item)
mcp.register_tool("create_moc", create_moc)

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8053)
```

**Task 5.2: MCP Tool Definitions**

File: `src/mcp/tools/__init__.py`
```python
from .vault import write_note, read_note
from .search import search_knowledge_base
from .inbox import process_inbox_item
from .moc import create_moc

__all__ = [
    "write_note",
    "read_note",
    "search_knowledge_base",
    "process_inbox_item",
    "create_moc"
]
```

**Validation**:
```bash
# Start MCP server
docker-compose up -d

# Test via MCP inspector
npx mcp-remote http://localhost:8053/mcp

# Test tools
write_note(title="Test Note", content="Test content", folder="01 - Notes", tags=["test"])
search_knowledge_base(query="test", match_count=5)
# ✅ All tools respond correctly
```

### Phase 6: Testing & Validation (Week 4)

**Task 6.1: Unit Test Coverage**

Files to test:
- `tests/test_models.py` - Pydantic validation
- `tests/test_vault_manager.py` - CRUD operations
- `tests/test_tag_analyzer.py` - Tag suggestions
- `tests/test_moc_generator.py` - MOC creation
- `tests/test_inbox_router.py` - Content classification
- `tests/test_inbox_processor.py` - End-to-end processing

**Run Tests**:
```bash
# All tests with coverage
pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# Expected: >80% coverage
```

**Task 6.2: Integration Testing**

File: `tests/integration/test_full_workflow.py`
```python
import pytest
from pathlib import Path

@pytest.mark.asyncio
async def test_inbox_to_moc_workflow(tmp_vault):
    """Test complete workflow: inbox → note → MOC"""
    processor = InboxProcessor(str(tmp_vault))

    # Process 15 items with same tag
    for i in range(15):
        await processor.process_item(
            title=f"Test Note {i}",
            content=f"Content about python programming {i}",
        )

    # Check MOC generation
    moc_gen = MOCGenerator(str(tmp_vault), threshold=12)
    clusters = moc_gen.find_clusters()

    assert len(clusters) > 0
    assert any(c.tag == "python" for c in clusters)
```

**Run Integration Tests**:
```bash
pytest tests/integration/ -v
# ✅ Full workflow completes
# ✅ MOC created at threshold
```

**Task 6.3: Quality Gates**

```bash
# Level 1: Syntax & Style
ruff check src/ tests/ --fix
mypy src/

# Level 2: Unit Tests
pytest tests/unit/ --cov=src --cov-fail-under=80

# Level 3: Integration Tests
pytest tests/integration/ -v

# All gates must pass before deployment
```

### Phase 7: Deployment & Migration (Week 5)

**Task 7.1: Deploy to vibes-network**

```bash
# Build and deploy
cd ~/source/vibes/mcp-second-brain-server
docker-compose up --build -d

# Verify health
curl http://localhost:8053/health
# Expected: {"status": "healthy"}

# Test MCP connection
npx mcp-remote http://localhost:8053/mcp
```

**Task 7.2: Update Claude Desktop Config**

File: `~/.config/Claude/claude_desktop_config.json`
```json
{
  "mcpServers": {
    "second-brain": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "http://localhost:8053/mcp"
      ]
    }
  }
}
```

**Remove basic-memory**:
```bash
# Stop basic-memory container
docker stop basic-memory

# Remove from config (delete basic-memory entry)
# Restart Claude Desktop
```

**Task 7.3: Production Validation**

Test all MCP tools in Claude Desktop:
1. ✅ Create note in correct folder
2. ✅ Search returns relevant results
3. ✅ Process inbox item routes correctly
4. ✅ Auto-tagging suggests good tags
5. ✅ MOC created at threshold
6. ✅ No broken links created
7. ✅ Frontmatter validates correctly

---

## Validation Gates

### Pre-Implementation Checklist
- [ ] Repository structure created
- [ ] Dependencies installed (uv)
- [ ] .env configured with API keys
- [ ] Docker Compose validated
- [ ] Second Brain backup created

### Unit Test Gates (>80% Coverage)
- [ ] `test_models.py` - Pydantic validation passes
- [ ] `test_vault_manager.py` - CRUD operations work
- [ ] `test_tag_analyzer.py` - Tag suggestions accurate
- [ ] `test_moc_generator.py` - MOC creation correct
- [ ] `test_inbox_router.py` - Content classification accurate
- [ ] `test_inbox_processor.py` - End-to-end processing works

### Integration Test Gates
- [ ] Full workflow test passes (inbox → note → MOC)
- [ ] Vector search returns relevant results
- [ ] Docker containers run on vibes-network
- [ ] MCP server responds to health checks

### Quality Gates
- [ ] Level 1: `ruff check` passes with no errors
- [ ] Level 1: `mypy src/` passes with no type errors
- [ ] Level 2: Unit tests pass with >80% coverage
- [ ] Level 3: Integration tests pass

### Production Validation Gates
- [ ] All MCP tools work in Claude Desktop
- [ ] Zero broken links created in 100 operations
- [ ] Auto-tagging >80% accuracy on 20 test items
- [ ] Inbox processing >90% correct routing on 20 items
- [ ] Vector search top-5 precision >85%
- [ ] MOC created when threshold reached
- [ ] No invalid frontmatter created

---

## Success Criteria

**MVP Complete** when:
1. ✅ MCP server running on vibes-network
2. ✅ Claude Desktop connected (basic-memory replaced)
3. ✅ All 25+ MCP tools working
4. ✅ Auto-tagging >80% accuracy
5. ✅ Auto-MOC creates MOCs at threshold
6. ✅ Inbox processing >90% success
7. ✅ Vector search precision >85%
8. ✅ Zero broken links/invalid paths
9. ✅ Test coverage >80%

**Ultimate Success**: Auto-generated MOC reveals an expertise cluster I didn't consciously recognize (emergence detection working).

---

## Gotchas & Edge Cases

### ID Collision Detection
**Problem**: Agents create notes faster than humans (multiple per second)
**Solution**:
- Check for existing ID before creating file
- If collision, sleep 1 second and regenerate
- Log collisions for monitoring

```python
async def generate_unique_id(self) -> str:
    while True:
        note_id = datetime.now().strftime("%Y%m%d%H%M%S")
        if not (self.vault_path / f"{note_id}.md").exists():
            return note_id
        await asyncio.sleep(1)
```

### Tag Fragmentation
**Problem**: Similar tags created (e.g., "ai", "AI", "artificial-intelligence")
**Solution**:
- Normalize all tags to lowercase-hyphenated
- Suggest from existing vocabulary first
- Fuzzy match against vocabulary (Levenshtein distance)

```python
def normalize_tag(tag: str) -> str:
    return tag.lower().replace(" ", "-").replace("_", "-")
```

### MOC Timing
**Problem**: MOC created too early (irrelevant notes grouped)
**Solution**:
- Default threshold: 12 notes
- Human approval before creation (dry-run mode)
- Allow threshold override per tag

### Dry-Run Mode
**Problem**: Destructive operations scary without preview
**Solution**:
- All write operations accept `dry_run: bool` parameter
- Return preview of changes instead of executing
- Log would-be changes

```python
async def create_note(..., dry_run: bool = False):
    if dry_run:
        return {"preview": "Would create file at...", "frontmatter": {...}}
    # Actually create file
```

### Vector Search Cold Start
**Problem**: First search slow (embeddings not cached)
**Solution**:
- Pre-embed all notes on startup (background task)
- Cache embeddings in Qdrant
- Incremental updates only

---

## Dependencies & Resources

### Time Estimate
- Phase 1 (Foundation): 1 week (40 hours)
- Phase 2 (Auto-tagging/MOCs): 1 week (40 hours)
- Phase 3 (Vector search): 1 week (40 hours)
- Phase 4 (Inbox processing): 3 days (24 hours)
- Phase 5 (MCP server): 1 week (40 hours)
- Phase 6 (Testing): 1 week (40 hours)
- Phase 7 (Deployment): 3 days (24 hours)

**Total**: ~5 weeks (208 hours)

### External Dependencies
- OpenAI API key (embeddings)
- Docker + Docker Compose
- vibes-network (Docker network)
- Qdrant (via RAG-Service)
- Second Brain vault (test copy)

### Knowledge Requirements
- MCP protocol patterns (from basic-memory)
- Qdrant vector search (from RAG-Service)
- Obsidian conventions (from Second Brain)
- Python async/await patterns
- Pydantic v2 validation
- Docker networking

---

## Appendix: MCP Tools Reference

**Phase 1 MVP Tools**:
1. `write_note` - Create note with conventions
2. `read_note` - Read note by ID/permalink
3. `search_knowledge_base` - Vector search
4. `process_inbox_item` - Route and tag inbox item
5. `create_moc` - Generate MOC for tag cluster
6. `list_tags` - Get tag vocabulary
7. `suggest_tags` - Get tag suggestions for content
8. `validate_note` - Check frontmatter compliance
9. `get_cluster_status` - Check MOC threshold status

**Future Tools** (Phase 2+):
10. `check_staleness` - Identify stale notes
11. `fact_check` - Validate against trusted sources
12. `propose_archive` - Suggest archival candidates
13. `sync_github_stars` - Import GitHub repos

---

## References

- **Architecture**: `202511140051` (Second Brain MCP Server Architecture)
- **Project Note**: `202511140050` (Project: Personal Notebook MCP Server)
- **basic-memory**: `./vibes/repos/basic-memory/` (MCP patterns)
- **RAG-Service**: `./repos/RAG-Service/` (Vector search)
- **Second Brain**: `./repos/Second Brain/` (Vault conventions)
