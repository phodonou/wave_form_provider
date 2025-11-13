"""ElevenLabs TTS Provider implementation."""

import os
from typing import Optional
from elevenlabs import ElevenLabs, Voice, VoiceSettings
from .tts_provider import TTSProvider, SynthesisResponse, SynthesisStreamResponse, SynthesisMetadata
from src.util.util import convert_parentheses_to_brackets


class ElevenLabsProvider(TTSProvider):
    """ElevenLabs TTS provider implementation."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize ElevenLabs provider.

        Args:
            api_key: ElevenLabs API key. If not provided, will use ELEVENLABS_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ElevenLabs API key is required. Set ELEVENLABS_API_KEY env var or pass api_key parameter."
            )

        self.client = ElevenLabs(api_key=self.api_key)

    def compile_text(self, text: str) -> str:
        """Convert () style markers to [] format for ElevenLabs."""
        return convert_parentheses_to_brackets(text)

    async def synthesize(
        self,
        voice_id: str,
        text: str,
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: Optional[float] = 0.5,
    ) -> SynthesisResponse:
        """
        Generate speech from text using ElevenLabs API.

        Args:
            voice_id: ElevenLabs voice ID (e.g., "21m00Tcm4TlvDq8ikWAM")
            text: Text to synthesize
            style_guidance: Style guidance for the voice (not directly supported by ElevenLabs)
            seed: Random seed for reproducibility
            creativity: Stability setting (0.0 to 1.0, inverted - higher creativity = lower stability)

        Returns:
            SynthesisResponse containing audio bytes and metadata
        """
        text = self.compile_text(text)
        
        voice_settings = VoiceSettings(
            stability=creativity,
        )

        try:
            audio_bytes = b""
            audio_generator = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                voice_settings=voice_settings,
                model_id="eleven_v3",
            )

            audio_bytes = b"".join(audio_generator)
            
            return SynthesisResponse(
                audio=audio_bytes,
                metadata=SynthesisMetadata(
                    voice_id=voice_id,
                    model="eleven_v3",
                    streaming=False,
                    size_bytes=len(audio_bytes),
                )
            )

        except Exception as e:
            raise RuntimeError(f"ElevenLabs TTS synthesis failed: {str(e)}") from e
    
    async def synthesize_stream(
        self,
        voice_id: str,
        text: str,
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: float = 0.5,
    ) -> SynthesisStreamResponse:
        raise NotImplementedError("Streaming not supported by ElevenLabs provider")
    
    async def list_voices(self) -> list[str]:
        raise NotImplementedError("Voice listing not supported by ElevenLabs provider")
    
    async def clone_voice(self, voice_id: str) -> str:
        raise NotImplementedError("Voice cloning not supported by ElevenLabs provider")
