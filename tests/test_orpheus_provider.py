"""Tests for Orpheus provider compilation logic."""

import pytest

try:
    from src.wave_form_provider.providers.orpheus_provider import OrpheusProvider
except ImportError:
    OrpheusProvider = None


@pytest.mark.skipif(OrpheusProvider is None, reason="Orpheus dependencies not installed")
class TestOrpheusCompileText:
    """Test cases for OrpheusProvider.compile_text method."""

    @pytest.fixture
    def provider(self):
        """Create an OrpheusProvider instance for testing."""
        return OrpheusProvider.__new__(OrpheusProvider)

    @pytest.mark.parametrize("input_text,expected", [
        ("Hello [laugh] world", "Hello <laugh> world"),
        ("Hello [chuckle] world", "Hello <chuckle> world"),
        ("[sigh] This is sad", "<sigh> This is sad"),
        ("Hello [laugh]", "Hello <laugh>"),
    ])
    def test_converts_brackets_to_angle(self, provider, input_text, expected):
        """Test that square brackets are converted to angle brackets."""
        assert provider.compile_text(input_text) == expected

    @pytest.mark.parametrize("input_text,expected", [
        ("Hello (sarcastically) world", "Hello world"),
        ("Hello (angry) world", "Hello world"),
        ("(whispers) Hello", "Hello"),
        ("Hello (fast)", "Hello"),
    ])
    def test_removes_parentheses(self, provider, input_text, expected):
        """Test that parentheses delivery markers are removed."""
        assert provider.compile_text(input_text) == expected

    @pytest.mark.parametrize("input_text,expected", [
        ("Hello [laugh] (angry) world", "Hello <laugh> world"),
        ("[chuckle] This is funny (sarcastically)", "<chuckle> This is funny"),
        ("(excited) Hello [gasp] world", "Hello <gasp> world"),
    ])
    def test_converts_and_removes(self, provider, input_text, expected):
        """Test that actions are converted and delivery is removed."""
        assert provider.compile_text(input_text) == expected

    @pytest.mark.parametrize("input_text", [
        "",
        "Normal text without annotations",
        "Hello world",
    ])
    def test_text_without_annotations(self, provider, input_text):
        """Test that text without annotations passes through unchanged."""
        assert provider.compile_text(input_text) == input_text

    def test_whitespace_cleanup(self, provider):
        """Test that extra whitespace is cleaned up."""
        assert provider.compile_text("Hello  (angry)  [laugh]  world") == "Hello <laugh> world"

    def test_punctuation_handling(self, provider):
        """Test that punctuation is handled correctly."""
        assert provider.compile_text("Hello [laugh] ! World") == "Hello <laugh>! World"

