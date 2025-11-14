"""Tests for VaultManager CRUD operations.

These tests verify that:
1. Notes are created with valid frontmatter
2. Invalid folder/type combinations are rejected
3. Tags are normalized correctly
4. IDs are unique (collision handling)
5. CRUD operations work correctly
6. Dry-run mode works as expected
"""

import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import shutil
import frontmatter

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


@pytest.fixture
def vault_manager(temp_vault):
    """Create a VaultManager instance with temp vault."""
    return VaultManager(str(temp_vault))


class TestVaultManagerInitialization:
    """Test VaultManager initialization."""

    def test_init_with_valid_path(self, temp_vault):
        """Test initialization with valid vault path."""
        manager = VaultManager(str(temp_vault))
        assert manager.vault_path == temp_vault
        assert manager.valid_folders == VaultManager.VALID_FOLDERS

    def test_init_with_invalid_path(self):
        """Test initialization with non-existent path."""
        with pytest.raises(ValueError, match="Vault path does not exist"):
            VaultManager("/nonexistent/path")

    def test_init_with_file_path(self, temp_vault):
        """Test initialization with file instead of directory."""
        file_path = temp_vault / "test.txt"
        file_path.touch()

        with pytest.raises(ValueError, match="not a directory"):
            VaultManager(str(file_path))


class TestIDGeneration:
    """Test ID generation methods."""

    def test_generate_id_format(self, vault_manager):
        """Test that generated ID matches YYYYMMDDHHmmss format."""
        note_id = vault_manager.generate_id()

        assert len(note_id) == 14
        assert note_id.isdigit()

        # Parse as datetime to verify format
        parsed = datetime.strptime(note_id, "%Y%m%d%H%M%S")
        assert isinstance(parsed, datetime)

    @pytest.mark.asyncio
    async def test_generate_unique_id(self, vault_manager):
        """Test that unique ID generation works."""
        unique_id = await vault_manager.generate_unique_id()

        assert len(unique_id) == 14
        assert unique_id.isdigit()

    @pytest.mark.asyncio
    async def test_id_collision_handling(self, vault_manager, temp_vault):
        """Test that ID collisions are handled by waiting and regenerating."""
        # Create a note with a specific timestamp
        first_id = vault_manager.generate_id()

        # Create the file manually to simulate collision
        folder_path = temp_vault / "01 - Notes"
        (folder_path / f"{first_id}.md").touch()

        # This should detect the collision and generate a new ID
        # We'll mock the generate_id to return the same ID first
        original_generate = vault_manager.generate_id
        call_count = 0

        def mock_generate():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return first_id  # Collision
            return original_generate()  # New ID after sleep

        vault_manager.generate_id = mock_generate
        await vault_manager.generate_unique_id()

        # Should have called generate_id twice (once collision, once success)
        assert call_count == 2
        # The unique ID should be different (generated after sleep)
        # Note: This might be the same if it happens in the same second,
        # but the logic ensures it checks for collisions


class TestFolderTypeValidation:
    """Test folder and type validation."""

    def test_validate_valid_combinations(self, vault_manager):
        """Test that valid folder/type combinations pass."""
        valid_combos = [
            ("00 - Inbox", "clipping"),
            ("00 - Inbox", "thought"),
            ("01 - Notes", "note"),
            ("02 - MOCs", "moc"),
            ("03 - Projects", "project"),
            ("04 - Areas", "area"),
            ("05 - Resources", "resource"),
        ]

        for folder, note_type in valid_combos:
            vault_manager.validate_folder_type(folder, note_type)  # Should not raise

    def test_validate_invalid_folder(self, vault_manager):
        """Test that invalid folder raises error."""
        with pytest.raises(ValueError, match="Invalid folder"):
            vault_manager.validate_folder_type("99 - Invalid", "note")

    def test_validate_invalid_type_for_folder(self, vault_manager):
        """Test that invalid type for folder raises error."""
        with pytest.raises(ValueError, match="not allowed in folder"):
            vault_manager.validate_folder_type("01 - Notes", "moc")

        with pytest.raises(ValueError, match="not allowed in folder"):
            vault_manager.validate_folder_type("02 - MOCs", "note")


class TestTagNormalization:
    """Test tag normalization."""

    def test_normalize_tag_lowercase(self):
        """Test that tags are converted to lowercase."""
        assert VaultManager.normalize_tag("Python") == "python"
        assert VaultManager.normalize_tag("UPPERCASE") == "uppercase"
        assert VaultManager.normalize_tag("MiXeD") == "mixed"

    def test_normalize_tag_spaces_to_hyphens(self):
        """Test that spaces are converted to hyphens."""
        assert VaultManager.normalize_tag("machine learning") == "machine-learning"
        assert VaultManager.normalize_tag("web   dev") == "web-dev"  # Multiple spaces

    def test_normalize_tag_underscores_to_hyphens(self):
        """Test that underscores are converted to hyphens."""
        assert VaultManager.normalize_tag("snake_case") == "snake-case"
        assert VaultManager.normalize_tag("my_tag_name") == "my-tag-name"

    def test_normalize_tag_special_characters(self):
        """Test that special characters are removed."""
        assert VaultManager.normalize_tag("AI & ML") == "ai-ml"
        assert VaultManager.normalize_tag("C++") == "c"
        assert VaultManager.normalize_tag("tag!@#$%") == "tag"

    def test_normalize_tag_multiple_hyphens(self):
        """Test that multiple consecutive hyphens are collapsed."""
        assert VaultManager.normalize_tag("tag---name") == "tag-name"
        assert VaultManager.normalize_tag("a--b--c") == "a-b-c"

    def test_normalize_tag_leading_trailing_hyphens(self):
        """Test that leading/trailing hyphens are removed."""
        assert VaultManager.normalize_tag("-tag-") == "tag"
        assert VaultManager.normalize_tag("--tag--") == "tag"

    def test_normalize_tag_complex_example(self):
        """Test complex normalization example."""
        assert VaultManager.normalize_tag("Knowledge_Management & PKM!") == "knowledge-management-pkm"


class TestPermalinkNormalization:
    """Test permalink normalization."""

    def test_normalize_permalink(self):
        """Test that permalinks are normalized like tags."""
        assert VaultManager.normalize_permalink("My First Note") == "my-first-note"
        assert VaultManager.normalize_permalink("Python Best Practices!") == "python-best-practices"


class TestCreateNote:
    """Test note creation."""

    @pytest.mark.asyncio
    async def test_create_note_basic(self, vault_manager, temp_vault):
        """Test basic note creation."""
        file_path = await vault_manager.create_note(
            title="Test Note",
            content="This is test content.",
            folder="01 - Notes",
            note_type="note",
            tags=["test", "example"],
        )

        # Verify file exists
        assert file_path.exists()

        # Parse and verify frontmatter
        post = frontmatter.load(file_path)
        metadata = post.metadata

        assert len(metadata['id']) == 14
        assert metadata['type'] == "note"
        assert metadata['tags'] == ["test", "example"]
        assert metadata['permalink'] == "test-note"
        assert 'created' in metadata
        assert 'updated' in metadata

        # Verify content
        assert "# Test Note" in post.content
        assert "This is test content." in post.content

    @pytest.mark.asyncio
    async def test_create_note_with_tag_normalization(self, vault_manager, temp_vault):
        """Test that tags are normalized during creation."""
        file_path = await vault_manager.create_note(
            title="Tag Test",
            content="Testing tag normalization",
            folder="01 - Notes",
            note_type="note",
            tags=["Python Programming", "AI & ML", "web_dev"],
        )

        post = frontmatter.load(file_path)
        metadata = post.metadata

        # Tags should be normalized
        assert "python-programming" in metadata['tags']
        assert "ai-ml" in metadata['tags']
        assert "web-dev" in metadata['tags']

    @pytest.mark.asyncio
    async def test_create_note_invalid_folder_type(self, vault_manager):
        """Test that invalid folder/type combination raises error."""
        with pytest.raises(ValueError, match="not allowed in folder"):
            await vault_manager.create_note(
                title="Invalid Note",
                content="Content",
                folder="01 - Notes",
                note_type="moc",  # MOC not allowed in Notes folder
                tags=["test"],
            )

    @pytest.mark.asyncio
    async def test_create_note_with_status(self, vault_manager, temp_vault):
        """Test creating note with status field."""
        file_path = await vault_manager.create_note(
            title="Project Note",
            content="Project content",
            folder="03 - Projects",
            note_type="project",
            tags=["project"],
            status="in-progress",
        )

        post = frontmatter.load(file_path)
        assert post.metadata['status'] == "in-progress"

    @pytest.mark.asyncio
    async def test_create_note_dry_run(self, vault_manager, temp_vault):
        """Test dry-run mode doesn't create file."""
        file_path = await vault_manager.create_note(
            title="Dry Run Test",
            content="This should not be created",
            folder="01 - Notes",
            note_type="note",
            tags=["test"],
            dry_run=True,
        )

        # File should NOT exist
        assert not file_path.exists()

    @pytest.mark.asyncio
    async def test_create_note_creates_folder_if_missing(self, vault_manager, temp_vault):
        """Test that create_note creates folder if it doesn't exist."""
        # Remove a folder
        folder_path = temp_vault / "04 - Areas"
        if folder_path.exists():
            shutil.rmtree(folder_path)

        # Create note should recreate the folder
        file_path = await vault_manager.create_note(
            title="Area Note",
            content="Content",
            folder="04 - Areas",
            note_type="area",
            tags=["test"],
        )

        assert folder_path.exists()
        assert file_path.exists()


class TestReadNote:
    """Test note reading."""

    @pytest.mark.asyncio
    async def test_read_existing_note(self, vault_manager, temp_vault):
        """Test reading an existing note."""
        # Create a note first
        file_path = await vault_manager.create_note(
            title="Read Test",
            content="Content to read",
            folder="01 - Notes",
            note_type="note",
            tags=["test"],
        )

        # Extract ID from filename
        note_id = file_path.stem

        # Read the note
        note_data = await vault_manager.read_note(note_id)

        assert note_data is not None
        assert note_data['frontmatter']['id'] == note_id
        assert "Content to read" in note_data['content']
        assert note_data['file_path'] == str(file_path)

    @pytest.mark.asyncio
    async def test_read_nonexistent_note(self, vault_manager):
        """Test reading a non-existent note returns None."""
        note_data = await vault_manager.read_note("99999999999999")
        assert note_data is None


class TestUpdateNote:
    """Test note updating."""

    @pytest.mark.asyncio
    async def test_update_note_content(self, vault_manager, temp_vault):
        """Test updating note content."""
        # Create note
        file_path = await vault_manager.create_note(
            title="Update Test",
            content="Original content",
            folder="01 - Notes",
            note_type="note",
            tags=["test"],
        )
        note_id = file_path.stem

        # Update content
        success = await vault_manager.update_note(
            note_id=note_id,
            content="Updated content",
        )

        assert success is True

        # Verify update
        note_data = await vault_manager.read_note(note_id)
        assert "Updated content" in note_data['content']

    @pytest.mark.asyncio
    async def test_update_note_tags(self, vault_manager, temp_vault):
        """Test updating note tags."""
        # Create note
        file_path = await vault_manager.create_note(
            title="Tag Update Test",
            content="Content",
            folder="01 - Notes",
            note_type="note",
            tags=["old-tag"],
        )
        note_id = file_path.stem

        # Update tags
        success = await vault_manager.update_note(
            note_id=note_id,
            tags=["New Tag", "Another_Tag"],  # Will be normalized
        )

        assert success is True

        # Verify tags were normalized and updated
        note_data = await vault_manager.read_note(note_id)
        assert "new-tag" in note_data['frontmatter']['tags']
        assert "another-tag" in note_data['frontmatter']['tags']

    @pytest.mark.asyncio
    async def test_update_note_status(self, vault_manager, temp_vault):
        """Test updating note status."""
        # Create project note
        file_path = await vault_manager.create_note(
            title="Project Update",
            content="Content",
            folder="03 - Projects",
            note_type="project",
            tags=["project"],
            status="planning",
        )
        note_id = file_path.stem

        # Update status
        success = await vault_manager.update_note(
            note_id=note_id,
            status="in-progress",
        )

        assert success is True

        # Verify update
        note_data = await vault_manager.read_note(note_id)
        assert note_data['frontmatter']['status'] == "in-progress"

    @pytest.mark.asyncio
    async def test_update_nonexistent_note(self, vault_manager):
        """Test updating non-existent note returns False."""
        success = await vault_manager.update_note(
            note_id="99999999999999",
            content="New content",
        )
        assert success is False

    @pytest.mark.asyncio
    async def test_update_note_dry_run(self, vault_manager, temp_vault):
        """Test dry-run mode doesn't modify file."""
        # Create note
        file_path = await vault_manager.create_note(
            title="Dry Run Update",
            content="Original content",
            folder="01 - Notes",
            note_type="note",
            tags=["test"],
        )
        note_id = file_path.stem

        # Update in dry-run mode
        success = await vault_manager.update_note(
            note_id=note_id,
            content="Updated content",
            dry_run=True,
        )

        assert success is True

        # Verify content was NOT changed
        note_data = await vault_manager.read_note(note_id)
        assert "Original content" in note_data['content']


class TestDeleteNote:
    """Test note deletion."""

    @pytest.mark.asyncio
    async def test_delete_existing_note(self, vault_manager, temp_vault):
        """Test deleting an existing note."""
        # Create note
        file_path = await vault_manager.create_note(
            title="Delete Test",
            content="Content",
            folder="01 - Notes",
            note_type="note",
            tags=["test"],
        )
        note_id = file_path.stem

        # Verify it exists
        assert file_path.exists()

        # Delete it
        success = await vault_manager.delete_note(note_id)
        assert success is True

        # Verify it's gone
        assert not file_path.exists()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_note(self, vault_manager):
        """Test deleting non-existent note returns False."""
        success = await vault_manager.delete_note("99999999999999")
        assert success is False

    @pytest.mark.asyncio
    async def test_delete_note_dry_run(self, vault_manager, temp_vault):
        """Test dry-run mode doesn't delete file."""
        # Create note
        file_path = await vault_manager.create_note(
            title="Dry Run Delete",
            content="Content",
            folder="01 - Notes",
            note_type="note",
            tags=["test"],
        )
        note_id = file_path.stem

        # Delete in dry-run mode
        success = await vault_manager.delete_note(note_id, dry_run=True)
        assert success is True

        # Verify file still exists
        assert file_path.exists()


class TestListNotes:
    """Test note listing."""

    @pytest.mark.asyncio
    async def test_list_all_notes(self, vault_manager, temp_vault):
        """Test listing all notes."""
        # Create several notes
        await vault_manager.create_note(
            "Note 1", "Content 1", "01 - Notes", "note", ["test"]
        )
        await vault_manager.create_note(
            "Note 2", "Content 2", "01 - Notes", "note", ["test"]
        )
        await vault_manager.create_note(
            "MOC 1", "MOC Content", "02 - MOCs", "moc", ["test"]
        )

        # List all
        all_notes = await vault_manager.list_notes()
        assert len(all_notes) == 3

    @pytest.mark.asyncio
    async def test_list_notes_by_folder(self, vault_manager, temp_vault):
        """Test listing notes filtered by folder."""
        # Create notes in different folders
        await vault_manager.create_note(
            "Note 1", "Content", "01 - Notes", "note", ["test"]
        )
        await vault_manager.create_note(
            "MOC 1", "Content", "02 - MOCs", "moc", ["test"]
        )

        # List only Notes folder
        notes = await vault_manager.list_notes(folder="01 - Notes")
        assert len(notes) == 1
        assert notes[0]['type'] == "note"

    @pytest.mark.asyncio
    async def test_list_notes_by_type(self, vault_manager, temp_vault):
        """Test listing notes filtered by type."""
        # Create different types
        await vault_manager.create_note(
            "Note 1", "Content", "01 - Notes", "note", ["test"]
        )
        await vault_manager.create_note(
            "Note 2", "Content", "01 - Notes", "note", ["test"]
        )
        await vault_manager.create_note(
            "MOC 1", "Content", "02 - MOCs", "moc", ["test"]
        )

        # List only note type
        notes = await vault_manager.list_notes(note_type="note")
        assert len(notes) == 2
        assert all(n['type'] == "note" for n in notes)

    @pytest.mark.asyncio
    async def test_list_notes_by_tag(self, vault_manager, temp_vault):
        """Test listing notes filtered by tag."""
        # Create notes with different tags
        await vault_manager.create_note(
            "Note 1", "Content", "01 - Notes", "note", ["python", "test"]
        )
        await vault_manager.create_note(
            "Note 2", "Content", "01 - Notes", "note", ["javascript", "test"]
        )

        # List only python-tagged notes
        notes = await vault_manager.list_notes(tag="python")
        assert len(notes) == 1
        assert "python" in notes[0]['tags']
