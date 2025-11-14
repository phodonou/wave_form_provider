"""Google Gemini TTS Provider implementation."""

import os
from typing import Optional
from google.cloud import texttospeech_v1 as texttospeech
from .tts_provider import TTSProvider, SynthesisResponse, SynthesisStreamResponse, SynthesisMetadata
from ..util.util import convert_parentheses_to_brackets


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
            audio_encoding=texttospeech.AudioEncoding.MP3,
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
            audio_bytes = response.audio_content
            
            return SynthesisResponse(
                audio=audio_bytes,
                metadata=SynthesisMetadata(
                    voice_id=voice_id,
                    model="gemini-2.5-flash-tts",
                    streaming=False,
                    size_bytes=len(audio_bytes),
                )
            )
            
        except Exception as e:
            raise RuntimeError(f"Google Gemini TTS synthesis failed: {str(e)}") from e
    
    async def synthesize_stream(
        self,
        voice_id: str,
        text: str,
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: float = 0.5,
    ) -> SynthesisStreamResponse:
        raise NotImplementedError("Streaming not supported by Google Gemini provider")
    

