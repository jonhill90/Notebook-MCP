"""Tests for inbox content routing logic.

This test suite validates the InboxRouter's ability to:
- Detect source types (URL, code, thought) with >90% accuracy
- Suggest appropriate folders based on Second Brain conventions
- Handle edge cases and ambiguous content

The router is critical for inbox automation, so comprehensive testing
ensures high accuracy in production use.
"""

from src.inbox.router import InboxRouter


class TestDetectSourceType:
    """Test source type detection accuracy."""

    def setup_method(self):
        """Initialize router for each test."""
        self.router = InboxRouter()

    def test_detect_url_with_https(self):
        """Should detect HTTPS URLs correctly."""
        content = "Check out this article: https://example.com/article"
        title = "Interesting Article"

        result = self.router.detect_source_type(content, title)

        assert result == "url", "Should detect HTTPS URL"

    def test_detect_url_with_http(self):
        """Should detect HTTP URLs correctly."""
        content = "Legacy site: http://oldsite.com"
        title = "Old Website"

        result = self.router.detect_source_type(content, title)

        assert result == "url", "Should detect HTTP URL"

    def test_detect_url_multiple_links(self):
        """Should detect content with multiple URLs."""
        content = """
        Resources to check:
        - https://example.com/one
        - https://example.com/two
        """
        title = "Resource List"

        result = self.router.detect_source_type(content, title)

        assert result == "url", "Should detect multiple URLs"

    def test_detect_code_with_markdown_block(self):
        """Should detect markdown code blocks."""
        content = """
        ```python
        def hello():
            print("world")
        ```
        """
        title = "Python Function"

        result = self.router.detect_source_type(content, title)

        assert result == "code", "Should detect markdown code block"

    def test_detect_code_with_multiple_blocks(self):
        """Should detect multiple code blocks."""
        content = """
        First example:
        ```javascript
        const x = 1;
        ```

        Second example:
        ```python
        y = 2
        ```
        """
        title = "Code Examples"

        result = self.router.detect_source_type(content, title)

        assert result == "code", "Should detect multiple code blocks"

    def test_detect_code_with_python_def(self):
        """Should detect Python function definitions."""
        content = "def calculate_sum(a, b):\n    return a + b"
        title = "Sum Function"

        result = self.router.detect_source_type(content, title)

        assert result == "code", "Should detect Python def keyword"

    def test_detect_code_with_python_class(self):
        """Should detect Python class definitions."""
        content = "class Calculator:\n    def add(self, x, y):\n        return x + y"
        title = "Calculator Class"

        result = self.router.detect_source_type(content, title)

        assert result == "code", "Should detect Python class keyword"

    def test_detect_code_with_javascript_function(self):
        """Should detect JavaScript function declarations."""
        content = "function greet(name) {\n  console.log('Hello ' + name);\n}"
        title = "Greeting Function"

        result = self.router.detect_source_type(content, title)

        assert result == "code", "Should detect JavaScript function keyword"

    def test_detect_code_with_javascript_const(self):
        """Should detect JavaScript const declarations."""
        content = "const API_KEY = 'abc123';\nconst BASE_URL = 'api.example.com';"
        title = "Config Constants"

        result = self.router.detect_source_type(content, title)

        assert result == "code", "Should detect JavaScript const keyword"

    def test_detect_code_with_import_statement(self):
        """Should detect Python import statements."""
        content = "import numpy as np\nfrom pandas import DataFrame"
        title = "Import Statements"

        result = self.router.detect_source_type(content, title)

        assert result == "code", "Should detect import keyword"

    def test_detect_code_with_async_function(self):
        """Should detect async function declarations."""
        content = "async def fetch_data():\n    response = await http.get(url)\n    return response"
        title = "Async Function"

        result = self.router.detect_source_type(content, title)

        assert result == "code", "Should detect async keyword"

    def test_detect_thought_simple_text(self):
        """Should detect simple thoughts as thought type."""
        content = "Need to research how vector databases work for the new project"
        title = "Research Idea"

        result = self.router.detect_source_type(content, title)

        assert result == "thought", "Should default to thought for simple text"

    def test_detect_thought_with_markdown(self):
        """Should detect markdown text without code as thought."""
        content = """
        # Research Notes

        Need to investigate:
        - Vector databases
        - Embedding models
        - Similarity search
        """
        title = "Research List"

        result = self.router.detect_source_type(content, title)

        assert result == "thought", "Should treat markdown text as thought"

    def test_detect_thought_empty_content(self):
        """Should handle empty content gracefully."""
        content = ""
        title = "Empty Note"

        result = self.router.detect_source_type(content, title)

        assert result == "thought", "Should default to thought for empty content"

    def test_url_priority_over_code(self):
        """URLs should take priority when content has both URL and code."""
        content = """
        Check this Python tutorial: https://docs.python.org/tutorial

        ```python
        def example():
            pass
        ```
        """
        title = "Python Tutorial"

        result = self.router.detect_source_type(content, title)

        assert result == "url", "URL detection should have higher priority than code"


class TestSuggestFolder:
    """Test folder suggestion logic."""

    def setup_method(self):
        """Initialize router for each test."""
        self.router = InboxRouter()

    def test_url_to_resources_for_documentation(self):
        """Documentation URLs should go to Resources."""
        content = "https://docs.anthropic.com/claude/reference"

        result = self.router.suggest_folder(source_type="url", content=content)

        assert result == "05 - Resources/05d - Documents", "Documentation should route to Resources/Documents"

    def test_url_to_resources_for_microsoft_learn(self):
        """Microsoft Learn URLs should go to Resources."""
        content = "https://learn.microsoft.com/azure/functions"

        result = self.router.suggest_folder(source_type="url", content=content)

        assert result == "05 - Resources/05d - Documents", "Microsoft Learn should route to Resources/Documents"

    def test_url_to_resources_for_python_docs(self):
        """Python documentation should go to Resources."""
        content = "https://docs.python.org/3/library/asyncio.html"

        result = self.router.suggest_folder(source_type="url", content=content)

        assert result == "05 - Resources/05d - Documents", "Python docs should route to Resources/Documents"

    def test_url_to_resources_for_mdn(self):
        """MDN documentation should go to Resources."""
        content = "https://developer.mozilla.org/en-US/docs/Web/JavaScript"

        result = self.router.suggest_folder(source_type="url", content=content)

        assert result == "05 - Resources/05d - Documents", "MDN should route to Resources/Documents"

    def test_url_to_resources_for_aws_docs(self):
        """AWS documentation should go to Resources."""
        content = "https://docs.aws.amazon.com/lambda/latest/dg/welcome.html"

        result = self.router.suggest_folder(source_type="url", content=content)

        assert result == "05 - Resources/05d - Documents", "AWS docs should route to Resources/Documents"

    def test_url_to_resources_for_react_docs(self):
        """React documentation should go to Resources."""
        content = "https://reactjs.org/docs/hooks-intro.html"

        result = self.router.suggest_folder(source_type="url", content=content)

        assert result == "05 - Resources/05d - Documents", "React docs should route to Resources/Documents"

    def test_url_to_clippings_for_news(self):
        """News articles should go to Clippings."""
        content = "https://news.ycombinator.com/item?id=12345"

        result = self.router.suggest_folder(source_type="url", content=content)

        assert result == "05 - Resources/05c - Clippings", "News should route to Resources/Clippings"

    def test_url_to_clippings_for_blog(self):
        """Blog posts should go to Clippings."""
        content = "https://someblog.com/interesting-post"

        result = self.router.suggest_folder(source_type="url", content=content)

        assert result == "05 - Resources/05c - Clippings", "Blogs should route to Resources/Clippings"

    def test_url_to_clippings_for_general_website(self):
        """General websites should go to Clippings."""
        content = "https://example.com/random-page"

        result = self.router.suggest_folder(source_type="url", content=content)

        assert result == "05 - Resources/05c - Clippings", "General websites should route to Resources/Clippings"

    def test_code_to_resources(self):
        """Code snippets should go to Resources."""
        content = "def example():\n    pass"

        result = self.router.suggest_folder(source_type="code", content=content)

        assert result == "05 - Resources/05e - Examples", "Code should route to Resources/Examples"

    def test_thought_to_notes(self):
        """Thoughts should go to Notes."""
        content = "Interesting idea about knowledge management"

        result = self.router.suggest_folder(source_type="thought", content=content)

        assert result == "01 - Notes/01a - Atomic", "Thoughts should route to Notes/Atomic"


class TestEndToEndRouting:
    """Test complete routing workflow (detect + suggest)."""

    def setup_method(self):
        """Initialize router for each test."""
        self.router = InboxRouter()

    def test_route_documentation_url(self):
        """Complete workflow for documentation URL."""
        content = "Great reference: https://docs.anthropic.com/claude/docs"
        title = "Claude Documentation"

        # Detect type
        source_type = self.router.detect_source_type(content, title)
        # Suggest folder
        folder = self.router.suggest_folder(source_type, content)

        assert source_type == "url"
        assert folder == "05 - Resources/05d - Documents"

    def test_route_blog_post(self):
        """Complete workflow for blog post."""
        content = "Found this: https://example.blog/interesting-article"
        title = "Blog Post"

        source_type = self.router.detect_source_type(content, title)
        folder = self.router.suggest_folder(source_type, content)

        assert source_type == "url"
        assert folder == "05 - Resources/05c - Clippings"

    def test_route_code_snippet(self):
        """Complete workflow for code snippet."""
        content = "```python\ndef calculate(x, y):\n    return x + y\n```"
        title = "Calculate Function"

        source_type = self.router.detect_source_type(content, title)
        folder = self.router.suggest_folder(source_type, content)

        assert source_type == "code"
        assert folder == "05 - Resources/05e - Examples"

    def test_route_thought(self):
        """Complete workflow for general thought."""
        content = "Need to explore how knowledge graphs could improve research workflow"
        title = "Research Idea"

        source_type = self.router.detect_source_type(content, title)
        folder = self.router.suggest_folder(source_type, content)

        assert source_type == "thought"
        assert folder == "01 - Notes/01a - Atomic"

    def test_accuracy_requirement(self):
        """Verify routing accuracy meets >90% requirement on diverse inputs."""
        test_cases = [
            # (content, title, expected_source, expected_folder)
            ("https://docs.python.org", "Python Docs", "url", "05 - Resources/05d - Documents"),
            ("https://blog.com/post", "Blog", "url", "05 - Resources/05c - Clippings"),
            ("def test(): pass", "Test Func", "code", "05 - Resources/05e - Examples"),
            ("Random thought", "Idea", "thought", "01 - Notes/01a - Atomic"),
            ("Check https://example.com", "Link", "url", "05 - Resources/05c - Clippings"),
            ("```js\nconst x = 1;\n```", "JS Code", "code", "05 - Resources/05e - Examples"),
            ("class MyClass: pass", "Class", "code", "05 - Resources/05e - Examples"),
            ("import pandas", "Import", "code", "05 - Resources/05e - Examples"),
            ("Research vector DBs", "Research", "thought", "01 - Notes/01a - Atomic"),
            ("https://learn.microsoft.com/azure", "Azure Docs", "url", "05 - Resources/05d - Documents"),
        ]

        correct_detections = 0
        total_cases = len(test_cases)

        for content, title, expected_source, expected_folder in test_cases:
            source = self.router.detect_source_type(content, title)
            folder = self.router.suggest_folder(source, content)

            if source == expected_source and folder == expected_folder:
                correct_detections += 1

        accuracy = (correct_detections / total_cases) * 100

        assert accuracy >= 90.0, f"Routing accuracy {accuracy}% below 90% requirement"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def setup_method(self):
        """Initialize router for each test."""
        self.router = InboxRouter()

    def test_whitespace_only_content(self):
        """Should handle whitespace-only content."""
        content = "   \n\n   \t\t   "
        title = "Empty"

        source_type = self.router.detect_source_type(content, title)

        assert source_type == "thought", "Whitespace should default to thought"

    def test_very_long_content(self):
        """Should handle very long content efficiently."""
        content = "https://example.com\n" + ("x" * 100000)
        title = "Long Content"

        source_type = self.router.detect_source_type(content, title)

        assert source_type == "url", "Should detect URL even in long content"

    def test_special_characters_in_content(self):
        """Should handle special characters gracefully."""
        content = "Special chars: @#$%^&*()_+{}|:<>?~`"
        title = "Special"

        source_type = self.router.detect_source_type(content, title)

        assert source_type == "thought", "Special chars should default to thought"

    def test_url_in_code_block(self):
        """URLs inside code blocks should still be detected as URL."""
        content = """
        ```python
        URL = "https://api.example.com"
        ```
        """
        title = "API Config"

        # URL detection has priority over code detection
        source_type = self.router.detect_source_type(content, title)

        assert source_type == "url", "URL should have priority even in code block"

    def test_case_sensitivity_in_code_detection(self):
        """Should detect code keywords regardless of indentation."""
        content = "    def indented_function():\n        pass"
        title = "Indented Code"

        source_type = self.router.detect_source_type(content, title)

        assert source_type == "code", "Should detect indented code"

    def test_unicode_content(self):
        """Should handle Unicode content."""
        content = "研究向量数据库的工作原理"
        title = "Research"

        source_type = self.router.detect_source_type(content, title)

        assert source_type == "thought", "Unicode should default to thought"
