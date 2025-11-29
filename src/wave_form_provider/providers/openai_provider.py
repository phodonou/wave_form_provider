"""OpenAI TTS Provider implementation."""

import os
from typing import Optional, List
from openai import AsyncOpenAI
from .tts_provider import TTSProvider, SynthesisResponse, SynthesisStreamResponse, SynthesisMetadata, DialogueLine
from ..util.util import remove_ssml, resample_wav, TARGET_SAMPLE_RATE

DEFAULT_OPEN_AI_STYLE_GUIDANCE = """
Voice Affect: Calm, composed, and reassuring; project quiet authority and confidence.

Tone: Sincere, empathetic, and gently authoritative—express genuine apology while conveying competence.

Pacing: Steady and moderate; unhurried enough to communicate care, yet efficient enough to demonstrate professionalism.

Emotion: Genuine empathy and understanding; speak with warmth, especially during apologies ("I'm very sorry for any disruption...").

Pronunciation: Clear and precise, emphasizing key reassurances ("smoothly," "quickly," "promptly") to reinforce confidence.

Pauses: Brief pauses after offering assistance or requesting details, highlighting willingness to listen and support.
"""


class OpenAIProvider(TTSProvider):
    """OpenAI TTS provider implementation."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY env var or pass api_key parameter."
            )
        
        self.client = AsyncOpenAI(api_key=self.api_key)

    def compile_text(self, text: str) -> str:
        """Remove all SSML annotations for OpenAI."""
        return remove_ssml(text)

    async def synthesize(
        self,
        voice_id: str,
        text: str,
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: float = 0.5,
    ) -> SynthesisResponse:
        text = self.compile_text(text)
        instructions = style_guidance if style_guidance else DEFAULT_OPEN_AI_STYLE_GUIDANCE
        
        try:
            response = await self.client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice=voice_id,
                input=text,
                instructions=instructions,
                response_format="wav",
            )
            
            audio_bytes = response.content
            audio_bytes, sample_rate = resample_wav(audio_bytes, TARGET_SAMPLE_RATE)
            
            return SynthesisResponse(
                audio=audio_bytes,
                metadata=SynthesisMetadata(
                    voice_id=voice_id,
                    model="gpt-4o-mini-tts",
                    audio_format="wav",
                    streaming=False,
                    size_bytes=len(audio_bytes),
                    sample_rate=sample_rate,
                )
            )
            
        except Exception as e:
            raise RuntimeError(f"OpenAI TTS synthesis failed: {str(e)}") from e
    
    async def synthesize_dialogue(
        self,
        dialogue_lines: List[DialogueLine],
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: float = 0.5,
    ) -> SynthesisResponse:
        raise NotImplementedError("Dialogue synthesis not yet implemented for OpenAI provider")
    
    async def synthesize_stream(
        self,
        voice_id: str,
        text: str,
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: float = 0.5,
    ) -> SynthesisStreamResponse:
        raise NotImplementedError("Streaming not supported by OpenAI provider")
    

