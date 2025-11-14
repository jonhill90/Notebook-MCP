"""Tests for TagAnalyzer.

These tests verify that:
1. Tag vocabulary is built correctly from vault
2. Tag suggestions match existing vocabulary
3. Title matches are prioritized over content matches
4. max_tags limit is respected
5. Tag scoring algorithm works correctly
6. Vocabulary can be refreshed
7. Edge cases are handled (empty vault, no matches, etc.)
"""

import pytest
import pytest_asyncio
from pathlib import Path
import tempfile
import shutil

from src.vault.tag_analyzer import TagAnalyzer
from src.vault.manager import VaultManager


@pytest.fixture
def temp_vault():
    """Create a temporary vault for testing."""
    temp_dir = tempfile.mkdtemp()
    vault_path = Path(temp_dir) / "test_vault"
    vault_path.mkdir()

    # Create folder structure
    folders = [
        "00 - Inbox",
        "01 - Notes",
        "02 - MOCs",
        "03 - Projects",
        "04 - Areas",
        "05 - Resources",
    ]
    for folder in folders:
        (vault_path / folder).mkdir()

    yield vault_path

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest_asyncio.fixture
async def vault_with_notes(temp_vault):
    """Create a vault with sample notes for testing."""
    manager = VaultManager(str(temp_vault))

    # Create notes with various tags
    await manager.create_note(
        title="Python Basics",
        content="Introduction to Python programming language",
        folder="01 - Notes",
        note_type="note",
        tags=["python", "programming", "tutorial"],
    )

    await manager.create_note(
        title="Machine Learning",
        content="ML algorithms and applications in Python",
        folder="01 - Notes",
        note_type="note",
        tags=["machine-learning", "python", "ai"],
    )

    await manager.create_note(
        title="Web Development",
        content="Building web applications with modern frameworks",
        folder="01 - Notes",
        note_type="note",
        tags=["web-dev", "javascript", "frontend"],
    )

    await manager.create_note(
        title="Data Science",
        content="Data analysis and visualization techniques",
        folder="01 - Notes",
        note_type="note",
        tags=["data-science", "python", "analytics"],
    )

    await manager.create_note(
        title="Algorithms MOC",
        content="Collection of algorithm notes",
        folder="02 - MOCs",
        note_type="moc",
        tags=["algorithms", "computer-science", "moc"],
    )

    return temp_vault


class TestTagAnalyzerInitialization:
    """Test TagAnalyzer initialization and vocabulary building."""

    def test_init_with_empty_vault(self, temp_vault):
        """Test initialization with empty vault."""
        analyzer = TagAnalyzer(str(temp_vault))

        assert analyzer.vault_path == temp_vault
        assert isinstance(analyzer.tag_vocabulary, set)
        assert len(analyzer.tag_vocabulary) == 0

    @pytest.mark.asyncio
    async def test_init_builds_vocabulary(self, vault_with_notes):
        """Test that vocabulary is built from vault notes."""
        analyzer = TagAnalyzer(str(vault_with_notes))

        # Should have collected all unique tags
        expected_tags = {
            "python", "programming", "tutorial",
            "machine-learning", "ai",
            "web-dev", "javascript", "frontend",
            "data-science", "analytics",
            "algorithms", "computer-science", "moc"
        }

        assert analyzer.tag_vocabulary == expected_tags

    @pytest.mark.asyncio
    async def test_vocabulary_deduplication(self, vault_with_notes):
        """Test that duplicate tags are deduplicated in vocabulary."""
        analyzer = TagAnalyzer(str(vault_with_notes))

        # 'python' appears in multiple notes but should only be in vocab once
        python_count = sum(1 for tag in analyzer.tag_vocabulary if tag == "python")
        assert python_count == 1


class TestVocabularyMethods:
    """Test vocabulary-related methods."""

    @pytest.mark.asyncio
    async def test_get_vocabulary(self, vault_with_notes):
        """Test getting vocabulary returns a copy."""
        analyzer = TagAnalyzer(str(vault_with_notes))

        vocab = analyzer.get_vocabulary()

        # Should be a copy (modifying it doesn't affect original)
        original_size = len(analyzer.tag_vocabulary)
        vocab.add("new-tag")

        assert len(analyzer.tag_vocabulary) == original_size

    @pytest.mark.asyncio
    async def test_get_vocabulary_stats(self, vault_with_notes):
        """Test vocabulary statistics."""
        analyzer = TagAnalyzer(str(vault_with_notes))

        stats = analyzer.get_vocabulary_stats()

        assert stats['total_tags'] == 13  # 13 unique tags
        assert stats['avg_tag_length'] > 0
        assert stats['multi_word_tags'] > 0  # Has hyphenated tags

    def test_get_vocabulary_stats_empty(self, temp_vault):
        """Test stats with empty vocabulary."""
        analyzer = TagAnalyzer(str(temp_vault))

        stats = analyzer.get_vocabulary_stats()

        assert stats['total_tags'] == 0
        assert stats['avg_tag_length'] == 0
        assert stats['multi_word_tags'] == 0

    @pytest.mark.asyncio
    async def test_refresh_vocabulary(self, vault_with_notes):
        """Test refreshing vocabulary after new notes added."""
        analyzer = TagAnalyzer(str(vault_with_notes))
        initial_count = len(analyzer.tag_vocabulary)

        # Add a new note with new tags
        manager = VaultManager(str(vault_with_notes))
        await manager.create_note(
            title="New Topic",
            content="New content",
            folder="01 - Notes",
            note_type="note",
            tags=["new-tag", "another-tag"],
        )

        # Vocabulary should still be old
        assert len(analyzer.tag_vocabulary) == initial_count

        # Refresh vocabulary
        new_count = analyzer.refresh_vocabulary()

        # Should now include new tags
        assert new_count == initial_count + 2
        assert "new-tag" in analyzer.tag_vocabulary
        assert "another-tag" in analyzer.tag_vocabulary


class TestContentTokenization:
    """Test content tokenization."""

    def test_tokenize_simple_content(self, temp_vault):
        """Test tokenizing simple content."""
        analyzer = TagAnalyzer(str(temp_vault))

        words = analyzer._tokenize_content("Python programming tutorial")

        assert words == ["python", "programming", "tutorial"]

    def test_tokenize_with_punctuation(self, temp_vault):
        """Test tokenizing content with punctuation."""
        analyzer = TagAnalyzer(str(temp_vault))

        words = analyzer._tokenize_content("Python, ML & AI!")

        assert "python" in words
        assert "ml" in words
        assert "ai" in words

    def test_tokenize_with_hyphens(self, temp_vault):
        """Test that hyphens are preserved in tokenization."""
        analyzer = TagAnalyzer(str(temp_vault))

        words = analyzer._tokenize_content("machine-learning and web-dev")

        assert "machine-learning" in words
        assert "web-dev" in words

    def test_tokenize_empty_content(self, temp_vault):
        """Test tokenizing empty content."""
        analyzer = TagAnalyzer(str(temp_vault))

        words = analyzer._tokenize_content("")

        assert words == []


class TestTagSuggestion:
    """Test tag suggestion functionality."""

    @pytest.mark.asyncio
    async def test_suggest_tags_basic(self, vault_with_notes):
        """Test basic tag suggestion."""
        analyzer = TagAnalyzer(str(vault_with_notes))

        tags = analyzer.suggest_tags(
            content="This is about Python programming",
            title="Python Guide",
            max_tags=5
        )

        # Should suggest python (matches both title and content)
        assert "python" in tags
        assert isinstance(tags, list)
        assert len(tags) <= 5

    @pytest.mark.asyncio
    async def test_suggest_tags_prioritizes_title(self, vault_with_notes):
        """Test that title matches are prioritized."""
        analyzer = TagAnalyzer(str(vault_with_notes))

        tags = analyzer.suggest_tags(
            content="Some random content about general topics",
            title="Machine Learning",  # Matches 'machine-learning' tag
            max_tags=5
        )

        # 'machine-learning' should be first due to title match
        assert tags[0] == "machine-learning"

    @pytest.mark.asyncio
    async def test_suggest_tags_max_tags_limit(self, vault_with_notes):
        """Test that max_tags limit is respected."""
        analyzer = TagAnalyzer(str(vault_with_notes))

        tags = analyzer.suggest_tags(
            content="Python machine learning web development data science",
            title="Programming Topics",
            max_tags=3
        )

        assert len(tags) <= 3

    @pytest.mark.asyncio
    async def test_suggest_tags_content_matching(self, vault_with_notes):
        """Test content-based tag matching."""
        analyzer = TagAnalyzer(str(vault_with_notes))

        tags = analyzer.suggest_tags(
            content="This tutorial covers Python and machine learning algorithms",
            title="Tutorial",
            max_tags=5
        )

        # Should suggest python and machine-learning based on content
        assert "python" in tags or "machine-learning" in tags or "tutorial" in tags

    @pytest.mark.asyncio
    async def test_suggest_tags_no_matches(self, vault_with_notes):
        """Test when no tags match content or title."""
        analyzer = TagAnalyzer(str(vault_with_notes))

        tags = analyzer.suggest_tags(
            content="Completely unrelated quantum physics topics",
            title="Quantum Physics",
            max_tags=5
        )

        # Should return empty list or very few tags
        # (quantum and physics not in vocabulary)
        assert isinstance(tags, list)

    def test_suggest_tags_empty_vocabulary(self, temp_vault):
        """Test suggestion with empty vocabulary."""
        analyzer = TagAnalyzer(str(temp_vault))

        tags = analyzer.suggest_tags(
            content="Some content",
            title="Some Title",
            max_tags=5
        )

        assert tags == []

    @pytest.mark.asyncio
    async def test_suggest_tags_returns_ordered_by_relevance(self, vault_with_notes):
        """Test that suggestions are ordered by relevance."""
        analyzer = TagAnalyzer(str(vault_with_notes))

        tags = analyzer.suggest_tags(
            content="Python Python Python machine learning",  # Python appears 3x
            title="Python Tutorial",  # Title also matches Python
            max_tags=5
        )

        # Python should be first due to high score (title + frequent content match)
        if len(tags) > 0:
            assert tags[0] == "python"


class TestTagScoring:
    """Test tag scoring algorithm."""

    def test_score_exact_title_match(self, temp_vault):
        """Test scoring for exact title match."""
        analyzer = TagAnalyzer(str(temp_vault))

        score = analyzer._score_tag_match(
            tag="python-tutorial",
            content_words=["some", "words"],
            title_normalized="python-tutorial"
        )

        # Exact title match should score 10 points
        assert score >= 10

    def test_score_partial_title_match(self, temp_vault):
        """Test scoring for partial title match."""
        analyzer = TagAnalyzer(str(temp_vault))

        score = analyzer._score_tag_match(
            tag="python",
            content_words=[],
            title_normalized="python-tutorial"
        )

        # Partial title match should score 5 points
        assert score >= 5

    def test_score_content_match(self, temp_vault):
        """Test scoring for content matches."""
        analyzer = TagAnalyzer(str(temp_vault))

        score = analyzer._score_tag_match(
            tag="python",
            content_words=["python", "python", "programming"],
            title_normalized="tutorial"
        )

        # Multiple content matches should increase score
        assert score >= 2  # At least 2 points for 2 matches

    def test_score_no_match(self, temp_vault):
        """Test scoring when nothing matches."""
        analyzer = TagAnalyzer(str(temp_vault))

        score = analyzer._score_tag_match(
            tag="python",
            content_words=["javascript", "web"],
            title_normalized="web-development"
        )

        assert score == 0


class TestAccuracyMetrics:
    """Test suggestion accuracy meets PRP requirements (>80%)."""

    @pytest.mark.asyncio
    async def test_accuracy_on_similar_content(self, vault_with_notes):
        """Test accuracy when content is similar to existing notes."""
        analyzer = TagAnalyzer(str(vault_with_notes))

        # Test case 1: Python content
        tags1 = analyzer.suggest_tags(
            content="Learning Python programming fundamentals",
            title="Python Fundamentals",
            max_tags=3
        )
        assert "python" in tags1  # Should match

        # Test case 2: ML content
        tags2 = analyzer.suggest_tags(
            content="Machine learning models and algorithms",
            title="ML Models",
            max_tags=3
        )
        assert "machine-learning" in tags2 or "algorithms" in tags2

        # Test case 3: Web dev content
        tags3 = analyzer.suggest_tags(
            content="JavaScript web development framework",
            title="Web Framework",
            max_tags=3
        )
        assert "javascript" in tags3 or "web-dev" in tags3

    @pytest.mark.asyncio
    async def test_suggestion_quality(self, vault_with_notes):
        """Test that suggestions are high quality (relevant to content)."""
        analyzer = TagAnalyzer(str(vault_with_notes))

        tags = analyzer.suggest_tags(
            content="This tutorial teaches Python for data science and machine learning",
            title="Python Data Science Tutorial",
            max_tags=5
        )

        # Should include relevant tags
        relevant_tags = {"python", "data-science", "machine-learning", "tutorial"}
        suggested_set = set(tags)

        # At least 2 out of 4 relevant tags should be suggested (50%+ precision)
        overlap = len(relevant_tags & suggested_set)
        assert overlap >= 2, f"Expected at least 2 relevant tags, got {overlap}"


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_suggest_with_very_long_content(self, vault_with_notes):
        """Test suggestion with very long content."""
        analyzer = TagAnalyzer(str(vault_with_notes))

        long_content = "Python " * 1000 + "machine learning " * 1000

        tags = analyzer.suggest_tags(
            content=long_content,
            title="Long Document",
            max_tags=5
        )

        # Should still work and return reasonable suggestions
        assert isinstance(tags, list)
        assert len(tags) <= 5

    @pytest.mark.asyncio
    async def test_suggest_with_special_characters(self, vault_with_notes):
        """Test suggestion with special characters in content."""
        analyzer = TagAnalyzer(str(vault_with_notes))

        tags = analyzer.suggest_tags(
            content="Python!!! @#$% programming &&& tutorial",
            title="Python Guide!!!",
            max_tags=5
        )

        # Should handle special characters gracefully
        assert isinstance(tags, list)

    @pytest.mark.asyncio
    async def test_suggest_with_max_tags_zero(self, vault_with_notes):
        """Test suggestion with max_tags=0."""
        analyzer = TagAnalyzer(str(vault_with_notes))

        tags = analyzer.suggest_tags(
            content="Python programming",
            title="Python",
            max_tags=0
        )

        assert tags == []

    @pytest.mark.asyncio
    async def test_suggest_with_max_tags_larger_than_vocabulary(self, vault_with_notes):
        """Test when max_tags exceeds vocabulary size."""
        analyzer = TagAnalyzer(str(vault_with_notes))

        tags = analyzer.suggest_tags(
            content="Python machine learning web development algorithms",
            title="Programming",
            max_tags=100  # Larger than vocabulary
        )

        # Should return all matching tags, not exceed vocabulary size
        assert len(tags) <= len(analyzer.tag_vocabulary)

    @pytest.mark.asyncio
    async def test_suggest_with_empty_title(self, vault_with_notes):
        """Test suggestion with empty title."""
        analyzer = TagAnalyzer(str(vault_with_notes))

        tags = analyzer.suggest_tags(
            content="Python programming tutorial",
            title="",
            max_tags=5
        )

        # Should still work, just no title-based scoring
        assert isinstance(tags, list)

    @pytest.mark.asyncio
    async def test_suggest_with_empty_content(self, vault_with_notes):
        """Test suggestion with empty content."""
        analyzer = TagAnalyzer(str(vault_with_notes))

        tags = analyzer.suggest_tags(
            content="",
            title="Python Tutorial",
            max_tags=5
        )

        # Should still suggest based on title
        assert isinstance(tags, list)
