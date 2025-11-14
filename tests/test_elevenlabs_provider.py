"""Tests for ElevenLabs provider compilation logic."""

import pytest
from src.wave_form_provider.providers.elevenlabs_provider import ElevenLabsProvider


class TestElevenLabsCompileText:
    """Test cases for ElevenLabsProvider.compile_text method."""

    @pytest.fixture
    def provider(self):
        """Create an ElevenLabsProvider instance for testing."""
        return ElevenLabsProvider.__new__(ElevenLabsProvider)

    @pytest.mark.parametrize("input_text,expected", [
        ("Hello (sarcastically) world", "Hello [sarcastically] world"),
        ("Hello (whispers) world", "Hello [whispers] world"),
        ("(sarcastically) Hello", "[sarcastically] Hello"),
        ("Hello (sarcastically)", "Hello [sarcastically]"),
    ])
    def test_converts_parentheses_to_brackets(self, provider, input_text, expected):
        """Test that parentheses are converted to brackets."""
        assert provider.compile_text(input_text) == expected

    @pytest.mark.parametrize("input_text,expected", [
        ("Hello [chuckle] world", "Hello [chuckle] world"),
        ("Hello (sarcastically) [chuckle] world", "Hello [sarcastically] [chuckle] world"),
        ("[laughter] (whispers) Hello", "[laughter] [whispers] Hello"),
    ])
    def test_preserves_existing_brackets(self, provider, input_text, expected):
        """Test that existing brackets are preserved."""
        assert provider.compile_text(input_text) == expected

    @pytest.mark.parametrize("input_text", [
        "",
        "Normal text without annotations",
        "Hello world",
    ])
    def test_text_without_annotations(self, provider, input_text):
        """Test that text without annotations passes through unchanged."""
        assert provider.compile_text(input_text) == input_text

