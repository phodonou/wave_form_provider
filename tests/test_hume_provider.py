"""Tests for Hume provider compilation logic."""

import pytest

try:
    from src.wave_form_provider.providers.hume_provider import HumeProvider
except ImportError:
    HumeProvider = None


@pytest.mark.skipif(HumeProvider is None, reason="Hume dependencies not installed")
class TestHumeCompileText:
    """Test cases for HumeProvider.compile_text method."""

    @pytest.fixture
    def provider(self):
        """Create a HumeProvider instance for testing."""
        provider = HumeProvider.__new__(HumeProvider)
        provider.speed_map = {
            "slow": 0.6,
            "normal": 1.0,
            "fast": 1.5,
            "really fast": 2.0,
        }
        return provider

    @pytest.mark.parametrize("input_text", [
        "",
        "Normal text without annotations",
        "Hello world",
        "Hello (angry) world",
        "Hello [laughter] world",
        "Hello [pause] world",
    ])
    def test_text_passes_through(self, provider, input_text):
        """Test that text passes through unchanged."""
        assert provider.compile_text(input_text) == input_text


@pytest.mark.skipif(HumeProvider is None, reason="Hume dependencies not installed")
class TestHumeParseToUtterances:
    """Test cases for HumeProvider._parse_to_utterances method."""

    @pytest.fixture
    def provider(self):
        """Create a HumeProvider instance for testing."""
        provider = HumeProvider.__new__(HumeProvider)
        provider.speed_map = {
            "slow": 0.6,
            "normal": 1.0,
            "fast": 1.5,
            "really fast": 2.0,
        }
        return provider

    def test_splits_on_emotion_changes(self, provider):
        """Test that utterances split on emotion changes."""
        text = "Hello (angry) I'm mad! (sad) Now I'm sad."
        utterances = provider._parse_to_utterances(text)
        assert len(utterances) == 3
        assert utterances[0]['text'] == "Hello"
        assert utterances[1]['text'] == "I'm mad!"
        assert utterances[1]['description'] == "angry"
        assert utterances[2]['text'] == "Now I'm sad."
        assert utterances[2]['description'] == "sad"

    def test_splits_on_speed_changes(self, provider):
        """Test that utterances split on speed changes."""
        text = "(fast) Hello (slow) Goodbye"
        utterances = provider._parse_to_utterances(text)
        assert len(utterances) == 2
        assert utterances[0]['text'] == "Hello"
        assert utterances[0]['speed'] == 1.5
        assert utterances[1]['text'] == "Goodbye"
        assert utterances[1]['speed'] == 0.6

    def test_actions_split_and_apply_to_previous(self, provider):
        """Test that actions trigger splits and apply to text before them."""
        text = "Hello [laughter] world [sigh]"
        utterances = provider._parse_to_utterances(text)
        assert len(utterances) == 2
        assert utterances[0]['text'] == "Hello"
        assert utterances[0]['description'] == "laughter"
        assert utterances[1]['text'] == "world"
        assert utterances[1]['description'] == "sigh"

    def test_emotion_then_action(self, provider):
        """Test emotion followed by action - action applies to text before it."""
        text = "Hello (angry) I'm mad! [laughter]"
        utterances = provider._parse_to_utterances(text)
        assert len(utterances) == 2
        assert utterances[0]['text'] == "Hello"
        assert utterances[1]['text'] == "I'm mad!"
        assert utterances[1]['description'] == "angry, laughter"

    def test_pause_in_middle_stays_in_text(self, provider):
        """Test that [pause] in middle stays in text."""
        text = "Hello [pause] world"
        utterances = provider._parse_to_utterances(text)
        assert len(utterances) == 1
        assert "[pause]" in utterances[0]['text']
        assert 'trailing_silence' not in utterances[0]
    
    def test_pause_at_end_becomes_trailing_silence(self, provider):
        """Test that [pause] at end becomes trailing_silence."""
        text = "Hello world. [pause]"
        utterances = provider._parse_to_utterances(text)
        assert len(utterances) == 1
        assert utterances[0]['text'] == "Hello world."
        assert utterances[0]['trailing_silence'] == 2
    
    def test_long_pause_at_end_becomes_trailing_silence(self, provider):
        """Test that [long pause] at end becomes trailing_silence."""
        text = "Hello world. [long pause]"
        utterances = provider._parse_to_utterances(text)
        assert len(utterances) == 1
        assert utterances[0]['text'] == "Hello world."
        assert utterances[0]['trailing_silence'] == 4

    def test_realistic_sentence(self, provider):
        """Test realistic sentence with multiple features."""
        text = "Hey there! [laughter] This is amazing! (happy) I'm glad."
        utterances = provider._parse_to_utterances(text)
        assert len(utterances) == 3
        assert utterances[0]['text'] == "Hey there!"
        assert utterances[0]['description'] == "laughter"
        assert utterances[1]['text'] == "This is amazing!"
        assert utterances[1]['description'] is None
        assert utterances[2]['text'] == "I'm glad."
        assert utterances[2]['description'] == "happy"

    def test_text_without_annotations(self, provider):
        """Test text without annotations creates single utterance."""
        text = "Hello world"
        utterances = provider._parse_to_utterances(text)
        assert len(utterances) == 1
        assert utterances[0]['text'] == "Hello world"
        assert utterances[0]['description'] is None
        assert utterances[0]['speed'] is None

    def test_full_flow_compile_then_parse(self, provider):
        """Test full flow: compile_text then _parse_to_utterances."""
        original_text = "Hey there! [laughter] This is amazing! (happy) I'm glad."
        compiled = provider.compile_text(original_text)
        assert compiled == original_text
        
        utterances = provider._parse_to_utterances(compiled)
        assert len(utterances) == 3
        assert utterances[0]['text'] == "Hey there!"
        assert utterances[0]['description'] == "laughter"
        assert utterances[1]['text'] == "This is amazing!"
        assert utterances[2]['text'] == "I'm glad."
        assert utterances[2]['description'] == "happy"

    def test_speed_and_emotion_together(self, provider):
        """Test speed persists across emotion changes."""
        text = "(fast) Hello (angry) I'm mad!"
        utterances = provider._parse_to_utterances(text)
        assert len(utterances) == 2
        assert utterances[0]['text'] == "Hello"
        assert utterances[0]['speed'] == 1.5
        assert utterances[1]['text'] == "I'm mad!"
        assert utterances[1]['speed'] == 1.5
        assert utterances[1]['description'] == "angry"

