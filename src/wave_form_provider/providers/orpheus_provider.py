"""Orpheus TTS Provider implementation via Replicate."""

import os
import re
from typing import Optional
import replicate
from .tts_provider import TTSProvider, SynthesisResponse, SynthesisStreamResponse, SynthesisMetadata


class OrpheusProvider(TTSProvider):
    """Orpheus TTS provider implementation using Replicate."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("REPLICATE_API_TOKEN")
        if not self.api_key:
            raise ValueError(
                "Replicate API token is required. Set REPLICATE_API_TOKEN env var or pass api_key parameter."
            )
        
        os.environ["REPLICATE_API_TOKEN"] = self.api_key
        self.model = "lucataco/orpheus-3b-0.1-ft:79f2a473e6a9720716a473d9b2f2951437dbf91dc02ccb7079fb3d89b881207f"

    def compile_text(self, text: str) -> str:
        """
        Convert unified syntax to Orpheus format.
        - [action] → <action>
        - (delivery) → removed
        """
        result = re.sub(r'\[([^\]]+)\]', r'<\1>', text)
        
        result = re.sub(r'\([^)]+\)', '', result)
        
        result = re.sub(r'\s+', ' ', result)
        result = re.sub(r'\s+([,.!?;:])', r'\1', result)
        
        return result.strip()

    async def synthesize(
        self,
        voice_id: str,
        text: str,
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: float = 0.5,
    ) -> SynthesisResponse:
        text = self.compile_text(text)
        
        # Map creativity (0.0-1.0) to temperature (0.1-1.5)
        temperature = 0.1 + (creativity * 1.4)
        
        input_params = {
            "text": text,
            "voice": voice_id,
            "temperature": temperature,
            "top_p": 0.95,
            "max_new_tokens": 1200,
            "repetition_penalty": 1.1,
        }
        
        try:
            output = replicate.run(
                self.model,
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
                    model="orpheus-3b",
                    streaming=False,
                    size_bytes=len(audio_bytes),
                )
            )
            
        except Exception as e:
            raise RuntimeError(f"Orpheus TTS synthesis failed: {str(e)}") from e
    
    async def synthesize_stream(
        self,
        voice_id: str,
        text: str,
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: float = 0.5,
    ) -> SynthesisStreamResponse:
        raise NotImplementedError("Streaming not supported by Orpheus provider")
    

