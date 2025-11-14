"""Tests for OpenAI provider compilation logic."""

import pytest
from src.wave_form_provider.providers.openai_provider import OpenAIProvider


class TestOpenAICompileText:
    """Test cases for OpenAIProvider.compile_text method."""

    @pytest.fixture
    def provider(self):
        """Create an OpenAIProvider instance for testing."""
        return OpenAIProvider.__new__(OpenAIProvider)

    @pytest.mark.parametrize("input_text,expected", [
        ("Hello [laughter] world", "Hello world"),
        ("Hello [sigh] world", "Hello world"),
        ("Hello [chuckle] world", "Hello world"),
        ("[laughter] Hello", "Hello"),
        ("Hello [laughter]", "Hello"),
        ("[laughter][sigh][pause]", ""),
    ])
    def test_removes_brackets(self, provider, input_text, expected):
        """Test that bracket annotations are removed."""
        assert provider.compile_text(input_text) == expected

    @pytest.mark.parametrize("input_text,expected", [
        ("Hello (sarcastically) world", "Hello world"),
        ("Hello (whispers) world", "Hello world"),
        ("(sarcastically) Hello", "Hello"),
        ("Hello (sarcastically)", "Hello"),
    ])
    def test_removes_parentheses(self, provider, input_text, expected):
        """Test that parentheses markers are removed."""
        assert provider.compile_text(input_text) == expected

    @pytest.mark.parametrize("input_text,expected", [
        ("Hello [chuckle] (whispers) world", "Hello world"),
        ("[laughter] Hello (sarcastically) world", "Hello world"),
        ("(sarcastically) [laughter] Hello", "Hello"),
    ])
    def test_removes_both(self, provider, input_text, expected):
        """Test that both brackets and parentheses are removed."""
        assert provider.compile_text(input_text) == expected

    @pytest.mark.parametrize("input_text", [
        "",
        "Normal text without annotations",
        "Hello world",
    ])
    def test_text_without_annotations(self, provider, input_text):
        """Test that text without annotations passes through unchanged."""
        assert provider.compile_text(input_text) == input_text

