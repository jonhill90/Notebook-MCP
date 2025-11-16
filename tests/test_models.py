"""Comprehensive tests for Pydantic models.

Tests validate that NoteFrontmatter and TagCluster models enforce
Second Brain conventions correctly.
"""

import pytest
from pydantic import ValidationError
from src.models import NoteFrontmatter, TagCluster


class TestNoteFrontmatter:
    """Test suite for NoteFrontmatter model validation."""

    def test_valid_frontmatter_creation(self):
        """Test creating valid frontmatter with all correct fields."""
        frontmatter = NoteFrontmatter(
            id="20251114020000",
            type="Note",
            tags=["python", "testing", "pydantic"],
            created="2025-11-14",
            updated="2025-11-14",
            permalink="01-notes/01r-research/20251114020000"
        )

        assert frontmatter.id == "20251114020000"
        assert frontmatter.type == "Note"
        assert frontmatter.tags == ["python", "testing", "pydantic"]
        assert frontmatter.created == "2025-11-14"
        assert frontmatter.updated == "2025-11-14"
        assert frontmatter.permalink == "01-notes/01r-research/20251114020000"

    def test_all_valid_note_types(self):
        """Test all valid note types (display names) are accepted."""
        valid_types = ["Note", "Map of Content", "Project", "Area", "Research", "Meeting"]

        for note_type in valid_types:
            frontmatter = NoteFrontmatter(
                id="20251114020000",
                type=note_type,
                tags=["test"],
                created="2025-11-14",
                updated="2025-11-14",
                permalink="01-notes/01r-research/20251114020000"
            )
            assert frontmatter.type == note_type

    def test_invalid_id_too_short(self):
        """Test that IDs shorter than 14 digits are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            NoteFrontmatter(
                id="2025111402",  # Only 10 digits
                type="Note",
                tags=["test"],
                created="2025-11-14",
                updated="2025-11-14",
                permalink="test"
            )

        assert "id" in str(exc_info.value)

    def test_invalid_id_too_long(self):
        """Test that IDs longer than 14 digits are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            NoteFrontmatter(
                id="202511140200000",  # 15 digits
                type="Note",
                tags=["test"],
                created="2025-11-14",
                updated="2025-11-14",
                permalink="test"
            )

        assert "id" in str(exc_info.value)

    def test_invalid_id_contains_letters(self):
        """Test that IDs with non-digit characters are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            NoteFrontmatter(
                id="2025111402000A",  # Contains letter
                type="Note",
                tags=["test"],
                created="2025-11-14",
                updated="2025-11-14",
                permalink="test"
            )

        assert "id" in str(exc_info.value)

    def test_tag_with_uppercase_rejected(self):
        """Test that tags with uppercase letters are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            NoteFrontmatter(
                id="20251114020000",
                type="Note",
                tags=["Python"],  # Uppercase
                created="2025-11-14",
                updated="2025-11-14",
                permalink="test"
            )

        assert "lowercase-hyphenated" in str(exc_info.value)

    def test_tag_with_spaces_rejected(self):
        """Test that tags with spaces are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            NoteFrontmatter(
                id="20251114020000",
                type="Note",
                tags=["python testing"],  # Space
                created="2025-11-14",
                updated="2025-11-14",
                permalink="test"
            )

        assert "lowercase-hyphenated" in str(exc_info.value)

    def test_tag_with_underscore_rejected(self):
        """Test that tags with underscores are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            NoteFrontmatter(
                id="20251114020000",
                type="Note",
                tags=["python_testing"],  # Underscore
                created="2025-11-14",
                updated="2025-11-14",
                permalink="test"
            )

        assert "lowercase-hyphenated" in str(exc_info.value)

    def test_tag_with_special_chars_rejected(self):
        """Test that tags with special characters are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            NoteFrontmatter(
                id="20251114020000",
                type="Note",
                tags=["python@testing"],  # Special char
                created="2025-11-14",
                updated="2025-11-14",
                permalink="test"
            )

        assert "lowercase-hyphenated" in str(exc_info.value)

    def test_valid_tags_with_numbers_and_hyphens(self):
        """Test that tags with lowercase, numbers, and hyphens are accepted."""
        frontmatter = NoteFrontmatter(
            id="20251114020000",
            type="Note",
            tags=["python3", "test-123", "web-dev"],
            created="2025-11-14",
            updated="2025-11-14",
            permalink="test"
        )

        assert frontmatter.tags == ["python3", "test-123", "web-dev"]

    def test_multiple_invalid_tags_all_reported(self):
        """Test that multiple invalid tags are all caught."""
        with pytest.raises(ValidationError) as exc_info:
            NoteFrontmatter(
                id="20251114020000",
                type="Note",
                tags=["Valid-tag", "INVALID", "also_invalid"],
                created="2025-11-14",
                updated="2025-11-14",
                permalink="test"
            )

        error_msg = str(exc_info.value)
        # Should catch first invalid tag
        assert "lowercase-hyphenated" in error_msg

    def test_permalink_with_uppercase_rejected(self):
        """Test that permalinks with uppercase letters are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            NoteFrontmatter(
                id="20251114020000",
                type="Note",
                tags=["test"],
                created="2025-11-14",
                updated="2025-11-14",
                permalink="Test-Note"  # Uppercase
            )

        assert "lowercase-hyphenated" in str(exc_info.value)

    def test_permalink_with_spaces_rejected(self):
        """Test that permalinks with spaces are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            NoteFrontmatter(
                id="20251114020000",
                type="Note",
                tags=["test"],
                created="2025-11-14",
                updated="2025-11-14",
                permalink="test note"  # Space
            )

        assert "lowercase-hyphenated" in str(exc_info.value)

    def test_permalink_with_underscore_rejected(self):
        """Test that permalinks with underscores are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            NoteFrontmatter(
                id="20251114020000",
                type="Note",
                tags=["test"],
                created="2025-11-14",
                updated="2025-11-14",
                permalink="test_note"  # Underscore
            )

        assert "lowercase-hyphenated" in str(exc_info.value)

    def test_valid_permalink_with_numbers_and_hyphens(self):
        """Test that permalinks with lowercase, numbers, and hyphens are accepted."""
        frontmatter = NoteFrontmatter(
            id="20251114020000",
            type="Note",
            tags=["test"],
            created="2025-11-14",
            updated="2025-11-14",
            permalink="my-note-123"
        )

        assert frontmatter.permalink == "my-note-123"

    def test_empty_tags_list_allowed(self):
        """Test that empty tags list is allowed (though not recommended)."""
        frontmatter = NoteFrontmatter(
            id="20251114020000",
            type="Note",
            tags=[],
            created="2025-11-14",
            updated="2025-11-14",
            permalink="test"
        )

        assert frontmatter.tags == []

    def test_model_serialization(self):
        """Test that model can be serialized to dict."""
        frontmatter = NoteFrontmatter(
            id="20251114020000",
            type="Note",
            tags=["python"],
            created="2025-11-14",
            updated="2025-11-14",
            permalink="01-notes/01r-research/20251114020000"
        )

        data = frontmatter.model_dump()

        assert data == {
            "id": "20251114020000",
            "type": "Note",
            "tags": ["python"],
            "created": "2025-11-14",
            "updated": "2025-11-14",
            "permalink": "01-notes/01r-research/20251114020000"
        }


class TestTagCluster:
    """Test suite for TagCluster model."""

    def test_valid_cluster_creation(self):
        """Test creating valid tag cluster."""
        cluster = TagCluster(
            tag="python",
            note_count=15,
            notes=["20251114020000", "20251114020100", "20251114020200"]
        )

        assert cluster.tag == "python"
        assert cluster.note_count == 15
        assert len(cluster.notes) == 3
        assert cluster.should_create_moc is False

    def test_cluster_with_moc_flag_set(self):
        """Test creating cluster with MOC flag explicitly set."""
        cluster = TagCluster(
            tag="python",
            note_count=15,
            notes=["20251114020000"],
            should_create_moc=True
        )

        assert cluster.should_create_moc is True

    def test_check_threshold_default(self):
        """Test check_threshold with default threshold (12)."""
        cluster = TagCluster(
            tag="python",
            note_count=15,
            notes=["20251114020000"] * 15
        )

        result = cluster.check_threshold()

        assert result is True
        assert cluster.should_create_moc is True

    def test_check_threshold_below_default(self):
        """Test check_threshold when below default threshold."""
        cluster = TagCluster(
            tag="python",
            note_count=10,
            notes=["20251114020000"] * 10
        )

        result = cluster.check_threshold()

        assert result is False
        assert cluster.should_create_moc is False

    def test_check_threshold_exactly_at_default(self):
        """Test check_threshold when exactly at threshold."""
        cluster = TagCluster(
            tag="python",
            note_count=12,
            notes=["20251114020000"] * 12
        )

        result = cluster.check_threshold()

        assert result is True
        assert cluster.should_create_moc is True

    def test_check_threshold_custom_threshold(self):
        """Test check_threshold with custom threshold."""
        cluster = TagCluster(
            tag="python",
            note_count=15,
            notes=["20251114020000"] * 15
        )

        # Below custom threshold
        result = cluster.check_threshold(threshold=20)
        assert result is False
        assert cluster.should_create_moc is False

        # At custom threshold
        result = cluster.check_threshold(threshold=15)
        assert result is True
        assert cluster.should_create_moc is True

        # Above custom threshold
        result = cluster.check_threshold(threshold=10)
        assert result is True
        assert cluster.should_create_moc is True

    def test_check_threshold_updates_flag(self):
        """Test that check_threshold updates should_create_moc flag."""
        cluster = TagCluster(
            tag="python",
            note_count=15,
            notes=["20251114020000"] * 15,
            should_create_moc=False
        )

        assert cluster.should_create_moc is False

        cluster.check_threshold(threshold=10)

        assert cluster.should_create_moc is True

    def test_zero_note_count(self):
        """Test cluster with zero notes."""
        cluster = TagCluster(
            tag="unused-tag",
            note_count=0,
            notes=[]
        )

        assert cluster.note_count == 0
        result = cluster.check_threshold()
        assert result is False

    def test_negative_note_count_rejected(self):
        """Test that negative note counts are rejected."""
        with pytest.raises(ValidationError):
            TagCluster(
                tag="python",
                note_count=-5,
                notes=[]
            )

    def test_cluster_serialization(self):
        """Test that cluster can be serialized to dict."""
        cluster = TagCluster(
            tag="python",
            note_count=15,
            notes=["20251114020000", "20251114020100"]
        )

        data = cluster.model_dump()

        assert data == {
            "tag": "python",
            "note_count": 15,
            "notes": ["20251114020000", "20251114020100"],
            "should_create_moc": False
        }

    def test_large_cluster(self):
        """Test cluster with large number of notes."""
        note_ids = [f"2025111402{i:04d}" for i in range(100)]
        cluster = TagCluster(
            tag="python",
            note_count=100,
            notes=note_ids
        )

        assert cluster.note_count == 100
        assert len(cluster.notes) == 100
        assert cluster.check_threshold(threshold=50) is True

    def test_cluster_tag_naming(self):
        """Test various tag naming patterns in clusters."""
        # Lowercase with hyphens
        cluster1 = TagCluster(tag="machine-learning", note_count=10, notes=[])
        assert cluster1.tag == "machine-learning"

        # Lowercase with numbers
        cluster2 = TagCluster(tag="python3", note_count=10, notes=[])
        assert cluster2.tag == "python3"

        # Single word
        cluster3 = TagCluster(tag="ai", note_count=10, notes=[])
        assert cluster3.tag == "ai"


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_complete_note_creation_flow(self):
        """Test creating note with validated frontmatter."""
        # Simulate creating a note with full frontmatter
        frontmatter = NoteFrontmatter(
            id="20251114020000",
            type="Note",
            tags=["python", "testing", "pydantic"],
            created="2025-11-14",
            updated="2025-11-14",
            permalink="pydantic-models-implementation"
        )

        # Verify all fields are correct
        assert frontmatter.id == "20251114020000"
        assert "python" in frontmatter.tags
        assert frontmatter.permalink == "pydantic-models-implementation"

        # Simulate serializing for file writing
        data = frontmatter.model_dump()
        assert isinstance(data, dict)
        assert "id" in data

    def test_moc_generation_flow(self):
        """Test MOC generation decision flow."""
        # Create clusters from tag analysis
        clusters = [
            TagCluster(tag="python", note_count=15, notes=[f"2025111402{i:04d}" for i in range(15)]),
            TagCluster(tag="javascript", note_count=8, notes=[f"2025111403{i:04d}" for i in range(8)]),
            TagCluster(tag="rust", note_count=20, notes=[f"2025111404{i:04d}" for i in range(20)]),
        ]

        # Check which clusters need MOCs
        moc_needed = []
        for cluster in clusters:
            if cluster.check_threshold(threshold=12):
                moc_needed.append(cluster.tag)

        assert "python" in moc_needed  # 15 notes
        assert "javascript" not in moc_needed  # Only 8 notes
        assert "rust" in moc_needed  # 20 notes

    def test_validation_prevents_bad_data(self):
        """Test that validation prevents creation of invalid frontmatter."""
        # Attempt to create note with bad conventions
        # Note: type field accepts any string (display names are free-form)
        invalid_inputs = [
            {"id": "123", "reason": "ID too short"},
            {"tags": ["Bad Tag"], "reason": "Tag with space"},
            {"tags": ["Bad_Tag"], "reason": "Tag with underscore"},
            {"permalink": "Bad Permalink", "reason": "Permalink with space"},
        ]

        base_data = {
            "id": "20251114020000",
            "type": "Note",
            "tags": ["test"],
            "created": "2025-11-14",
            "updated": "2025-11-14",
            "permalink": "01-notes/01r-research/20251114020000"
        }

        for invalid_input in invalid_inputs:
            invalid_input.pop("reason")  # Remove reason, just used for documentation
            test_data = {**base_data, **invalid_input}

            with pytest.raises(ValidationError, match=r".*"):
                NoteFrontmatter(**test_data)
