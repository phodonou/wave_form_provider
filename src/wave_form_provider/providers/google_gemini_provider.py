"""Google Gemini TTS Provider implementation."""

import io
import os
import wave
from typing import Optional, List
from google.cloud import texttospeech_v1 as texttospeech
from .tts_provider import TTSProvider, SynthesisResponse, SynthesisStreamResponse, SynthesisMetadata, DialogueLine
from ..util.util import convert_parentheses_to_brackets

SAMPLE_RATE = 24000

class GoogleGeminiProvider(TTSProvider):
    """Google Gemini TTS provider implementation."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_GENERATIVE_AI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Google API key required. Set GOOGLE_GENERATIVE_AI_API_KEY env var or pass api_key parameter."
            )
        
        os.environ["GOOGLE_GENERATIVE_AI_API_KEY"] = self.api_key
        self.client = texttospeech.TextToSpeechClient()

    def compile_text(self, text: str) -> str:
        """Convert () style markers to [] format for Google Gemini, like ElevenLabs."""
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
        creativity: float = 0.5,
    ) -> SynthesisResponse:
        text = self.compile_text(text)
        prompt = style_guidance if style_guidance else "Say the following naturally"
        
        synthesis_input = texttospeech.SynthesisInput(
            text=text,
            prompt=prompt
        )
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name=voice_id,
            model_name="gemini-2.5-flash-tts",
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            sample_rate_hertz=SAMPLE_RATE,
            speaking_rate=1.0,
            volume_gain_db=0.0,
        )
        
        try:
            request = texttospeech.SynthesizeSpeechRequest(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config,
                advanced_voice_options=texttospeech.AdvancedVoiceOptions(
                    low_latency_journey_synthesis=True,
                ),
            )
            
            response = self.client.synthesize_speech(request=request)
            pcm_data = response.audio_content
            audio_bytes = self._wrap_pcm_as_wav(pcm_data, SAMPLE_RATE)
            
            return SynthesisResponse(
                audio=audio_bytes,
                metadata=SynthesisMetadata(
                    voice_id=voice_id,
                    model="gemini-2.5-flash-tts",
                    audio_format="wav",
                    streaming=False,
                    size_bytes=len(audio_bytes),
                    sample_rate=SAMPLE_RATE,
                )
            )
            
        except Exception as e:
            raise RuntimeError(f"Google Gemini TTS synthesis failed: {str(e)}") from e
    
    async def synthesize_dialogue(
        self,
        dialogue_lines: List[DialogueLine],
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: float = 0.5,
    ) -> SynthesisResponse:
        raise NotImplementedError("Dialogue synthesis not yet implemented for Google Gemini provider")
    
    async def synthesize_stream(
        self,
        voice_id: str,
        text: str,
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: float = 0.5,
    ) -> SynthesisStreamResponse:
        raise NotImplementedError("Streaming not supported by Google Gemini provider")

