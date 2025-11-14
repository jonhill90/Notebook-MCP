"""MOC (Map of Content) Generator for Second Brain.

This module provides automatic MOC generation when tag clusters reach threshold.
MOCs help organize and provide context for growing collections of related notes.

Default threshold: 12 notes per tag
"""

from pathlib import Path
from collections import defaultdict
from typing import List, Optional, Dict
import frontmatter  # type: ignore[import-untyped]
from loguru import logger

from ..models import TagCluster


class MOCGenerator:
    """Generates Maps of Content (MOCs) for tag clusters.

    The MOCGenerator identifies when a tag has accumulated enough notes (default: 12)
    to warrant creating a MOC. MOCs provide organization and context for collections
    of related notes.

    Attributes:
        vault_path: Path to the Second Brain vault
        threshold: Minimum number of notes to trigger MOC creation (default: 12)

    Example:
        ```python
        generator = MOCGenerator("/path/to/vault", threshold=12)

        # Find all tag clusters above threshold
        clusters = generator.find_clusters()

        # Create MOC for a specific cluster
        for cluster in clusters:
            if cluster.should_create_moc:
                moc_path = await generator.create_moc(cluster)
                print(f"Created MOC: {moc_path}")
        ```
    """

    def __init__(self, vault_path: str, threshold: int = 12):
        """Initialize the MOCGenerator.

        Args:
            vault_path: Path to the Second Brain vault directory
            threshold: Minimum notes per tag to trigger MOC creation (default: 12)

        Raises:
            ValueError: If vault_path doesn't exist or isn't a directory
        """
        self.vault_path = Path(vault_path)
        self.threshold = threshold

        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {vault_path}")
        if not self.vault_path.is_dir():
            raise ValueError(f"Vault path is not a directory: {vault_path}")

        logger.info(
            f"MOCGenerator initialized with vault: {vault_path}, threshold: {threshold}"
        )

    def find_clusters(self) -> List[TagCluster]:
        """Find tag clusters that exceed threshold.

        Scans all notes in the vault and builds a mapping of tags to notes.
        Returns only clusters that meet or exceed the threshold.

        Returns:
            List of TagCluster objects with should_create_moc=True

        Example:
            >>> generator = MOCGenerator("/vault", threshold=12)
            >>> clusters = generator.find_clusters()
            >>> for cluster in clusters:
            ...     print(f"Tag '{cluster.tag}' has {cluster.note_count} notes")
            Tag 'python' has 15 notes
            Tag 'knowledge-management' has 13 notes
        """
        # Build tag -> notes mapping
        tag_to_notes: Dict[str, List[str]] = defaultdict(list)

        # Scan all markdown files in vault
        for md_file in self.vault_path.rglob("*.md"):
            try:
                post = frontmatter.load(md_file)

                # Check if note has required metadata
                if 'tags' not in post.metadata:
                    continue
                if 'id' not in post.metadata:
                    logger.warning(f"Note missing ID: {md_file}")
                    continue

                # Add note to each tag's cluster
                note_id = post.metadata['id']
                for tag in post.metadata['tags']:
                    tag_to_notes[tag].append(note_id)

            except Exception as e:
                logger.warning(f"Error reading {md_file}: {e}")
                continue

        # Create clusters for tags meeting threshold
        clusters = []
        for tag, notes in tag_to_notes.items():
            cluster = TagCluster(
                tag=tag,
                note_count=len(notes),
                notes=notes,
                should_create_moc=False
            )

            # Check if cluster meets threshold
            if cluster.check_threshold(self.threshold):
                clusters.append(cluster)
                logger.info(
                    f"Cluster '{tag}' meets threshold: {cluster.note_count} notes"
                )

        return clusters

    async def create_moc(
        self,
        cluster: TagCluster,
        dry_run: bool = False,
        custom_content: Optional[str] = None
    ) -> Path:
        """Generate MOC for tag cluster.

        Creates a Map of Content file in the "02 - MOCs" folder with links to
        all notes in the cluster.

        Args:
            cluster: TagCluster to create MOC for
            dry_run: If True, returns path without creating file (default: False)
            custom_content: Optional custom content to add (default: auto-generated)

        Returns:
            Path to created MOC file

        Raises:
            ValueError: If cluster doesn't meet threshold or VaultManager fails

        Example:
            >>> cluster = TagCluster(tag="python", note_count=15, notes=[...])
            >>> moc_path = await generator.create_moc(cluster)
            >>> print(f"MOC created at: {moc_path}")
            MOC created at: /vault/02 - MOCs/20251114020000.md
        """
        if not cluster.should_create_moc:
            logger.warning(
                f"Cluster '{cluster.tag}' doesn't meet threshold "
                f"({cluster.note_count} < {self.threshold})"
            )
            # We'll still allow creation if explicitly called,
            # but log a warning

        # Generate MOC title
        # Convert tag to title case (e.g., "python" -> "Python")
        # Handle hyphenated tags (e.g., "machine-learning" -> "Machine Learning")
        title_words = cluster.tag.replace('-', ' ').split()
        title = ' '.join(word.capitalize() for word in title_words)
        moc_title = f"{title} MOC"

        # Generate content
        if custom_content:
            content = custom_content
        else:
            content = self._generate_moc_content(cluster, title)

        # Create via VaultManager
        # Import here to avoid circular dependency
        from .manager import VaultManager

        vault = VaultManager(str(self.vault_path))

        try:
            file_path = await vault.create_note(
                title=moc_title,
                content=content,
                folder="02 - MOCs",
                note_type="moc",
                tags=[cluster.tag, "moc"],
                dry_run=dry_run
            )

            logger.info(f"MOC created for tag '{cluster.tag}': {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Failed to create MOC for '{cluster.tag}': {e}")
            raise

    def _generate_moc_content(self, cluster: TagCluster, title: str) -> str:
        """Generate default MOC content.

        Args:
            cluster: TagCluster to generate content for
            title: Formatted title (e.g., "Python")

        Returns:
            Generated markdown content

        Example content:
            ```markdown
            Collection of 15 notes about python

            ## Notes

            - [[20251114020000]]
            - [[20251114020100]]
            ...
            ```
        """
        content = f"Collection of {cluster.note_count} notes about {title.lower()}\n\n"
        content += "## Notes\n\n"

        # Link to all notes in cluster
        for note_id in sorted(cluster.notes):  # Sort for consistency
            content += f"- [[{note_id}]]\n"

        return content

    async def check_moc_needed(self, tag: str) -> Optional[TagCluster]:
        """Check if a specific tag needs a MOC.

        Args:
            tag: Tag to check

        Returns:
            TagCluster if threshold met, None otherwise

        Example:
            >>> cluster = await generator.check_moc_needed("python")
            >>> if cluster:
            ...     print(f"MOC needed for {cluster.tag}")
        """
        clusters = self.find_clusters()

        for cluster in clusters:
            if cluster.tag == tag:
                return cluster

        return None

    async def create_all_needed_mocs(self, dry_run: bool = False) -> List[Path]:
        """Create MOCs for all clusters exceeding threshold.

        Convenience method to generate all needed MOCs in one call.

        Args:
            dry_run: If True, simulates creation without writing files

        Returns:
            List of paths to created MOC files

        Example:
            >>> moc_paths = await generator.create_all_needed_mocs()
            >>> print(f"Created {len(moc_paths)} MOCs")
        """
        clusters = self.find_clusters()

        if not clusters:
            logger.info("No clusters meet threshold, no MOCs needed")
            return []

        logger.info(f"Creating MOCs for {len(clusters)} clusters")

        created_mocs = []
        for cluster in clusters:
            try:
                moc_path = await self.create_moc(cluster, dry_run=dry_run)
                created_mocs.append(moc_path)
            except Exception as e:
                logger.error(f"Failed to create MOC for '{cluster.tag}': {e}")
                continue

        logger.info(f"Successfully created {len(created_mocs)} MOCs")
        return created_mocs
