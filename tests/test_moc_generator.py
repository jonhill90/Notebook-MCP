"""Tests for MOCGenerator.

These tests verify that:
1. Tag clusters are identified correctly
2. MOCs are created when threshold is met
3. MOC content includes all note links
4. MOC is placed in correct folder (02 - MOCs)
5. Dry-run mode works as expected
6. Edge cases are handled properly
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import frontmatter

from src.vault.moc_generator import MOCGenerator
from src.vault.manager import VaultManager


@pytest.fixture
def temp_vault():
    """Create a temporary vault for testing with full 3-level structure."""
    temp_dir = tempfile.mkdtemp()
    vault_path = Path(temp_dir) / "test_vault"
    vault_path.mkdir()

    # Create full 3-level folder structure matching VaultManager.VALID_FOLDERS
    folders = [
        "00 - Inbox/00a - Active",
        "00 - Inbox/00b - Backlog",
        "00 - Inbox/00c - Clippings",
        "00 - Inbox/00d - Documents",
        "00 - Inbox/00e - Excalidraw",
        "00 - Inbox/00r - Research",
        "00 - Inbox/00t - Thoughts",
        "00 - Inbox/00v - Video",
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
        "05 - Resources/05v - Video",
    ]
    for folder in folders:
        (vault_path / folder).mkdir(parents=True, exist_ok=True)

    yield vault_path

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def vault_manager(temp_vault):
    """Create a VaultManager instance with temp vault."""
    return VaultManager(str(temp_vault))


@pytest.fixture
def moc_generator(temp_vault):
    """Create a MOCGenerator instance with temp vault."""
    return MOCGenerator(str(temp_vault), threshold=12)


class TestMOCGeneratorInitialization:
    """Test MOCGenerator initialization."""

    def test_init_with_valid_path(self, temp_vault):
        """Test initialization with valid vault path."""
        generator = MOCGenerator(str(temp_vault), threshold=10)
        assert generator.vault_path == temp_vault
        assert generator.threshold == 10

    def test_init_default_threshold(self, temp_vault):
        """Test initialization with default threshold."""
        generator = MOCGenerator(str(temp_vault))
        assert generator.threshold == 12  # Default from PRP

    def test_init_with_invalid_path(self):
        """Test initialization with non-existent path."""
        with pytest.raises(ValueError, match="Vault path does not exist"):
            MOCGenerator("/nonexistent/path")

    def test_init_with_file_path(self, temp_vault):
        """Test initialization with file instead of directory."""
        file_path = temp_vault / "test.txt"
        file_path.touch()

        with pytest.raises(ValueError, match="not a directory"):
            MOCGenerator(str(file_path))


class TestFindClusters:
    """Test cluster detection."""

    @pytest.mark.asyncio
    async def test_find_clusters_empty_vault(self, moc_generator):
        """Test finding clusters in empty vault."""
        clusters = moc_generator.find_clusters()
        assert clusters == []

    @pytest.mark.asyncio
    async def test_find_clusters_below_threshold(self, vault_manager, moc_generator):
        """Test that clusters below threshold are not returned."""
        # Create 11 notes with same tag (below threshold of 12)
        for i in range(11):
            await vault_manager.create_note(
                title=f"Note {i}",
                content=f"Content {i}",
                folder="01 - Notes/01a - Atomic",
                note_type="note",
                tags=["python"],
            )

        clusters = moc_generator.find_clusters()

        # python tag is below threshold, but month tag (on 11 notes) is below too
        assert len(clusters) == 0

    @pytest.mark.asyncio
    async def test_find_clusters_at_threshold(self, vault_manager, moc_generator):
        """Test that clusters at threshold are returned."""
        # Create exactly 12 notes (at threshold)
        for i in range(12):
            await vault_manager.create_note(
                title=f"Note {i}",
                content=f"Content {i}",
                folder="01 - Notes/01a - Atomic",
                note_type="note",
                tags=["python"],
            )

        clusters = moc_generator.find_clusters()

        # Should return 2 clusters: python (12) + month tag (12)
        assert len(clusters) == 2
        python_cluster = [c for c in clusters if c.tag == "python"][0]
        assert python_cluster.note_count == 12
        assert python_cluster.should_create_moc is True

    @pytest.mark.asyncio
    async def test_find_clusters_above_threshold(self, vault_manager, moc_generator):
        """Test that clusters above threshold are returned."""
        # Create 15 notes (above threshold)
        for i in range(15):
            await vault_manager.create_note(
                title=f"Note {i}",
                content=f"Content {i}",
                folder="01 - Notes/01a - Atomic",
                note_type="note",
                tags=["python"],
            )

        clusters = moc_generator.find_clusters()

        # Should return 2 clusters: python (15) + month tag (15)
        assert len(clusters) == 2
        python_cluster = [c for c in clusters if c.tag == "python"][0]
        assert python_cluster.note_count == 15
        assert python_cluster.should_create_moc is True

    @pytest.mark.asyncio
    async def test_find_multiple_clusters(self, vault_manager, moc_generator):
        """Test finding multiple clusters meeting threshold."""
        # Create 13 notes with "python" tag
        for i in range(13):
            await vault_manager.create_note(
                title=f"Python Note {i}",
                content=f"Python content {i}",
                folder="01 - Notes/01a - Atomic",
                note_type="note",
                tags=["python"],
            )

        # Create 14 notes with "javascript" tag
        for i in range(14):
            await vault_manager.create_note(
                title=f"JS Note {i}",
                content=f"JavaScript content {i}",
                folder="01 - Notes/01a - Atomic",
                note_type="note",
                tags=["javascript"],
            )

        # Create 10 notes with "rust" tag (below threshold)
        for i in range(10):
            await vault_manager.create_note(
                title=f"Rust Note {i}",
                content=f"Rust content {i}",
                folder="01 - Notes/01a - Atomic",
                note_type="note",
                tags=["rust"],
            )

        clusters = moc_generator.find_clusters()

        # Should return 3 clusters (python, javascript, and month tag - 37 total notes)
        assert len(clusters) == 3

        tags = {c.tag for c in clusters}
        assert "python" in tags
        assert "javascript" in tags
        assert "rust" not in tags

        # Verify counts
        python_cluster = next(c for c in clusters if c.tag == "python")
        js_cluster = next(c for c in clusters if c.tag == "javascript")

        assert python_cluster.note_count == 13
        assert js_cluster.note_count == 14

    @pytest.mark.asyncio
    async def test_find_clusters_with_multiple_tags(self, vault_manager, moc_generator):
        """Test that notes with multiple tags contribute to multiple clusters."""
        # Create 12 notes, each with both "python" and "web-dev" tags
        for i in range(12):
            await vault_manager.create_note(
                title=f"Note {i}",
                content=f"Content {i}",
                folder="01 - Notes/01a - Atomic",
                note_type="note",
                tags=["python", "web-dev"],
            )

        clusters = moc_generator.find_clusters()

        # Should find 3 clusters: python (12), web-dev (12), and month tag (12)
        assert len(clusters) == 3

        tags = {c.tag for c in clusters}
        assert "python" in tags
        assert "web-dev" in tags

        # All three should have 12 notes
        python_cluster = [c for c in clusters if c.tag == "python"][0]
        webdev_cluster = [c for c in clusters if c.tag == "web-dev"][0]
        assert python_cluster.note_count == 12
        assert webdev_cluster.note_count == 12

    @pytest.mark.asyncio
    async def test_find_clusters_ignores_notes_without_tags(self, vault_manager, moc_generator, temp_vault):
        """Test that notes without tags are skipped."""
        # Create note with tags
        for i in range(12):
            await vault_manager.create_note(
                title=f"Tagged Note {i}",
                content="Content",
                folder="01 - Notes/01a - Atomic",
                note_type="note",
                tags=["python"],
            )

        # Manually create note without tags (bypass VaultManager validation)
        notes_folder = temp_vault / "01 - Notes"
        bad_note_path = notes_folder / "20001231120000.md"
        with open(bad_note_path, 'w') as f:
            f.write("---\nid: '20001231120000'\n---\n\nContent without tags")

        clusters = moc_generator.find_clusters()

        # Should find 2 clusters: python (12) + month tag (12)
        # Bad note without tags is ignored
        assert len(clusters) == 2
        python_cluster = [c for c in clusters if c.tag == "python"][0]
        assert python_cluster.note_count == 12


class TestCreateMOC:
    """Test MOC creation."""

    @pytest.mark.asyncio
    async def test_create_moc_basic(self, moc_generator, vault_manager, temp_vault):
        """Test basic MOC creation."""
        # Create notes for cluster
        note_ids = []
        for i in range(15):
            file_path = await vault_manager.create_note(
                title=f"Python Note {i}",
                content=f"Content {i}",
                folder="01 - Notes/01a - Atomic",
                note_type="note",
                tags=["python"],
            )
            note_ids.append(file_path.stem)

        # Find cluster
        clusters = moc_generator.find_clusters()
        assert len(clusters) == 2  # python + month tag

        # Get python cluster
        cluster = [c for c in clusters if c.tag == "python"][0]

        # Create MOC
        moc_path = await moc_generator.create_moc(cluster)

        # Verify MOC exists
        assert moc_path.exists()

        # Verify MOC is in correct folder
        assert moc_path.parent.name == "02 - MOCs"

        # Parse and verify MOC frontmatter
        post = frontmatter.load(moc_path)
        metadata = post.metadata

        assert metadata['type'] == "MOC"
        assert "python" in metadata['tags']
        assert "moc" in metadata['tags']
        # Permalink now uses full path format (Session 6 change)
        assert "02-mocs" in metadata['permalink']
        assert metadata['id'] in metadata['permalink']

        # Verify MOC content
        content = post.content
        assert "# Python MOC" in content
        assert "Collection of 15 notes about python" in content
        assert "## Notes" in content

        # Verify all note links are present
        for note_id in note_ids:
            assert f"[[{note_id}]]" in content

    @pytest.mark.asyncio
    async def test_create_moc_title_formatting(self, moc_generator, vault_manager):
        """Test that MOC titles are formatted correctly."""
        # Test with hyphenated tag
        for i in range(12):
            await vault_manager.create_note(
                title=f"Note {i}",
                content="Content",
                folder="01 - Notes/01a - Atomic",
                note_type="note",
                tags=["machine-learning"],
            )

        clusters = moc_generator.find_clusters()
        cluster = clusters[0]

        moc_path = await moc_generator.create_moc(cluster)
        post = frontmatter.load(moc_path)

        # Title should be "Machine Learning MOC"
        assert "# Machine Learning MOC" in post.content
        assert "about machine learning" in post.content

    @pytest.mark.asyncio
    async def test_create_moc_dry_run(self, moc_generator, vault_manager, temp_vault):
        """Test dry-run mode doesn't create file."""
        # Create notes
        for i in range(12):
            await vault_manager.create_note(
                title=f"Note {i}",
                content="Content",
                folder="01 - Notes/01a - Atomic",
                note_type="note",
                tags=["python"],
            )

        clusters = moc_generator.find_clusters()
        cluster = clusters[0]

        # Create MOC in dry-run mode
        moc_path = await moc_generator.create_moc(cluster, dry_run=True)

        # File should NOT exist
        assert not moc_path.exists()

        # But path should be in correct folder
        assert "02 - MOCs" in str(moc_path)

    @pytest.mark.asyncio
    async def test_create_moc_custom_content(self, moc_generator, vault_manager):
        """Test creating MOC with custom content."""
        # Create notes
        for i in range(12):
            await vault_manager.create_note(
                title=f"Note {i}",
                content="Content",
                folder="01 - Notes/01a - Atomic",
                note_type="note",
                tags=["python"],
            )

        clusters = moc_generator.find_clusters()
        cluster = clusters[0]

        # Create MOC with custom content
        custom = "This is my custom MOC content.\n\n## Custom Section\n\nCustom text."
        moc_path = await moc_generator.create_moc(cluster, custom_content=custom)

        post = frontmatter.load(moc_path)

        # Should have custom content
        assert "This is my custom MOC content" in post.content
        assert "## Custom Section" in post.content

    @pytest.mark.asyncio
    async def test_create_moc_sorted_links(self, moc_generator, vault_manager):
        """Test that note links are sorted consistently."""
        # Create notes
        note_ids = []
        for i in range(12):
            file_path = await vault_manager.create_note(
                title=f"Note {i}",
                content="Content",
                folder="01 - Notes/01a - Atomic",
                note_type="note",
                tags=["python"],
            )
            note_ids.append(file_path.stem)

        clusters = moc_generator.find_clusters()
        moc_path = await moc_generator.create_moc(clusters[0])

        post = frontmatter.load(moc_path)
        content = post.content

        # Extract all note links
        import re
        links = re.findall(r'\[\[(\d{14})\]\]', content)

        # Links should be sorted
        assert links == sorted(links)


class TestCheckMOCNeeded:
    """Test checking if specific tag needs MOC."""

    @pytest.mark.asyncio
    async def test_check_moc_needed_true(self, moc_generator, vault_manager):
        """Test checking tag that needs MOC."""
        # Create 12 notes with python tag
        for i in range(12):
            await vault_manager.create_note(
                title=f"Note {i}",
                content="Content",
                folder="01 - Notes/01a - Atomic",
                note_type="note",
                tags=["python"],
            )

        cluster = await moc_generator.check_moc_needed("python")

        assert cluster is not None
        assert cluster.tag == "python"
        assert cluster.note_count == 12
        assert cluster.should_create_moc is True

    @pytest.mark.asyncio
    async def test_check_moc_needed_false(self, moc_generator, vault_manager):
        """Test checking tag that doesn't need MOC."""
        # Create only 10 notes (below threshold)
        for i in range(10):
            await vault_manager.create_note(
                title=f"Note {i}",
                content="Content",
                folder="01 - Notes/01a - Atomic",
                note_type="note",
                tags=["python"],
            )

        cluster = await moc_generator.check_moc_needed("python")

        assert cluster is None

    @pytest.mark.asyncio
    async def test_check_moc_needed_nonexistent_tag(self, moc_generator, vault_manager):
        """Test checking tag that doesn't exist."""
        # Create notes with different tag
        for i in range(12):
            await vault_manager.create_note(
                title=f"Note {i}",
                content="Content",
                folder="01 - Notes/01a - Atomic",
                note_type="note",
                tags=["python"],
            )

        cluster = await moc_generator.check_moc_needed("javascript")

        assert cluster is None


class TestCreateAllNeededMOCs:
    """Test bulk MOC creation."""

    @pytest.mark.asyncio
    async def test_create_all_needed_mocs_none_needed(self, moc_generator, vault_manager):
        """Test when no MOCs are needed."""
        # Create notes below threshold
        for i in range(10):
            await vault_manager.create_note(
                title=f"Note {i}",
                content="Content",
                folder="01 - Notes/01a - Atomic",
                note_type="note",
                tags=["python"],
            )

        moc_paths = await moc_generator.create_all_needed_mocs()

        assert len(moc_paths) == 0

    @pytest.mark.asyncio
    async def test_create_all_needed_mocs_multiple(self, moc_generator, vault_manager, temp_vault):
        """Test creating multiple MOCs at once."""
        # Create clusters for python (13 notes)
        for i in range(13):
            await vault_manager.create_note(
                title=f"Python Note {i}",
                content="Content",
                folder="01 - Notes/01a - Atomic",
                note_type="note",
                tags=["python"],
            )

        # Create clusters for javascript (12 notes)
        for i in range(12):
            await vault_manager.create_note(
                title=f"JS Note {i}",
                content="Content",
                folder="01 - Notes/01a - Atomic",
                note_type="note",
                tags=["javascript"],
            )

        # Create below threshold (10 notes)
        for i in range(10):
            await vault_manager.create_note(
                title=f"Rust Note {i}",
                content="Content",
                folder="01 - Notes/01a - Atomic",
                note_type="note",
                tags=["rust"],
            )

        moc_paths = await moc_generator.create_all_needed_mocs()

        # Should create 3 MOCs (python, javascript, and auto-added month tag - total 35 notes)
        # Month tag appears on all 35 notes, exceeding threshold
        assert len(moc_paths) == 3

        # Verify both exist
        for moc_path in moc_paths:
            assert moc_path.exists()
            assert moc_path.parent.name == "02 - MOCs"

    @pytest.mark.asyncio
    async def test_create_all_needed_mocs_dry_run(self, moc_generator, vault_manager):
        """Test dry-run mode for bulk creation."""
        # Create clusters
        for i in range(12):
            await vault_manager.create_note(
                title=f"Note {i}",
                content="Content",
                folder="01 - Notes/01a - Atomic",
                note_type="note",
                tags=["python"],
            )

        moc_paths = await moc_generator.create_all_needed_mocs(dry_run=True)

        # Should return paths (python tag + auto-added month tag on 12 notes)
        assert len(moc_paths) == 2

        # But files should NOT exist
        for moc_path in moc_paths:
            assert not moc_path.exists()


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_custom_threshold(self, vault_manager, temp_vault):
        """Test MOC generator with custom threshold."""
        # Create generator with threshold of 5
        generator = MOCGenerator(str(temp_vault), threshold=5)

        # Create 6 notes
        for i in range(6):
            await vault_manager.create_note(
                title=f"Note {i}",
                content="Content",
                folder="01 - Notes/01a - Atomic",
                note_type="note",
                tags=["python"],
            )

        clusters = generator.find_clusters()

        # Should find 2 clusters (python tag + auto-added month tag on 6 notes)
        assert len(clusters) == 2
        # One cluster should be python with 6 notes
        python_cluster = [c for c in clusters if c.tag == "python"][0]
        assert python_cluster.note_count == 6

    @pytest.mark.asyncio
    async def test_notes_across_folders(self, vault_manager, moc_generator):
        """Test that clusters include notes from all folders."""
        # Create notes in different folders with same tag
        for i in range(6):
            await vault_manager.create_note(
                title=f"Note {i}",
                content="Content",
                folder="01 - Notes/01a - Atomic",
                note_type="note",
                tags=["python"],
            )

        for i in range(7):
            await vault_manager.create_note(
                title=f"Resource {i}",
                content="Content",
                folder="05 - Resources/05d - Documents",
                note_type="resource",
                tags=["python"],
            )

        clusters = moc_generator.find_clusters()

        # Should find 2 clusters: python (6 + 7 = 13) + auto-added month tag (13 notes)
        assert len(clusters) == 2
        # Python cluster should have combined notes from both folders
        python_cluster = [c for c in clusters if c.tag == "python"][0]
        assert python_cluster.note_count == 13
