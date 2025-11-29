"""Tests for Inworld provider compilation logic."""

import pytest

try:
    from src.wave_form_provider.providers.inworld_provider import InworldProvider
except ImportError:
    InworldProvider = None


@pytest.mark.skipif(InworldProvider is None, reason="Inworld dependencies not installed")
class TestInworldCompileText:
    """Test cases for InworldProvider.compile_text method."""

    @pytest.fixture
    def provider(self):
        """Create an InworldProvider instance for testing."""
        return InworldProvider.__new__(InworldProvider)

    @pytest.mark.parametrize("input_text,expected", [
        ("", ""),
        ("Normal text without annotations", "Normal text without annotations"),
        ("Hello world", "Hello world"),
        ("Hello (angry) world", "Hello [angry] world"),
        ("Hello [laughter] world", "Hello [laughter] world"),
        ("(excited) Hello!", "[excited] Hello!"),
        ("Hello (sad) and (happy) world", "Hello [sad] and [happy] world"),
        ("Hello [laugh] (whisper) goodbye", "Hello [laugh] [whisper] goodbye"),
    ])
    def test_converts_parentheses_to_brackets(self, provider, input_text, expected):
        """Test that () are converted to [] for Inworld."""
        assert provider.compile_text(input_text) == expected

    @pytest.mark.parametrize("input_text", [
        "[laughter] Hello",
        "Hello [sigh] world",
        "[chuckle]",
    ])
    def test_brackets_stay_unchanged(self, provider, input_text):
        """Test that [] stay unchanged."""
        assert provider.compile_text(input_text) == input_text
