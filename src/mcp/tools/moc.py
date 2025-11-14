"""MCP tool for MOC (Map of Content) generation.

This module provides the create_moc MCP tool that generates MOCs for
tag clusters when they reach the threshold.

Pattern: Follows basic-memory MCP tool patterns (async functions, structured returns)
Critical Gotchas Addressed:
- Threshold checking (default: 12 notes)
- MOC creation with proper linking
- Placement in "02 - MOCs" folder

Reference: prps/INITIAL_personal_notebook_mcp.md (Task 2.2)
"""

import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)


async def create_moc(
    tag: str,
    threshold: Optional[int] = None,
    dry_run: bool = False
) -> dict[str, Any]:
    """Create a Map of Content (MOC) for a tag cluster.

    This MCP tool finds all notes with a specific tag and creates a MOC
    if the note count meets the threshold. Supports dry-run mode for preview.

    Args:
        tag: Tag to create MOC for (lowercase-hyphenated)
        threshold: Minimum note count (default: 12)
        dry_run: If True, return preview without creating file

    Returns:
        dict: MOC creation result with structure:
            {
                "tag": str,              # Tag MOC was created for
                "note_count": int,       # Number of notes in cluster
                "threshold": int,        # Threshold used
                "should_create": bool,   # Whether threshold was met
                "moc_created": bool,     # Whether MOC was created
                "note_id": str,          # Generated MOC note ID (if created)
                "file_path": str,        # Path to MOC file (if created)
                "preview": str           # Preview of MOC content (if dry_run)
            }

    Raises:
        ValueError: If tag is empty or invalid
        RuntimeError: If environment variables missing

    Example:
        ```python
        # Check if MOC should be created (dry run)
        result = await create_moc(tag="vector-search", dry_run=True)

        # Result (threshold not met):
        # {
        #     "tag": "vector-search",
        #     "note_count": 8,
        #     "threshold": 12,
        #     "should_create": False,
        #     "moc_created": False,
        #     "preview": "Would create MOC with 8 notes (threshold: 12)"
        # }

        # Result (threshold met):
        # {
        #     "tag": "vector-search",
        #     "note_count": 15,
        #     "threshold": 12,
        #     "should_create": True,
        #     "moc_created": False,
        #     "preview": "# Vector Search MOC\\n\\nCollection of 15 notes...\\n\\n## Notes\\n\\n- [[20251114...]]\n..."
        # }

        # Create MOC (for real)
        result = await create_moc(tag="vector-search")

        # Result:
        # {
        #     "tag": "vector-search",
        #     "note_count": 15,
        #     "threshold": 12,
        #     "should_create": True,
        #     "moc_created": True,
        #     "note_id": "20251114154000",
        #     "file_path": "/vault/02 - MOCs/20251114154000.md"
        # }
        ```

    Pattern: MOCGenerator finds clusters and creates MOCs via VaultManager
    """
    # Validation
    if not tag or not tag.strip():
        raise ValueError("Tag cannot be empty or whitespace only")

    # Normalize tag to lowercase-hyphenated
    normalized_tag = tag.lower().replace(" ", "-").replace("_", "-")

    # Default threshold
    if threshold is None:
        threshold = 12

    if threshold < 1:
        raise ValueError("Threshold must be at least 1")

    # Get environment variable
    vault_path = os.getenv("VAULT_PATH")
    if not vault_path:
        raise RuntimeError("VAULT_PATH environment variable not set")

    # Import MOCGenerator (local import to avoid circular dependencies)
    from ...vault.moc_generator import MOCGenerator

    try:
        # Initialize generator
        generator = MOCGenerator(vault_path, threshold=threshold)

        # Find all clusters
        clusters = generator.find_clusters()

        # Find cluster for this tag
        target_cluster = None
        for cluster in clusters:
            if cluster.tag == normalized_tag:
                target_cluster = cluster
                break

        # If cluster not found, build it manually
        if target_cluster is None:
            from ...models import TagCluster
            # Build cluster from vault
            import frontmatter  # type: ignore[import-untyped]
            from pathlib import Path

            vault_path_obj = Path(vault_path)
            tag_notes = []

            for md_file in vault_path_obj.rglob("*.md"):
                post = frontmatter.load(md_file)
                if 'tags' in post.metadata and 'id' in post.metadata:
                    if normalized_tag in post.metadata['tags']:
                        tag_notes.append(post.metadata['id'])

            target_cluster = TagCluster(
                tag=normalized_tag,
                note_count=len(tag_notes),
                notes=tag_notes
            )
            target_cluster.check_threshold(threshold)

        # Check if should create
        should_create = target_cluster.should_create_moc

        # Dry run mode: return preview
        if dry_run:
            if not should_create:
                preview = (
                    f"Would create MOC with {target_cluster.note_count} notes "
                    f"(threshold: {threshold})"
                )
            else:
                # Generate preview content
                title = f"{normalized_tag.replace('-', ' ').title()} MOC"
                preview = f"# {title}\n\n"
                preview += (
                    f"Collection of {target_cluster.note_count} notes "
                    f"about {normalized_tag}\n\n"
                )
                preview += "## Notes\n\n"
                for note_id in target_cluster.notes[:5]:  # Show first 5
                    preview += f"- [[{note_id}]]\n"
                if len(target_cluster.notes) > 5:
                    preview += f"- ... ({len(target_cluster.notes) - 5} more notes)\n"

            return {
                "tag": normalized_tag,
                "note_count": target_cluster.note_count,
                "threshold": threshold,
                "should_create": should_create,
                "moc_created": False,
                "preview": preview
            }

        # Check threshold
        if not should_create:
            logger.info(
                f"MCP create_moc: tag '{normalized_tag}' has "
                f"{target_cluster.note_count} notes (threshold: {threshold}), "
                f"not creating MOC"
            )
            return {
                "tag": normalized_tag,
                "note_count": target_cluster.note_count,
                "threshold": threshold,
                "should_create": False,
                "moc_created": False
            }

        # Create MOC
        file_path = await generator.create_moc(target_cluster)
        note_id = file_path.stem

        logger.info(
            f"MCP create_moc: created MOC '{note_id}' for tag '{normalized_tag}' "
            f"({target_cluster.note_count} notes)"
        )

        # Return result
        return {
            "tag": normalized_tag,
            "note_count": target_cluster.note_count,
            "threshold": threshold,
            "should_create": True,
            "moc_created": True,
            "note_id": note_id,
            "file_path": str(file_path)
        }

    except Exception as e:
        logger.error(f"MCP create_moc error: {e}", exc_info=True)
        raise
