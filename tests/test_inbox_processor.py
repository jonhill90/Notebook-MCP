"""Tests for InboxProcessor end-to-end workflow.

This test suite validates the InboxProcessor's ability to:
1. Orchestrate complete inbox processing workflow
2. Correctly route URLs to Resources
3. Correctly route code to Resources
4. Correctly route thoughts to Notes
5. Suggest tags accurately
6. Create notes with proper conventions
7. Handle batch processing
8. Achieve >90% routing accuracy (PRP requirement)

The InboxProcessor is the primary integration point for inbox automation,
so comprehensive testing ensures production readiness.
"""

import pytest
import pytest_asyncio
from pathlib import Path
import tempfile
import shutil

from src.inbox.processor import InboxProcessor
from src.vault.manager import VaultManager


@pytest.fixture
def temp_vault():
    """Create a temporary vault for testing."""
    temp_dir = tempfile.mkdtemp()
    vault_path = Path(temp_dir) / "test_vault"
    vault_path.mkdir()

    # Create 3-level folder structure
    folders = [
        "00 - Inbox/00a - Active",
        "00 - Inbox/00b - Backlog",
        "00 - Inbox/00c - Clippings",
        "00 - Inbox/00d - Documents",
        "00 - Inbox/00r - Research",
        "00 - Inbox/00t - Thoughts",
        "01 - Notes/01a - Atomic",
        "01 - Notes/01m - Meetings",
        "01 - Notes/01r - Research",
        "02 - MOCs",
        "03 - Projects/03b - Personal",
        "03 - Projects/03c - Work",
        "03 - Projects/03p - PRPs",
        "04 - Areas",
        "05 - Resources/05c - Clippings",
        "05 - Resources/05d - Documents",
        "05 - Resources/05e - Examples",
        "05 - Resources/05l - Learning",
        "05 - Resources/05r - Repos",
    ]
    for folder in folders:
        (vault_path / folder).mkdir(parents=True)

    yield vault_path

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest_asyncio.fixture
async def vault_with_tags(temp_vault):
    """Create vault with existing notes to build tag vocabulary."""
    manager = VaultManager(str(temp_vault))

    # Create notes with common tags (using 3-level folder paths)
    await manager.create_note(
        title="Python Tutorial",
        content="Python programming basics",
        folder="01 - Notes/01a - Atomic",
        note_type="note",
        tags=["python", "programming", "tutorial"],
    )

    await manager.create_note(
        title="JavaScript Guide",
        content="JavaScript web development",
        folder="01 - Notes/01a - Atomic",
        note_type="note",
        tags=["javascript", "web-dev", "frontend"],
    )

    await manager.create_note(
        title="React Documentation",
        content="React hooks and components",
        folder="05 - Resources/05d - Documents",
        note_type="resource",
        tags=["react", "javascript", "frontend"],
    )

    await manager.create_note(
        title="Machine Learning",
        content="ML algorithms and models",
        folder="01 - Notes/01a - Atomic",
        note_type="note",
        tags=["machine-learning", "ai", "python"],
    )

    return temp_vault


class TestInboxProcessorInitialization:
    """Test InboxProcessor initialization."""

    def test_init_creates_components(self, temp_vault):
        """Test that initialization creates all required components."""
        processor = InboxProcessor(str(temp_vault))

        assert processor.vault_path == temp_vault
        assert processor.router is not None
        assert processor.tag_analyzer is not None
        assert processor.vault_manager is not None

    @pytest.mark.asyncio
    async def test_init_builds_vocabulary(self, vault_with_tags):
        """Test that vocabulary is built from existing notes."""
        processor = InboxProcessor(str(vault_with_tags))

        # Should have collected tags from existing notes
        vocab = processor.tag_analyzer.get_vocabulary()
        assert "python" in vocab
        assert "javascript" in vocab
        assert "react" in vocab
        assert "machine-learning" in vocab


class TestProcessURLClippings:
    """Test processing of URL clippings."""

    @pytest.mark.asyncio
    async def test_process_documentation_url(self, vault_with_tags):
        """Test processing documentation URL routes to Resources."""
        processor = InboxProcessor(str(vault_with_tags))

        result = await processor.process_item(
            title="Python Documentation",
            content="https://docs.python.org/3/tutorial/index.html"
        )

        assert result["source_type"] == "url"
        assert result["folder"] == "05 - Resources/05d - Documents"
        assert Path(result["file_path"]).exists()
        assert isinstance(result["tags"], list)

        # Verify note was created with correct type (resource for 05 - Resources/05d - Documents)
        note_id = Path(result["file_path"]).stem
        note_data = await processor.vault_manager.read_note(note_id)
        assert note_data["frontmatter"]["type"] == "resource"

    @pytest.mark.asyncio
    async def test_process_blog_url(self, vault_with_tags):
        """Test processing blog URL routes to Clippings."""
        processor = InboxProcessor(str(vault_with_tags))

        result = await processor.process_item(
            title="Interesting Blog Post",
            content="https://someblog.com/great-article"
        )

        assert result["source_type"] == "url"
        assert result["folder"] == "05 - Resources/05c - Clippings"
        assert Path(result["file_path"]).exists()

        # Verify note type is 'clipping' for Resources/Clippings folder
        note_id = Path(result["file_path"]).stem
        note_data = await processor.vault_manager.read_note(note_id)
        assert note_data["frontmatter"]["type"] == "resource"

    @pytest.mark.asyncio
    async def test_process_react_docs_url(self, vault_with_tags):
        """Test React documentation routes to Resources."""
        processor = InboxProcessor(str(vault_with_tags))

        result = await processor.process_item(
            title="React Hooks",
            content="https://reactjs.org/docs/hooks-intro.html"
        )

        assert result["source_type"] == "url"
        assert result["folder"] == "05 - Resources/05d - Documents"
        # Should suggest react tag from vocabulary
        assert "react" in result["tags"] or "javascript" in result["tags"]

    @pytest.mark.asyncio
    async def test_process_mdn_docs_url(self, vault_with_tags):
        """Test MDN documentation routes to Resources."""
        processor = InboxProcessor(str(vault_with_tags))

        result = await processor.process_item(
            title="JavaScript Promises",
            content="https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise"
        )

        assert result["source_type"] == "url"
        assert result["folder"] == "05 - Resources/05d - Documents"


class TestProcessCodeSnippets:
    """Test processing of code snippets."""

    @pytest.mark.asyncio
    async def test_process_python_code_block(self, vault_with_tags):
        """Test Python code block routes to Resources."""
        processor = InboxProcessor(str(vault_with_tags))

        result = await processor.process_item(
            title="Python Function",
            content="""
```python
def calculate_sum(a, b):
    return a + b
```
            """
        )

        assert result["source_type"] == "code"
        assert result["folder"] == "05 - Resources/05e - Examples"
        assert Path(result["file_path"]).exists()

        # Verify note type is 'resource' (for 05 - Resources/05e - Examples folder)
        note_id = Path(result["file_path"]).stem
        note_data = await processor.vault_manager.read_note(note_id)
        assert note_data["frontmatter"]["type"] == "resource"

    @pytest.mark.asyncio
    async def test_process_python_code_with_tags(self, vault_with_tags):
        """Test Python code gets relevant tag suggestions."""
        processor = InboxProcessor(str(vault_with_tags))

        result = await processor.process_item(
            title="Python Async Example",
            content="async def fetch_data():\n    return await api.get()"
        )

        assert result["source_type"] == "code"
        assert result["folder"] == "05 - Resources/05e - Examples"
        # Should suggest python tag from vocabulary
        assert "python" in result["tags"]

    @pytest.mark.asyncio
    async def test_process_javascript_code(self, vault_with_tags):
        """Test JavaScript code routes to Resources."""
        processor = InboxProcessor(str(vault_with_tags))

        result = await processor.process_item(
            title="JS Function",
            content="const greet = (name) => console.log(`Hello ${name}`);"
        )

        assert result["source_type"] == "code"
        assert result["folder"] == "05 - Resources/05e - Examples"

    @pytest.mark.asyncio
    async def test_process_class_definition(self, vault_with_tags):
        """Test class definition routes to Resources."""
        processor = InboxProcessor(str(vault_with_tags))

        result = await processor.process_item(
            title="Calculator Class",
            content="class Calculator:\n    def add(self, x, y):\n        return x + y"
        )

        assert result["source_type"] == "code"
        assert result["folder"] == "05 - Resources/05e - Examples"


class TestProcessThoughts:
    """Test processing of general thoughts/notes."""

    @pytest.mark.asyncio
    async def test_process_simple_thought(self, vault_with_tags):
        """Test simple thought routes to Notes."""
        processor = InboxProcessor(str(vault_with_tags))

        result = await processor.process_item(
            title="Research Idea",
            content="Need to explore vector databases for knowledge management"
        )

        assert result["source_type"] == "thought"
        assert result["folder"] == "01 - Notes/01a - Atomic"
        assert Path(result["file_path"]).exists()

        # Verify note type is 'note'
        note_id = Path(result["file_path"]).stem
        note_data = await processor.vault_manager.read_note(note_id)
        assert note_data["frontmatter"]["type"] == "note"

    @pytest.mark.asyncio
    async def test_process_markdown_thought(self, vault_with_tags):
        """Test markdown thought routes to Notes."""
        processor = InboxProcessor(str(vault_with_tags))

        result = await processor.process_item(
            title="Research Notes",
            content="""
# Research Ideas

- Explore knowledge graphs
- Investigate vector search
- Try semantic clustering
            """
        )

        assert result["source_type"] == "thought"
        assert result["folder"] == "01 - Notes/01a - Atomic"

    @pytest.mark.asyncio
    async def test_process_thought_with_relevant_tags(self, vault_with_tags):
        """Test thought gets relevant tag suggestions."""
        processor = InboxProcessor(str(vault_with_tags))

        result = await processor.process_item(
            title="Python Learning Path",
            content="Create a structured learning path for Python programming"
        )

        assert result["source_type"] == "thought"
        assert result["folder"] == "01 - Notes/01a - Atomic"
        # Should suggest python-related tags from vocabulary
        assert "python" in result["tags"] or "programming" in result["tags"]


class TestTagSuggestion:
    """Test tag suggestion integration."""

    @pytest.mark.asyncio
    async def test_tags_suggested_from_vocabulary(self, vault_with_tags):
        """Test that tags are suggested from existing vocabulary."""
        processor = InboxProcessor(str(vault_with_tags))

        result = await processor.process_item(
            title="Python Machine Learning",
            content="Tutorial about machine learning with Python libraries"
        )

        # Should suggest tags that exist in vocabulary
        vocab = processor.tag_analyzer.get_vocabulary()
        for tag in result["tags"]:
            assert tag in vocab, f"Tag '{tag}' not in vocabulary"

    @pytest.mark.asyncio
    async def test_max_tags_limit(self, vault_with_tags):
        """Test that max_tags limit is respected."""
        processor = InboxProcessor(str(vault_with_tags))

        result = await processor.process_item(
            title="Programming Tutorial",
            content="Python JavaScript React machine learning tutorial",
            max_tags=3
        )

        assert len(result["tags"]) <= 3

    @pytest.mark.asyncio
    async def test_tags_normalized(self, vault_with_tags):
        """Test that all tags are normalized to lowercase-hyphenated."""
        processor = InboxProcessor(str(vault_with_tags))

        result = await processor.process_item(
            title="Test Note",
            content="Some content"
        )

        # All tags should be lowercase-hyphenated
        for tag in result["tags"]:
            assert tag.islower() or '-' in tag
            assert ' ' not in tag
            assert '_' not in tag


class TestEndToEndWorkflow:
    """Test complete end-to-end workflow."""

    @pytest.mark.asyncio
    async def test_complete_url_workflow(self, vault_with_tags):
        """Test complete workflow for URL clipping."""
        processor = InboxProcessor(str(vault_with_tags))

        result = await processor.process_item(
            title="Claude Documentation",
            content="https://docs.anthropic.com/claude/reference"
        )

        # Verify all steps completed
        assert result["source_type"] == "url"
        assert result["folder"] == "05 - Resources/05d - Documents"
        assert isinstance(result["tags"], list)
        assert Path(result["file_path"]).exists()

        # Verify note was created correctly
        note_path = Path(result["file_path"])
        assert "05 - Resources" in str(note_path)
        assert note_path.suffix == ".md"

        # Verify note content
        note_id = note_path.stem
        note_data = await processor.vault_manager.read_note(note_id)
        assert note_data is not None
        assert "Claude Documentation" in note_data["content"]
        assert "docs.anthropic.com" in note_data["content"]

    @pytest.mark.asyncio
    async def test_complete_code_workflow(self, vault_with_tags):
        """Test complete workflow for code snippet."""
        processor = InboxProcessor(str(vault_with_tags))

        code_content = """
```python
async def process_data(items):
    results = []
    for item in items:
        result = await transform(item)
        results.append(result)
    return results
```
        """

        result = await processor.process_item(
            title="Async Processing Example",
            content=code_content
        )

        assert result["source_type"] == "code"
        assert result["folder"] == "05 - Resources/05e - Examples"
        assert Path(result["file_path"]).exists()

        # Verify note type is 'resource' (for 05 - Resources/05e - Examples folder)
        note_id = Path(result["file_path"]).stem
        note_data = await processor.vault_manager.read_note(note_id)
        assert note_data["frontmatter"]["type"] == "resource"
        assert code_content.strip() in note_data["content"]

    @pytest.mark.asyncio
    async def test_complete_thought_workflow(self, vault_with_tags):
        """Test complete workflow for thought/note."""
        processor = InboxProcessor(str(vault_with_tags))

        result = await processor.process_item(
            title="Python Programming Ideas",
            content="Develop a comprehensive Python tutorial covering async programming"
        )

        assert result["source_type"] == "thought"
        assert result["folder"] == "01 - Notes/01a - Atomic"
        assert Path(result["file_path"]).exists()

        # Verify frontmatter
        note_id = Path(result["file_path"]).stem
        note_data = await processor.vault_manager.read_note(note_id)
        assert note_data["frontmatter"]["type"] == "note"
        # Tags suggested from vocabulary (python, programming should match)
        assert isinstance(note_data["frontmatter"]["tags"], list)


class TestBatchProcessing:
    """Test batch processing functionality."""

    @pytest.mark.asyncio
    async def test_process_batch_multiple_items(self, vault_with_tags):
        """Test processing multiple items in batch."""
        processor = InboxProcessor(str(vault_with_tags))

        items = [
            {"title": "URL 1", "content": "https://docs.python.org/tutorial"},
            {"title": "Code 1", "content": "def test(): pass"},
            {"title": "Thought 1", "content": "Research idea about AI"},
        ]

        results = await processor.process_batch(items)

        assert len(results) == 3
        assert results[0]["source_type"] == "url"
        assert results[1]["source_type"] == "code"
        assert results[2]["source_type"] == "thought"

        # Verify all notes created
        for result in results:
            assert Path(result["file_path"]).exists()

    @pytest.mark.asyncio
    async def test_process_batch_with_error_handling(self, vault_with_tags):
        """Test batch processing continues on error."""
        processor = InboxProcessor(str(vault_with_tags))

        items = [
            {"title": "Valid", "content": "https://example.com"},
            {"title": "Invalid", "content": ""},  # Empty content
            {"title": "Valid 2", "content": "Another thought"},
        ]

        results = await processor.process_batch(items)

        # Should process all items (even if some fail)
        assert len(results) == 3


class TestAccuracyRequirement:
    """Test that routing accuracy meets PRP requirement (>90%)."""

    @pytest.mark.asyncio
    async def test_routing_accuracy_exceeds_90_percent(self, vault_with_tags):
        """Test routing accuracy on diverse test cases exceeds 90%."""
        processor = InboxProcessor(str(vault_with_tags))

        test_cases = [
            # (title, content, expected_source, expected_folder)
            ("Python Docs", "https://docs.python.org", "url", "05 - Resources/05d - Documents"),
            ("Blog Post", "https://blog.example.com/post", "url", "05 - Resources/05c - Clippings"),
            ("React Docs", "https://reactjs.org/docs/hooks", "url", "05 - Resources/05d - Documents"),
            ("Code Example", "def hello(): pass", "code", "05 - Resources/05e - Examples"),
            ("JS Code", "const x = 1;", "code", "05 - Resources/05e - Examples"),
            ("Class Def", "class MyClass: pass", "code", "05 - Resources/05e - Examples"),
            ("Thought", "Research vector databases", "thought", "01 - Notes/01a - Atomic"),
            ("Idea", "Explore knowledge graphs", "thought", "01 - Notes/01a - Atomic"),
            ("MDN", "https://developer.mozilla.org/docs", "url", "05 - Resources/05d - Documents"),
            ("Tutorial", "Learn Python programming", "thought", "01 - Notes/01a - Atomic"),
            ("Azure Docs", "https://learn.microsoft.com/azure", "url", "05 - Resources/05d - Documents"),
            ("Import", "import pandas as pd", "code", "05 - Resources/05e - Examples"),
            ("News", "https://news.ycombinator.com/item", "url", "05 - Resources/05c - Clippings"),
            ("Function", "function test() {}", "code", "05 - Resources/05e - Examples"),
            ("Note", "Important meeting notes", "thought", "01 - Notes/01a - Atomic"),
        ]

        correct_count = 0
        total_count = len(test_cases)

        for title, content, expected_source, expected_folder in test_cases:
            result = await processor.process_item(title, content)

            if (result["source_type"] == expected_source and
                result["folder"] == expected_folder):
                correct_count += 1

        accuracy = (correct_count / total_count) * 100

        assert accuracy >= 90.0, (
            f"Routing accuracy {accuracy:.1f}% below 90% requirement "
            f"({correct_count}/{total_count} correct)"
        )


class TestProcessorUtilities:
    """Test processor utility methods."""

    @pytest.mark.asyncio
    async def test_get_processing_stats(self, vault_with_tags):
        """Test getting processing statistics."""
        processor = InboxProcessor(str(vault_with_tags))

        stats = processor.get_processing_stats()

        assert "vocabulary_size" in stats or "total_tags" in stats
        assert isinstance(stats, dict)

    @pytest.mark.asyncio
    async def test_refresh_vocabulary(self, vault_with_tags):
        """Test refreshing vocabulary after new notes."""
        processor = InboxProcessor(str(vault_with_tags))

        initial_size = len(processor.tag_analyzer.get_vocabulary())

        # Create new note with new tags
        await processor.vault_manager.create_note(
            title="New Topic",
            content="New content",
            folder="01 - Notes/01a - Atomic",
            note_type="note",
            tags=["new-tag-1", "new-tag-2"]
        )

        # Refresh vocabulary
        new_size = await processor.refresh_vocabulary()

        assert new_size > initial_size
        assert "new-tag-1" in processor.tag_analyzer.get_vocabulary()


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_process_empty_content(self, vault_with_tags):
        """Test processing item with empty content."""
        processor = InboxProcessor(str(vault_with_tags))

        result = await processor.process_item(
            title="Empty Note",
            content=""
        )

        # Should default to thought
        assert result["source_type"] == "thought"
        assert Path(result["file_path"]).exists()

    @pytest.mark.asyncio
    async def test_process_very_long_title(self, vault_with_tags):
        """Test processing with very long title."""
        processor = InboxProcessor(str(vault_with_tags))

        long_title = "A" * 200

        result = await processor.process_item(
            title=long_title,
            content="Some content"
        )

        # Should handle gracefully
        assert Path(result["file_path"]).exists()

    @pytest.mark.asyncio
    async def test_process_special_characters(self, vault_with_tags):
        """Test processing content with special characters."""
        processor = InboxProcessor(str(vault_with_tags))

        result = await processor.process_item(
            title="Special!@#$%",
            content="Content with émojis 🎉 and ünïcödé"
        )

        assert Path(result["file_path"]).exists()

    @pytest.mark.asyncio
    async def test_process_url_priority_over_code(self, vault_with_tags):
        """Test that URL detection has priority when content has both."""
        processor = InboxProcessor(str(vault_with_tags))

        result = await processor.process_item(
            title="API Documentation",
            content="""
Check this API: https://api.example.com

```python
API_URL = "https://api.example.com"
```
            """
        )

        # URL should have priority
        assert result["source_type"] == "url"

    @pytest.mark.asyncio
    async def test_sequential_processing_avoids_collisions(self, vault_with_tags):
        """Test that sequential processing avoids ID collisions."""
        processor = InboxProcessor(str(vault_with_tags))

        # Process multiple items rapidly
        results = []
        for i in range(5):
            result = await processor.process_item(
                title=f"Note {i}",
                content=f"Content {i}"
            )
            results.append(result)

        # All should have unique file paths
        file_paths = [r["file_path"] for r in results]
        assert len(file_paths) == len(set(file_paths))
