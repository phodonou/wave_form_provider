"""ElevenLabs TTS Provider implementation."""

import io
import os
import wave
import base64
from typing import Optional, List
from elevenlabs import ElevenLabs, Voice, VoiceSettings
from .tts_provider import TTSProvider, SynthesisResponse, SynthesisStreamResponse, SynthesisMetadata, DialogueLine, SynthesisWithTimestampsResponse, Alignment, VoiceSegment
from ..util.util import convert_parentheses_to_brackets

SAMPLE_RATE = 24000
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

    def _wrap_pcm_as_wav(self, pcm_data: bytes, sample_rate: int = SAMPLE_RATE, num_channels: int = 1, sample_width: int = 2) -> bytes:
        """Wrap raw PCM data with a WAV header."""
        output_buffer = io.BytesIO()
        with wave.open(output_buffer, 'wb') as wav_out:
            wav_out.setnchannels(num_channels)
            wav_out.setsampwidth(sample_width)
            wav_out.setframerate(sample_rate)
            wav_out.writeframes(pcm_data)
        return output_buffer.getvalue()

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
            audio_generator = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                voice_settings=voice_settings,
                model_id="eleven_v3",
                output_format=f"pcm_{SAMPLE_RATE}",
            )

            pcm_data = b"".join(audio_generator)
            audio_bytes = self._wrap_pcm_as_wav(pcm_data, SAMPLE_RATE)
            
            return SynthesisResponse(
                audio=audio_bytes,
                metadata=SynthesisMetadata(
                    voice_id=voice_id,
                    model="eleven_v3",
                    audio_format="wav",
                    streaming=False,
                    size_bytes=len(audio_bytes),
                    sample_rate=SAMPLE_RATE,
                )
            )

        except Exception as e:
            raise RuntimeError(f"ElevenLabs TTS synthesis failed: {str(e)}") from e
    
    async def synthesize_dialogue(
        self,
        dialogue_lines: List[DialogueLine],
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: float = 0.5,
    ) -> SynthesisResponse:
        """
        Generate speech from dialogue lines using ElevenLabs dialogue API.

        Args:
            dialogue_lines: List of DialogueLine objects containing text and voice_id
            style_guidance: Style guidance for the voice (not directly supported by ElevenLabs)
            seed: Random seed for reproducibility
            creativity: Stability setting (0.0 to 1.0, inverted - higher creativity = lower stability)

        Returns:
            SynthesisResponse containing audio bytes and metadata
        """
        inputs = []
        for line in dialogue_lines:
            compiled_text = self.compile_text(line.text)
            inputs.append({
                "text": compiled_text,
                "voice_id": line.voice_id
            })
        
        try:
            audio_generator = self.client.text_to_dialogue.convert(
                inputs=inputs,
                output_format=f"pcm_{SAMPLE_RATE}",
            )

            pcm_data = b"".join(audio_generator)
            audio_bytes = self._wrap_pcm_as_wav(pcm_data, SAMPLE_RATE)
            
            voice_id = dialogue_lines[0].voice_id if dialogue_lines else "unknown"
            
            return SynthesisResponse(
                audio=audio_bytes,
                metadata=SynthesisMetadata(
                    voice_id=voice_id,
                    model="eleven_v3",
                    audio_format="wav",
                    streaming=False,
                    size_bytes=len(audio_bytes),
                    sample_rate=SAMPLE_RATE,
                )
            )

        except Exception as e:
            raise RuntimeError(f"ElevenLabs dialogue synthesis failed: {str(e)}") from e
        
    
    async def synthesize_stream(
        self,
        voice_id: str,
        text: str,
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: float = 0.5,
    ) -> SynthesisStreamResponse:
        raise NotImplementedError("Streaming not supported by ElevenLabs provider")

    async def synthesize_with_timestamps(
        self,
        voice_id: str,
        text: str,
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: Optional[float] = 0.5,
    ) -> SynthesisWithTimestampsResponse:
        text = self.compile_text(text)
        
        voice_settings = VoiceSettings(
            stability=creativity,
        )

        try:
            response = self.client.text_to_speech.convert_with_timestamps(
                voice_id=voice_id,
                text=text,
                voice_settings=voice_settings,
                model_id="eleven_v3",
                output_format=f"pcm_{SAMPLE_RATE}",
            )

            pcm_data = base64.b64decode(response.audio_base_64)
            audio_bytes = self._wrap_pcm_as_wav(pcm_data, SAMPLE_RATE)
            
            alignment = Alignment(**response.alignment.model_dump())
            normalized_alignment = Alignment(**response.normalized_alignment.model_dump())
            
            return SynthesisWithTimestampsResponse(
                audio=audio_bytes,
                metadata=SynthesisMetadata(
                    voice_id=voice_id,
                    model="eleven_v3",
                    audio_format="wav",
                    streaming=False,
                    size_bytes=len(audio_bytes),
                    sample_rate=SAMPLE_RATE,
                ),
                voice_segments=None,
                alignment=alignment,
                normalized_alignment=normalized_alignment,
            )

        except Exception as e:
            raise RuntimeError(f"ElevenLabs TTS synthesis with timestamps failed: {str(e)}") from e

    async def synthesize_dialogue_with_timestamps(
        self,
        dialogue_lines: List[DialogueLine],
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: float = 0.5,
    ) -> SynthesisWithTimestampsResponse:
        inputs = []
        for line in dialogue_lines:
            compiled_text = self.compile_text(line.text)
            inputs.append({
                "text": compiled_text,
                "voice_id": line.voice_id
            })
        
        try:
            response = self.client.text_to_dialogue.convert_with_timestamps(
                inputs=inputs,
                output_format=f"pcm_{SAMPLE_RATE}",
            )

            pcm_data = base64.b64decode(response.audio_base_64)
            audio_bytes = self._wrap_pcm_as_wav(pcm_data, SAMPLE_RATE)
            
            voice_segments = [VoiceSegment(**seg.model_dump()) for seg in response.voice_segments]
            alignment = Alignment(**response.alignment.model_dump())
            normalized_alignment = Alignment(**response.normalized_alignment.model_dump())
            
            voice_id = dialogue_lines[0].voice_id if dialogue_lines else "unknown"
            
            return SynthesisWithTimestampsResponse(
                audio=audio_bytes,
                metadata=SynthesisMetadata(
                    voice_id=voice_id,
                    model="eleven_v3",
                    audio_format="wav",
                    streaming=False,
                    size_bytes=len(audio_bytes),
                    sample_rate=SAMPLE_RATE,
                ),
                voice_segments=voice_segments,
                alignment=alignment,
                normalized_alignment=normalized_alignment,
            )

        except Exception as e:
            raise RuntimeError(f"ElevenLabs dialogue synthesis with timestamps failed: {str(e)}") from e
    
