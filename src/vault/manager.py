"""Vault manager for Second Brain MCP Server.

This module provides the core CRUD operations for the Second Brain vault with
strict enforcement of conventions:
- Folder structure (00-05 system)
- ID generation (YYYYMMDDHHmmss format)
- Frontmatter validation
- Tag normalization
"""

from pathlib import Path
from datetime import datetime
from typing import Optional, Any, Literal, cast
import asyncio
import frontmatter  # type: ignore[import-untyped]
from loguru import logger

from ..models import NoteFrontmatter


class VaultManager:
    """Manages all note CRUD operations with convention enforcement.

    The VaultManager ensures that all notes created follow Second Brain conventions:
    - Notes are placed in the correct folder based on type
    - IDs are unique and follow YYYYMMDDHHmmss format
    - Frontmatter is validated and complete
    - Tags are normalized to lowercase-hyphenated format

    Attributes:
        vault_path: Path to the Second Brain vault
        valid_folders: Mapping of folder names to allowed note types

    Example:
        ```python
        manager = VaultManager("/path/to/vault")

        # Create a note
        file_path = await manager.create_note(
            title="My First Note",
            content="This is the content",
            folder="01 - Notes",
            note_type="note",
            tags=["python", "learning"]
        )

        # Read a note
        note = await manager.read_note(note_id="20251114020000")

        # Update a note
        await manager.update_note(
            note_id="20251114020000",
            content="Updated content",
            tags=["python", "learning", "advanced"]
        )
        ```
    """

    # Valid folder structure for Second Brain
    # Maps folder names to allowed note types in that folder
    VALID_FOLDERS: dict[str, list[str]] = {
        # Inbox subfolders
        "00 - Inbox/00a - Active": ["thought", "todo"],
        "00 - Inbox/00b - Backlog": ["thought", "todo"],
        "00 - Inbox/00c - Clippings": ["clipping"],
        "00 - Inbox/00d - Documents": ["clipping", "resource"],
        "00 - Inbox/00e - Excalidraw": ["clipping"],
        "00 - Inbox/00r - Research": ["thought", "note"],
        "00 - Inbox/00t - Thoughts": ["thought"],
        "00 - Inbox/00v - Video": ["clipping"],
        # Notes subfolders
        "01 - Notes/01a - Atomic": ["note"],
        "01 - Notes/01m - Meetings": ["note"],
        "01 - Notes/01r - Research": ["note"],
        # MOCs
        "02 - MOCs": ["moc"],
        # Projects subfolders
        "03 - Projects/03b - Personal": ["project"],
        "03 - Projects/03c - Work": ["project"],
        "03 - Projects/03p - PRPs": ["note"],  # PRPs stored as notes
        # Areas
        "04 - Areas": ["area"],
        # Resources subfolders
        "05 - Resources/05c - Clippings": ["clipping"],
        "05 - Resources/05d - Documents": ["resource"],
        "05 - Resources/05e - Examples": ["resource"],
        "05 - Resources/05l - Learning": ["resource", "clipping"],
        "05 - Resources/05r - Repos": ["resource"],
        "05 - Resources/05v - Video": ["clipping"],
    }

    # Type display names for frontmatter (capitalized per templates)
    TYPE_DISPLAY_NAMES = {
        "note": "Note",
        "research": "Research",
        "meeting": "Meeting",
        "thought": "Thought",
        "moc": "Map of Content",
        "project": "Project",
        "area": "Area",
        "resource": "resource",  # Lowercase per process-clipping template
        "clipping": "resource",  # Clippings use "resource" type
        "todo": "Todo",
        "prp": "PRP",
    }

    def __init__(self, vault_path: str):
        """Initialize the VaultManager.

        Args:
            vault_path: Path to the Second Brain vault directory

        Raises:
            ValueError: If vault_path doesn't exist or isn't a directory
        """
        self.vault_path = Path(vault_path)

        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {vault_path}")
        if not self.vault_path.is_dir():
            raise ValueError(f"Vault path is not a directory: {vault_path}")

        self.valid_folders = self.VALID_FOLDERS
        logger.info(f"VaultManager initialized with vault path: {vault_path}")

    def generate_id(self) -> str:
        """Generate a 14-character ID in YYYYMMDDHHmmss format.

        Returns:
            14-character timestamp string

        Example:
            >>> manager.generate_id()
            '20251114020000'
        """
        return datetime.now().strftime("%Y%m%d%H%M%S")

    async def generate_unique_id(self) -> str:
        """Generate a unique 14-character ID, handling collisions.

        This addresses the ID collision gotcha from the PRP: agents create notes
        faster than humans (multiple per second). If a collision is detected,
        we wait 1 second and regenerate.

        Returns:
            Unique 14-character timestamp string

        Note:
            Logs collision events for monitoring

        Example:
            >>> manager = VaultManager("/vault")
            >>> unique_id = await manager.generate_unique_id()
            '20251114020000'  # Guaranteed unique
        """
        while True:
            note_id = self.generate_id()

            # Check if ID already exists in any folder
            collision_found = False
            for folder in self.valid_folders.keys():
                folder_path = self.vault_path / folder
                if folder_path.exists():
                    potential_file = folder_path / f"{note_id}.md"
                    if potential_file.exists():
                        collision_found = True
                        logger.warning(f"ID collision detected: {note_id}, waiting 1 second")
                        break

            if not collision_found:
                return note_id

            # Wait 1 second and try again
            await asyncio.sleep(1)

    def validate_folder_type(self, folder: str, note_type: str) -> None:
        """Validate that note type is allowed in the specified folder.

        Args:
            folder: Folder name (e.g., "01 - Notes")
            note_type: Note type (e.g., "note", "moc")

        Raises:
            ValueError: If folder is invalid or note_type not allowed in folder

        Example:
            >>> manager.validate_folder_type("01 - Notes", "note")  # OK
            >>> manager.validate_folder_type("01 - Notes", "moc")   # Raises ValueError
        """
        if folder not in self.valid_folders:
            raise ValueError(
                f"Invalid folder: '{folder}'. "
                f"Valid folders: {list(self.valid_folders.keys())}"
            )

        if note_type not in self.valid_folders[folder]:
            raise ValueError(
                f"Note type '{note_type}' not allowed in folder '{folder}'. "
                f"Allowed types: {self.valid_folders[folder]}"
            )

    @staticmethod
    def normalize_tag(tag: str) -> str:
        """Normalize a tag to lowercase-hyphenated format.

        This addresses the tag fragmentation gotcha from the PRP. Converts:
        - Spaces to hyphens
        - Underscores to hyphens
        - Uppercase to lowercase

        Args:
            tag: Tag to normalize

        Returns:
            Normalized tag in lowercase-hyphenated format

        Example:
            >>> VaultManager.normalize_tag("AI & ML")
            'ai-ml'
            >>> VaultManager.normalize_tag("Knowledge_Management")
            'knowledge-management'
        """
        # Convert to lowercase
        normalized = tag.lower()

        # Replace spaces and underscores with hyphens
        normalized = normalized.replace(" ", "-").replace("_", "-")

        # Remove non-alphanumeric characters except hyphens
        import re
        normalized = re.sub(r'[^a-z0-9-]', '', normalized)

        # Remove multiple consecutive hyphens
        normalized = re.sub(r'-+', '-', normalized)

        # Remove leading/trailing hyphens
        normalized = normalized.strip('-')

        return normalized

    @staticmethod
    def normalize_permalink(title: str) -> str:
        """Convert title to lowercase-hyphenated permalink.

        Args:
            title: Note title

        Returns:
            Normalized permalink

        Example:
            >>> VaultManager.normalize_permalink("My First Note!")
            'my-first-note'
        """
        # Use the same normalization logic as tags
        return VaultManager.normalize_tag(title)

    async def create_note(
        self,
        title: str,
        content: str,
        folder: str,
        note_type: str,
        tags: list[str],
        dry_run: bool = False,
    ) -> Path:
        """Create a new note with convention enforcement.

        This is the primary method for creating notes. It:
        1. Validates folder/type combination
        2. Generates unique ID (14-char YYYYMMDDHHmmss)
        3. Normalizes tags and auto-adds month tag
        4. Creates frontmatter with proper display names
        5. Writes file to vault

        Args:
            title: Note title (will be converted to permalink)
            content: Note content (markdown)
            folder: Target folder (e.g., "01 - Notes/01a - Atomic")
            note_type: Note type (e.g., "note", "research", "meeting")
            tags: List of tags (will be normalized, month tag auto-added)
            dry_run: If True, returns preview without creating file (default: False)

        Returns:
            Path to created note file

        Raises:
            ValueError: If folder/type combination invalid or validation fails

        Example:
            >>> manager = VaultManager("/vault")
            >>> path = await manager.create_note(
            ...     title="Python Best Practices",
            ...     content="# Python Best Practices\\n\\n...",
            ...     folder="01 - Notes/01a - Atomic",
            ...     note_type="note",
            ...     tags=["python", "best-practices"]
            ... )
            >>> print(path)
            /vault/01 - Notes/01a - Atomic/20251114020000.md
        """
        # Validate folder/type combination
        self.validate_folder_type(folder, note_type)

        # Generate unique ID
        note_id = await self.generate_unique_id()

        # Normalize tags
        normalized_tags = [self.normalize_tag(tag) for tag in tags]

        # Auto-add month tag (MM-YYYY format)
        month_tag = datetime.now().strftime("%m-%Y")
        if month_tag not in normalized_tags:
            normalized_tags.append(month_tag)

        # Generate permalink with full path (folder/id)
        # Convert folder path to lowercase-hyphenated format for permalink
        # Handle spaces around hyphens: "01 - Notes" -> "01-notes"
        folder_permalink = folder.lower().replace(" - ", "-").replace(" ", "-")
        permalink = f"{folder_permalink}/{note_id}"

        # Create simple date format (YYYY-MM-DD)
        today = datetime.now().strftime("%Y-%m-%d")

        # Get display name for type (capitalized per templates)
        type_display = self.TYPE_DISPLAY_NAMES.get(note_type, note_type.title())

        # Create frontmatter model (validates conventions)
        try:
            fm = NoteFrontmatter(
                id=note_id,
                type=type_display,
                tags=normalized_tags,
                created=today,
                updated=today,
                permalink=permalink,
            )
        except Exception as e:
            raise ValueError(f"Frontmatter validation failed: {e}")

        # Dry-run mode: return preview
        if dry_run:
            preview = {
                "preview": f"Would create file at: {folder}/{note_id}.md",
                "frontmatter": fm.model_dump(),
                "title": title,
                "content_length": len(content),
            }
            logger.info(f"Dry-run mode: {preview}")
            return Path(folder) / f"{note_id}.md"

        # Create folder if it doesn't exist
        folder_path = self.vault_path / folder
        folder_path.mkdir(parents=True, exist_ok=True)

        # Create file path
        file_path = folder_path / f"{note_id}.md"

        # Create frontmatter post
        # Add title to content
        full_content = f"# {title}\n\n{content}"
        post = frontmatter.Post(full_content, **fm.model_dump())

        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))

        logger.info(f"Created note: {file_path}")
        return file_path

    async def read_note(self, note_id: str) -> Optional[dict[str, Any]]:
        """Read a note by ID.

        Searches all valid folders for a note with the given ID.

        Args:
            note_id: 14-character note ID

        Returns:
            Dictionary containing note data:
                - frontmatter: Parsed frontmatter dict
                - content: Note content
                - file_path: Path to note file
            Returns None if note not found

        Example:
            >>> note = await manager.read_note("20251114020000")
            >>> print(note['frontmatter']['title'])
            'My Note'
        """
        # Search all folders recursively for the note
        for folder in self.valid_folders.keys():
            folder_path = self.vault_path / folder

            # Search recursively in subfolders
            for file_path in folder_path.rglob(f"{note_id}.md"):
                # Parse frontmatter
                post = frontmatter.load(file_path)

                return {
                    "frontmatter": post.metadata,
                    "content": post.content,
                    "file_path": str(file_path),
                }

        logger.warning(f"Note not found: {note_id}")
        return None

    async def update_note(
        self,
        note_id: str,
        content: Optional[str] = None,
        tags: Optional[list[str]] = None,
        status: Optional[str] = None,
        dry_run: bool = False,
    ) -> bool:
        """Update an existing note.

        Updates specified fields while preserving others.
        Updates the 'updated' timestamp automatically.

        Args:
            note_id: 14-character note ID
            content: New content (optional, keeps existing if not provided)
            tags: New tags (optional, normalized automatically)
            status: New status (optional)
            dry_run: If True, returns preview without updating

        Returns:
            True if update successful, False if note not found

        Example:
            >>> await manager.update_note(
            ...     note_id="20251114020000",
            ...     tags=["python", "updated"],
            ...     status="in-progress"
            ... )
            True
        """
        # Find the note
        note_data = await self.read_note(note_id)
        if not note_data:
            return False

        file_path = Path(note_data['file_path'])
        post = frontmatter.load(file_path)

        # Update content if provided
        if content is not None:
            post.content = content

        # Update tags if provided (normalize them)
        if tags is not None:
            normalized_tags = [self.normalize_tag(tag) for tag in tags]
            post.metadata['tags'] = normalized_tags

        # Update status if provided
        if status is not None:
            post.metadata['status'] = status

        # Update timestamp
        post.metadata['updated'] = datetime.now().isoformat()

        # Dry-run mode: return preview
        if dry_run:
            preview = {
                "preview": f"Would update file at: {file_path}",
                "frontmatter": post.metadata,
                "content_length": len(post.content),
            }
            logger.info(f"Dry-run mode: {preview}")
            return True

        # Write updated file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))

        logger.info(f"Updated note: {file_path}")
        return True

    async def delete_note(self, note_id: str, dry_run: bool = False) -> bool:
        """Delete a note by ID.

        Args:
            note_id: 14-character note ID
            dry_run: If True, returns preview without deleting

        Returns:
            True if deletion successful, False if note not found

        Example:
            >>> await manager.delete_note("20251114020000")
            True
        """
        # Find the note
        note_data = await self.read_note(note_id)
        if not note_data:
            return False

        file_path = Path(note_data['file_path'])

        # Dry-run mode: return preview
        if dry_run:
            logger.info(f"Dry-run mode: Would delete file at: {file_path}")
            return True

        # Delete the file
        file_path.unlink()
        logger.info(f"Deleted note: {file_path}")
        return True

    async def list_notes(
        self,
        folder: Optional[str] = None,
        note_type: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """List notes matching criteria.

        Args:
            folder: Filter by folder (optional)
            note_type: Filter by note type (optional)
            tag: Filter by tag (optional)

        Returns:
            List of note metadata dictionaries

        Example:
            >>> notes = await manager.list_notes(folder="01 - Notes", tag="python")
            >>> print(f"Found {len(notes)} Python notes")
        """
        results = []

        # Determine which folders to search
        folders_to_search = [folder] if folder else list(self.valid_folders.keys())

        for folder_name in folders_to_search:
            folder_path = self.vault_path / folder_name

            if not folder_path.exists():
                continue

            # Find all markdown files
            for file_path in folder_path.glob("*.md"):
                try:
                    post = frontmatter.load(file_path)
                    metadata = post.metadata

                    # Apply filters
                    if note_type and metadata.get('type') != note_type:
                        continue

                    if tag and tag not in metadata.get('tags', []):
                        continue

                    results.append({
                        "id": metadata.get('id'),
                        "type": metadata.get('type'),
                        "tags": metadata.get('tags', []),
                        "created": metadata.get('created'),
                        "updated": metadata.get('updated'),
                        "permalink": metadata.get('permalink'),
                        "file_path": str(file_path),
                    })

                except Exception as e:
                    logger.warning(f"Error reading {file_path}: {e}")
                    continue

        return results
