"""Tag analyzer for Second Brain MCP Server.

This module provides intelligent tag suggestion capabilities:
- Builds vocabulary from existing vault tags
- Suggests relevant tags based on content analysis
- Prevents tag fragmentation by matching existing vocabulary
- Prioritizes title-based matches for better accuracy

The TagAnalyzer addresses the tag fragmentation gotcha from the PRP by:
1. Normalizing all tag suggestions to lowercase-hyphenated format
2. Matching against existing vocabulary first (prevent new variations)
3. Using fuzzy matching to find similar existing tags
4. Scoring by content frequency and title relevance
"""

from pathlib import Path
from typing import Dict, List, Set
import re
import frontmatter  # type: ignore[import-untyped]
from loguru import logger


class TagAnalyzer:
    """Analyzes vault content to suggest relevant tags for new notes.

    The TagAnalyzer builds a vocabulary of all existing tags in the vault
    and uses content analysis to suggest the most relevant tags for new content.
    This prevents tag fragmentation by prioritizing existing tags over new ones.

    Attributes:
        vault_path: Path to the Second Brain vault
        tag_vocabulary: Set of all existing tags in the vault

    Example:
        ```python
        analyzer = TagAnalyzer("/path/to/vault")

        # Suggest tags for new content
        tags = analyzer.suggest_tags(
            content="This is about Python programming and machine learning",
            title="Python ML Tutorial",
            max_tags=5
        )
        # Returns: ['python', 'machine-learning', 'tutorial', ...]
        ```
    """

    def __init__(self, vault_path: str):
        """Initialize the TagAnalyzer and build vocabulary.

        Args:
            vault_path: Path to the Second Brain vault directory

        Note:
            The vocabulary is built immediately on initialization by
            scanning all markdown files in the vault. For large vaults,
            this may take a few seconds.
        """
        self.vault_path = Path(vault_path)
        self.tag_vocabulary = self._build_vocabulary()
        logger.info(
            f"TagAnalyzer initialized with {len(self.tag_vocabulary)} tags "
            f"from vault: {vault_path}"
        )

    def _build_vocabulary(self) -> Set[str]:
        """Extract all existing tags from vault markdown files.

        Scans all .md files in the vault and extracts tags from frontmatter.
        This builds the vocabulary used for tag suggestions.

        Returns:
            Set of all unique tags found in the vault

        Note:
            - Skips files with parsing errors (logs warning)
            - Only includes tags from valid frontmatter
            - Tags are already normalized in the vault (from VaultManager)
        """
        tags = set()
        md_files_count = 0
        error_count = 0

        for md_file in self.vault_path.rglob("*.md"):
            md_files_count += 1
            try:
                post = frontmatter.load(md_file)
                if 'tags' in post.metadata and isinstance(post.metadata['tags'], list):
                    for tag in post.metadata['tags']:
                        if isinstance(tag, str):
                            tags.add(tag)
            except Exception as e:
                error_count += 1
                logger.warning(f"Error parsing {md_file}: {e}")
                continue

        logger.debug(
            f"Built vocabulary from {md_files_count} files "
            f"({error_count} errors), found {len(tags)} unique tags"
        )
        return tags

    def _tokenize_content(self, content: str) -> List[str]:
        """Tokenize content into words for matching.

        Converts content to lowercase and splits into words, removing
        common punctuation and special characters.

        Args:
            content: Text content to tokenize

        Returns:
            List of lowercase words from the content

        Example:
            >>> analyzer._tokenize_content("Python, ML & AI!")
            ['python', 'ml', 'ai']
        """
        # Convert to lowercase
        text = content.lower()

        # Remove special characters except hyphens and spaces
        text = re.sub(r'[^\w\s-]', ' ', text)

        # Split on whitespace
        words = text.split()

        # Remove empty strings
        return [w for w in words if w]

    def _score_tag_match(
        self,
        tag: str,
        content_words: List[str],
        title_normalized: str
    ) -> int:
        """Score how well a tag matches the content and title.

        Scoring logic:
        - Title exact match: +10 points
        - Title contains tag: +5 points
        - Tag contains title word: +3 points
        - Content word exact match: +1 point per match
        - Content word partial match: +0.5 points per match

        Args:
            tag: Tag to score
            content_words: Tokenized content words
            title_normalized: Normalized title (lowercase-hyphenated)

        Returns:
            Integer score (higher = better match)
        """
        score: float = 0.0
        tag_parts = tag.split('-')

        # Title-based scoring (highest priority)
        if tag == title_normalized:
            score += 10  # Exact title match
        elif tag in title_normalized or title_normalized in tag:
            score += 5  # Title contains tag or vice versa
        else:
            # Check if tag parts match title words
            title_words = title_normalized.split('-')
            for tag_part in tag_parts:
                if tag_part in title_words:
                    score += 3

        # Content-based scoring
        for word in content_words:
            # Exact word match
            if word == tag or word in tag_parts:
                score += 1
            # Partial match (tag contains word or vice versa)
            elif word in tag or any(word in part for part in tag_parts):
                score += 0.5

        return int(score)

    def suggest_tags(
        self,
        content: str,
        title: str,
        max_tags: int = 5
    ) -> List[str]:
        """Suggest relevant tags based on content and title analysis.

        This is the primary method for tag suggestion. It:
        1. Tokenizes the content into words
        2. Normalizes the title to match tag format
        3. Scores all vocabulary tags against content and title
        4. Returns the top N highest-scoring tags

        Args:
            content: Note content (markdown text)
            title: Note title
            max_tags: Maximum number of tags to suggest (default: 5)

        Returns:
            List of suggested tags, ordered by relevance (best first)

        Example:
            >>> analyzer = TagAnalyzer("/vault")
            >>> tags = analyzer.suggest_tags(
            ...     content="This tutorial covers Python basics",
            ...     title="Python Tutorial",
            ...     max_tags=3
            ... )
            >>> print(tags)
            ['python', 'tutorial', 'programming']

        Note:
            - Only suggests tags from existing vocabulary (prevents fragmentation)
            - Returns empty list if no matching tags found
            - Title matches are weighted higher than content matches
            - More frequent content matches score higher
        """
        if not self.tag_vocabulary:
            logger.warning("Tag vocabulary is empty, cannot suggest tags")
            return []

        # Tokenize content
        content_words = self._tokenize_content(content)

        # Normalize title to match tag format
        title_normalized = title.lower().replace(" ", "-")
        title_normalized = re.sub(r'[^a-z0-9-]', '', title_normalized)
        title_normalized = re.sub(r'-+', '-', title_normalized).strip('-')

        # Score all vocabulary tags
        tag_scores = {}
        for tag in self.tag_vocabulary:
            score = self._score_tag_match(tag, content_words, title_normalized)
            if score > 0:  # Only include tags with positive score
                tag_scores[tag] = score

        # Sort by score (descending) and return top N
        sorted_tags = sorted(tag_scores.items(), key=lambda x: x[1], reverse=True)
        suggested_tags = [tag for tag, score in sorted_tags[:max_tags]]

        logger.debug(
            f"Suggested {len(suggested_tags)} tags for title '{title}': "
            f"{suggested_tags}"
        )

        return suggested_tags

    def refresh_vocabulary(self) -> int:
        """Rebuild the tag vocabulary from vault.

        Useful for updating the vocabulary after new notes have been created.

        Returns:
            Number of tags in the refreshed vocabulary

        Example:
            >>> analyzer = TagAnalyzer("/vault")
            >>> # ... create new notes ...
            >>> new_count = analyzer.refresh_vocabulary()
            >>> print(f"Vocabulary now has {new_count} tags")
        """
        self.tag_vocabulary = self._build_vocabulary()
        logger.info(f"Vocabulary refreshed: {len(self.tag_vocabulary)} tags")
        return len(self.tag_vocabulary)

    def get_vocabulary(self) -> Set[str]:
        """Get the current tag vocabulary.

        Returns:
            Set of all tags in the vocabulary

        Example:
            >>> analyzer = TagAnalyzer("/vault")
            >>> vocab = analyzer.get_vocabulary()
            >>> print(f"Vault has {len(vocab)} unique tags")
        """
        return self.tag_vocabulary.copy()

    def get_vocabulary_stats(self) -> Dict[str, int | float]:
        """Get statistics about the tag vocabulary.

        Returns:
            Dictionary with vocabulary statistics:
                - total_tags: Number of unique tags
                - avg_tag_length: Average tag length in characters
                - multi_word_tags: Number of hyphenated tags

        Example:
            >>> analyzer = TagAnalyzer("/vault")
            >>> stats = analyzer.get_vocabulary_stats()
            >>> print(f"Total tags: {stats['total_tags']}")
        """
        if not self.tag_vocabulary:
            return {
                "total_tags": 0,
                "avg_tag_length": 0,
                "multi_word_tags": 0,
            }

        total_tags = len(self.tag_vocabulary)
        avg_length = sum(len(tag) for tag in self.tag_vocabulary) / total_tags
        multi_word = sum(1 for tag in self.tag_vocabulary if '-' in tag)

        return {
            "total_tags": total_tags,
            "avg_tag_length": round(avg_length, 1),
            "multi_word_tags": multi_word,
        }
