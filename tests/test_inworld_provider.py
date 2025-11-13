"""Tests for Inworld provider compilation logic."""

import pytest

try:
    from src.providers.inworld_provider import InworldProvider
except ImportError:
    InworldProvider = None


@pytest.mark.skipif(InworldProvider is None, reason="Inworld dependencies not installed")
class TestInworldCompileText:
    """Test cases for InworldProvider.compile_text method."""

    @pytest.fixture
    def provider(self):
        """Create an InworldProvider instance for testing."""
        return InworldProvider.__new__(InworldProvider)

    @pytest.mark.parametrize("input_text", [
        "",
        "Normal text without annotations",
        "Hello world",
        "Hello (angry) world",
        "Hello [laughter] world",
    ])
    def test_text_passes_through(self, provider, input_text):
        """Test that text passes through unchanged."""
        assert provider.compile_text(input_text) == input_text


@pytest.mark.skipif(InworldProvider is None, reason="Inworld dependencies not installed")
class TestInworldParseToSegments:
    """Test cases for InworldProvider._parse_to_segments method."""

    @pytest.fixture
    def provider(self):
        """Create an InworldProvider instance for testing."""
        provider = InworldProvider.__new__(InworldProvider)
        provider.speed_map = {
            "slow": 0.7,
            "normal": 1.0,
            "fast": 1.3,
            "really fast": 1.5,
        }
        return provider

    def test_splits_on_emotion_changes(self, provider):
        """Test that segments split on emotion changes."""
        text = "Hello (angry) I'm mad! (sad) Now I'm sad."
        segments = provider._parse_to_segments(text)
        assert len(segments) == 3
        assert segments[0]['text'] == "Hello"
        assert segments[0].get('emotion') is None
        assert segments[1]['text'] == "I'm mad!"
        assert segments[1]['emotion'] == "angry"
        assert segments[2]['text'] == "Now I'm sad."
        assert segments[2]['emotion'] == "sad"

    def test_splits_on_speed_changes(self, provider):
        """Test that segments split on speed changes."""
        text = "(fast) Hello (slow) Goodbye"
        segments = provider._parse_to_segments(text)
        assert len(segments) == 2
        assert segments[0]['text'] == "Hello"
        assert segments[0]['speed'] == 1.3
        assert segments[1]['text'] == "Goodbye"
        assert segments[1]['speed'] == 0.7

    def test_actions_stay_in_text(self, provider):
        """Test that actions stay in text."""
        text = "Hello [laughter] world [sigh]"
        segments = provider._parse_to_segments(text)
        assert len(segments) == 1
        assert "[laughter]" in segments[0]['text']
        assert "[sigh]" in segments[0]['text']

    def test_emotion_with_actions(self, provider):
        """Test that emotions split but actions stay."""
        text = "Hello [laughter] (angry) I'm mad! [sigh]"
        segments = provider._parse_to_segments(text)
        assert len(segments) == 2
        assert segments[0]['text'] == "Hello [laughter]"
        assert segments[1]['text'] == "I'm mad! [sigh]"
        assert segments[1]['emotion'] == "angry"

    def test_emotion_does_not_persist(self, provider):
        """Test that emotion doesn't carry to next segment."""
        text = "(angry) First (fast) Second"
        segments = provider._parse_to_segments(text)
        assert len(segments) == 2
        assert segments[0]['emotion'] == "angry"
        assert segments[0].get('speed') is None
        assert segments[1].get('emotion') is None
        assert segments[1]['speed'] == 1.3

    def test_speed_does_not_persist(self, provider):
        """Test that speed doesn't carry to next segment."""
        text = "(fast) First (sad) Second"
        segments = provider._parse_to_segments(text)
        assert len(segments) == 2
        assert segments[0]['speed'] == 1.3
        assert segments[0].get('emotion') is None
        assert segments[1].get('speed') is None
        assert segments[1]['emotion'] == "sad"

    def test_realistic_sentence(self, provider):
        """Test realistic sentence with multiple features."""
        text = "Hello there! [laughter] (excited) I got the job! (fast) Let me tell you more."
        segments = provider._parse_to_segments(text)
        assert len(segments) == 3
        assert segments[0]['text'] == "Hello there! [laughter]"
        assert segments[0].get('emotion') is None
        assert segments[1]['text'] == "I got the job!"
        assert segments[1]['emotion'] == "excited"
        assert segments[2]['text'] == "Let me tell you more."
        assert segments[2]['speed'] == 1.3

    def test_text_without_annotations(self, provider):
        """Test text without annotations creates single segment."""
        text = "Hello world"
        segments = provider._parse_to_segments(text)
        assert len(segments) == 1
        assert segments[0]['text'] == "Hello world"
        assert segments[0].get('emotion') is None
        assert segments[0].get('speed') is None

    def test_full_flow_compile_then_parse(self, provider):
        """Test full flow: compile_text then _parse_to_segments."""
        original_text = "Hello [laughter] (excited) I got the job!"
        compiled = provider.compile_text(original_text)
        assert compiled == original_text
        
        segments = provider._parse_to_segments(compiled)
        assert len(segments) == 2
        assert "[laughter]" in segments[0]['text']
        assert segments[1]['emotion'] == "excited"

