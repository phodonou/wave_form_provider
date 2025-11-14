"""Tests for Cartesia provider compilation logic."""

import pytest
from src.wave_form_provider.providers.cartesia_provider import CartesiaProvider


class TestCartesiaCompileText:
    """Test cases for CartesiaProvider.compile_text method."""

    @pytest.fixture
    def provider(self):
        """Create a CartesiaProvider instance for testing."""
        provider = CartesiaProvider.__new__(CartesiaProvider)
        provider.speed_map = {
            "slow": 0.6,
            "normal": 1.0,
            "fast": 1.3,
            "really fast": 1.5,
        }
        provider.volume_map = {
            "quiet": 0.5,
            "normal": 1.0,
            "loud": 1.5,
            "shout": 2.0,
        }
        provider.pause_map = {
            "short pause": "0.5s",
            "pause": "1s",
            "long pause": "2s",
        }
        return provider

    @pytest.mark.parametrize("input_text,expected", [
        ("(slow) Hello", '<speed ratio="0.6"/> Hello'),
        ("(normal) Hello", '<speed ratio="1.0"/> Hello'),
        ("(fast) Hello", '<speed ratio="1.3"/> Hello'),
        ("(really fast) Hello", '<speed ratio="1.5"/> Hello'),
        ("(FAST) Hello", '<speed ratio="1.3"/> Hello'),  # Case insensitive
        ("(Fast) Hello", '<speed ratio="1.3"/> Hello'),
    ])
    def test_speed_commands(self, provider, input_text, expected):
        """Test that speed commands are converted to speed tags."""
        assert provider.compile_text(input_text) == expected

    @pytest.mark.parametrize("input_text,expected", [
        ("(quiet) Hello", '<volume ratio="0.5"/> Hello'),
        ("(loud) Hello", '<volume ratio="1.5"/> Hello'),
        ("(shout) Hello", '<volume ratio="2.0"/> Hello'),
        ("(SHOUT) Hello", '<volume ratio="2.0"/> Hello'),  # Case insensitive
    ])
    def test_volume_commands(self, provider, input_text, expected):
        """Test that volume commands are converted to volume tags."""
        assert provider.compile_text(input_text) == expected

    @pytest.mark.parametrize("input_text,expected", [
        ("(short pause) Hello", '<break time="0.5s"/> Hello'),
        ("(pause) Hello", '<break time="1s"/> Hello'),
        ("(long pause) Hello", '<break time="2s"/> Hello'),
        ("(PAUSE) Hello", '<break time="1s"/> Hello'),  # Case insensitive
    ])
    def test_pause_commands(self, provider, input_text, expected):
        """Test that pause commands are converted to break tags."""
        assert provider.compile_text(input_text) == expected

    @pytest.mark.parametrize("input_text,expected", [
        ("My name is (spell) Bob", 'My name is <spell>Bob</spell>'),
        ("My name is (spell)Bob", 'My name is <spell>Bob</spell>'),
        ("My account is (spell) ABC-123", 'My account is <spell>ABC-123</spell>'),
        ("My phone is (spell)(123) 456-7890", 'My phone is <spell>(123)</spell> 456-7890'),
        ("My card is (spell)1234-5678-9012-3456", 'My card is <spell>1234-5678-9012-3456</spell>'),
        ("(spell)Bob, spelled (spell)Bob", '<spell>Bob</spell>, spelled <spell>Bob</spell>'),
        ("(spell)Bob. Next (spell)ABC", '<spell>Bob</spell>. Next <spell>ABC</spell>'),
        ("(SPELL)Bob", '<spell>Bob</spell>'),  # Case insensitive
    ])
    def test_spell_markers(self, provider, input_text, expected):
        """Test that spell markers are converted to spell tags."""
        assert provider.compile_text(input_text) == expected

    @pytest.mark.parametrize("input_text,expected", [
        ("(spell) ", "(spell) "),  # No word, left as-is
        ("(spell)", "(spell)"),  # Standalone, left as-is
    ])
    def test_spell_markers_no_word(self, provider, input_text, expected):
        """Test that spell markers with no word are left as-is."""
        assert provider.compile_text(input_text) == expected

    @pytest.mark.parametrize("input_text,expected", [
        ("Hello (angry) world", 'Hello <emotion value="angry" /> world'),
        ("(sad) I am sad", '<emotion value="sad" /> I am sad'),
        ("(happy) I am happy!", '<emotion value="happy" /> I am happy!'),
        ("(SAD) I am sad", '<emotion value="SAD" /> I am sad'),  # Preserves case
    ])
    def test_emotion_markers(self, provider, input_text, expected):
        """Test that emotion markers are converted to emotion tags."""
        assert provider.compile_text(input_text) == expected

    def test_emotion_inside_spell_tag(self, provider):
        """Test that emotions inside spell tags are not processed."""
        input_text = "My phone is (spell)(123) 456-7890"
        result = provider.compile_text(input_text)
        # Should have <spell>(123)</spell>, not <spell><emotion value="123" /></spell>
        assert '<spell>(123)</spell>' in result
        assert '<emotion value="123" />' not in result

    @pytest.mark.parametrize("input_text,expected", [
        ("[laughter] Hello", "[laughter] Hello"),
        ("[sigh] Hello", "[sigh] Hello"),
        ("[chuckle] Hello", "[chuckle] Hello"),
        ("Hello [laughter] world", "Hello [laughter] world"),
    ])
    def test_action_markers_pass_through(self, provider, input_text, expected):
        """Test that action markers are passed through unchanged."""
        assert provider.compile_text(input_text) == expected

    @pytest.mark.parametrize("input_text,expected", [
        ("<speed ratio=\"1.5\"/> Hello", '<speed ratio="1.5"/> Hello'),
        ("<volume ratio=\"2.0\"/> Hello", '<volume ratio="2.0"/> Hello'),
        ("<break time=\"1s\"/> Hello", '<break time="1s"/> Hello'),
    ])
    def test_provider_specific_tags_pass_through(self, provider, input_text, expected):
        """Test that provider-specific tags are passed through unchanged."""
        assert provider.compile_text(input_text) == expected

    def test_combined_commands(self, provider):
        """Test multiple commands in one text."""
        input_text = "(fast) I speak quickly. (pause) Then (angry) I get mad! [laughter]"
        result = provider.compile_text(input_text)
        assert '<speed ratio="1.3"/>' in result
        assert '<break time="1s"/>' in result
        assert '<emotion value="angry" />' in result
        assert "[laughter]" in result

    def test_spell_and_emotion_combined(self, provider):
        """Test spell and emotion markers together."""
        input_text = "(spell)Bob and (angry) I am mad"
        result = provider.compile_text(input_text)
        assert '<spell>Bob</spell>' in result
        assert '<emotion value="angry" />' in result

    @pytest.mark.parametrize("input_text", [
        "",
        "Normal text without annotations",
        "Hello world",
    ])
    def test_text_without_annotations(self, provider, input_text):
        """Test that text without annotations passes through unchanged."""
        assert provider.compile_text(input_text) == input_text

    def test_multiple_speed_commands(self, provider):
        """Test multiple speed commands in sequence."""
        input_text = "(slow) First (fast) Second"
        result = provider.compile_text(input_text)
        assert '<speed ratio="0.6"/>' in result
        assert '<speed ratio="1.3"/>' in result

    def test_multiple_emotions(self, provider):
        """Test multiple emotion markers."""
        input_text = "(happy) Hello (sad) Goodbye"
        result = provider.compile_text(input_text)
        assert '<emotion value="happy" />' in result
        assert '<emotion value="sad" />' in result

