"""Chatterbox TTS Provider implementation via Replicate."""

import os
from typing import Optional
import replicate
from .tts_provider import TTSProvider, SynthesisResponse, SynthesisStreamResponse, SynthesisMetadata


class ChatterboxProvider(TTSProvider):
    """Chatterbox TTS provider implementation using Replicate."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("REPLICATE_API_TOKEN")
        if not self.api_key:
            raise ValueError(
                "Replicate API token is required. Set REPLICATE_API_TOKEN env var or pass api_key parameter."
            )
        
        os.environ["REPLICATE_API_TOKEN"] = self.api_key

    def compile_text(self, text: str) -> str:
        """Pass text through unchanged for Chatterbox."""
        return text

    async def synthesize(
        self,
        voice_id: str,
        text: str,
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: float = 0.5,
    ) -> SynthesisResponse:
        text = self.compile_text(text)
        input_params = {
            "prompt": text,
            "cfg_weight": 0.5,
            "temperature": creativity if creativity else 0.8,
            "exaggeration": 0.5,
        }
        
        if seed is not None:
            input_params["seed"] = int(seed)
        
        try:
            output = replicate.run(
                "resemble-ai/chatterbox",
                input=input_params
            )
            
            if hasattr(output, 'read'):
                audio_bytes = output.read()
            else:
                audio_bytes = b"".join(output)
            
            return SynthesisResponse(
                audio=audio_bytes,
                metadata=SynthesisMetadata(
                    voice_id=voice_id,
                    model="chatterbox",
                    streaming=False,
                    size_bytes=len(audio_bytes),
                )
            )
            
        except Exception as e:
            raise RuntimeError(f"Chatterbox TTS synthesis failed: {str(e)}") from e
    
    async def synthesize_stream(
        self,
        voice_id: str,
        text: str,
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: float = 0.5,
    ) -> SynthesisStreamResponse:
        raise NotImplementedError("Streaming not supported by Chatterbox provider")
    
    async def list_voices(self) -> list[str]:
        raise NotImplementedError("Voice listing not supported by Chatterbox provider")
    
    async def clone_voice(self, voice_id: str) -> str:
        raise NotImplementedError("Voice cloning not supported by Chatterbox provider")

