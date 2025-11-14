"""Tests for Google Gemini provider compilation logic."""

import pytest

try:
    from src.wave_form_provider.providers.google_gemini_provider import GoogleGeminiProvider
except ImportError:
    GoogleGeminiProvider = None


@pytest.mark.skipif(GoogleGeminiProvider is None, reason="Google Gemini dependencies not installed")
class TestGoogleGeminiCompileText:
    """Test cases for GoogleGeminiProvider.compile_text method."""

    @pytest.fixture
    def provider(self):
        """Create a GoogleGeminiProvider instance for testing."""
        return GoogleGeminiProvider.__new__(GoogleGeminiProvider)

    @pytest.mark.parametrize("input_text,expected", [
        ("Hello (sarcastically) world", "Hello [sarcastically] world"),
        ("Hello (whispers) world", "Hello [whispers] world"),
        ("(sarcastically) Hello", "[sarcastically] Hello"),
        ("Hello (sarcastically)", "Hello [sarcastically]"),
    ])
    def test_converts_parentheses_to_brackets(self, provider, input_text, expected):
        """Test that parentheses are converted to brackets (same as ElevenLabs)."""
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

