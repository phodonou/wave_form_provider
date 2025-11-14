"""Tests for utility functions."""

import pytest
from src.wave_form_provider.util.util import remove_ssml, convert_parentheses_to_brackets


class TestRemoveSSML:
    """Test cases for remove_ssml function."""

    @pytest.mark.parametrize("input_text,expected", [
        ("Hello! [laughter] This is a test", "Hello! This is a test"),
        ("Well [sigh] I guess [pause] that works", "Well I guess that works"),
        ("Hello [laugh][sigh][pause] world", "Hello world"),
        ("Hello [ long pause ] world", "Hello world"),
    ])
    def test_removes_annotations(self, input_text, expected):
        """Test that SSML annotations are removed correctly."""
        assert remove_ssml(input_text) == expected

    @pytest.mark.parametrize("input_text,expected", [
        ("[whisper]Can you hear me? ", "Can you hear me?"),
        ("Hello [laugh]", "Hello"),
        ("[laugh][sigh][pause]", ""),
    ])
    def test_annotations_at_edges(self, input_text, expected):
        """Test annotations at start/end of text."""
        assert remove_ssml(input_text) == expected

    @pytest.mark.parametrize("input_text,expected", [
        ("Hello [laugh]! How are you?", "Hello! How are you?"),
        ("Hello! [sigh] How are you?", "Hello! How are you?"),
        ("Hello! [sigh], how are you?", "Hello!, how are you?"),
    ])
    def test_punctuation_handling(self, input_text, expected):
        """Test that punctuation is handled correctly around annotations."""
        assert remove_ssml(input_text) == expected

    @pytest.mark.parametrize("input_text,expected", [
        ("  [laugh]  Hello  [pause]  world  ", "Hello world"),
        ("This is normal text", "This is normal text"),
        ("", ""),
        ("   ", ""),
    ])
    def test_whitespace_normalization(self, input_text, expected):
        """Test that whitespace is normalized correctly."""
        assert remove_ssml(input_text) == expected

    def test_special_characters_in_annotation(self):
        """Test annotations with special characters."""
        assert remove_ssml("Test [emoji: 😂] text") == "Test text"

    def test_nested_brackets(self):
        """Test that nested brackets are handled (current behavior)."""
        result = remove_ssml("Hello [outer [inner] text] world")
        assert "Hello" in result and "world" in result
        assert "[outer" not in result and "[inner" not in result


class TestConvertParenthesesToBrackets:
    """Test cases for convert_parentheses_to_brackets function."""

    @pytest.mark.parametrize("input_text,expected", [
        ("Hello (sarcastically) world", "Hello [sarcastically] world"),
        ("(whispers) Can you hear me?", "[whispers] Can you hear me?"),
        ("Hello [chuckle] (sigh) world", "Hello [chuckle] [sigh] world"),
        ("(sarcastically) Not the kind... [chuckle] but", "[sarcastically] Not the kind... [chuckle] but"),
        ("Normal text", "Normal text"),
    ])
    def test_converts_parentheses_to_brackets(self, input_text, expected):
        """Test that parentheses are converted to brackets."""
        assert convert_parentheses_to_brackets(input_text) == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
