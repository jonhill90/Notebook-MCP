"""Pydantic models for Second Brain MCP Server.

This module enforces Second Brain frontmatter conventions through data validation.
All models follow the established patterns for:
- 14-character YYYYMMDDHHmmss IDs
- lowercase-hyphenated tags
- lowercase-hyphenated permalinks
- Folder-type validation
"""

from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional
import re


class NoteFrontmatter(BaseModel):
    """Enforces Second Brain frontmatter conventions.

    This model validates that note frontmatter follows all required conventions:
    - id: Must be 14-digit YYYYMMDDHHmmss format
    - type: Must be one of the valid note types
    - tags: Must be lowercase-hyphenated (no spaces, underscores, or uppercase)
    - permalink: Must be lowercase-hyphenated
    - created/updated: ISO 8601 datetime strings
    - status: Optional field for projects/tasks

    Example:
        ```python
        frontmatter = NoteFrontmatter(
            id="20251114020000",
            type="note",
            tags=["knowledge-management", "python"],
            created="2025-11-14T02:00:00",
            updated="2025-11-14T02:00:00",
            permalink="example-note"
        )
        ```

    Raises:
        ValidationError: If any field doesn't match conventions
    """

    id: str = Field(pattern=r'^\d{14}$', description="14-char YYYYMMDDHHmmss timestamp")
    type: Literal["note", "moc", "project", "area", "resource", "clipping"] = Field(
        description="Note type determines folder placement"
    )
    tags: list[str] = Field(description="lowercase-hyphenated tags only")
    created: str = Field(description="ISO 8601 datetime string")
    updated: str = Field(description="ISO 8601 datetime string")
    permalink: str = Field(description="lowercase-hyphenated slug for linking")
    status: Optional[str] = Field(default=None, description="Optional status for projects/tasks")

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Validate that all tags are lowercase-hyphenated.

        Tags must match pattern: ^[a-z0-9-]+$
        - Only lowercase letters, numbers, and hyphens
        - No spaces, underscores, or uppercase letters

        Args:
            v: List of tags to validate

        Returns:
            Validated list of tags

        Raises:
            ValueError: If any tag doesn't match pattern
        """
        for tag in v:
            if not re.match(r'^[a-z0-9-]+$', tag):
                raise ValueError(
                    f"Tag '{tag}' must be lowercase-hyphenated. "
                    f"Only lowercase letters, numbers, and hyphens allowed."
                )
        return v

    @field_validator('permalink')
    @classmethod
    def validate_permalink(cls, v: str) -> str:
        """Validate that permalink is lowercase-hyphenated.

        Permalink must match pattern: ^[a-z0-9-]+$
        - Only lowercase letters, numbers, and hyphens
        - No spaces, underscores, or uppercase letters

        Args:
            v: Permalink to validate

        Returns:
            Validated permalink

        Raises:
            ValueError: If permalink doesn't match pattern
        """
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError(
                f"Permalink '{v}' must be lowercase-hyphenated. "
                f"Only lowercase letters, numbers, and hyphens allowed."
            )
        return v


class TagCluster(BaseModel):
    """Represents a cluster of notes sharing a common tag.

    Used for MOC (Map of Content) generation when tag clusters reach threshold.
    Default threshold is 12 notes (configurable).

    Attributes:
        tag: The tag that groups these notes
        note_count: Number of notes with this tag
        notes: List of note IDs (14-char YYYYMMDDHHmmss format)
        should_create_moc: Flag indicating if MOC should be created

    Example:
        ```python
        cluster = TagCluster(
            tag="python",
            note_count=15,
            notes=["20251114020000", "20251114020100", ...],
            should_create_moc=False
        )

        # Check if threshold reached
        if cluster.check_threshold(threshold=12):
            print(f"MOC should be created for tag: {cluster.tag}")
        ```
    """

    tag: str = Field(description="Tag that groups these notes")
    note_count: int = Field(ge=0, description="Number of notes with this tag")
    notes: list[str] = Field(description="List of note IDs in this cluster")
    should_create_moc: bool = Field(default=False, description="Flag for MOC creation")

    def check_threshold(self, threshold: int = 12) -> bool:
        """Check if cluster size exceeds MOC creation threshold.

        When a tag cluster reaches the threshold, it suggests that enough
        content exists to warrant creating a Map of Content (MOC) to organize
        and provide context for those notes.

        Args:
            threshold: Minimum number of notes to trigger MOC creation (default: 12)

        Returns:
            True if cluster meets or exceeds threshold

        Side Effects:
            Sets self.should_create_moc to True if threshold met

        Example:
            ```python
            cluster = TagCluster(tag="python", note_count=15, notes=[...])

            # Default threshold (12)
            if cluster.check_threshold():
                print("Create MOC for python")

            # Custom threshold
            if cluster.check_threshold(threshold=20):
                print("Create MOC (stricter threshold)")
            ```
        """
        self.should_create_moc = self.note_count >= threshold
        return self.should_create_moc
