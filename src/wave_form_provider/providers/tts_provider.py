"""TTS Provider abstract interface."""
from abc import ABC, abstractmethod
from typing import Optional, AsyncIterator
from pydantic import BaseModel, Field, ConfigDict


class SynthesisMetadata(BaseModel):
    """Metadata about the synthesized audio."""
    voice_id: str
    model: str
    size_bytes: Optional[int] = None
    streaming: bool = False
    duration_seconds: Optional[float] = None
    sample_rate: Optional[int] = None


class SynthesisResponse(BaseModel):
    """Response from TTS synthesis."""
    audio: bytes
    metadata: SynthesisMetadata

class SynthesisStreamResponse(BaseModel):
    """Response from TTS synthesis stream."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    audio: AsyncIterator[bytes]
    metadata: SynthesisMetadata
    
class TTSProvider(ABC):
    """Abstract interface all TTS providers must implement."""

    @abstractmethod
    def compile_text(self, text: str) -> str:
        """
        Compile text for provider-specific requirements.
        
        Unified syntax:
        - [] - insert some action (e.g., [laughter], [chuckle])
        - () - say the subsequent speech in this way (e.g., (sarcastically), (whispers))
        
        Args:
            text: The input text to compile
            
        Returns:
            Compiled text suitable for this provider
        """
        pass

    @abstractmethod
    async def synthesize(
        self,
        voice_id: str,
        text: str,
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: float = 0.5,
    ) -> SynthesisResponse:
        """Generate speech from text. Returns SynthesisResponse with audio in bytes and metadata."""
        pass
    
    @abstractmethod
    async def synthesize_stream(
        self,
        voice_id: str,
        text: str,
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: float = 0.5,
    ) -> SynthesisStreamResponse:
        """Generate speech from text. Returns SynthesisResponse with audio in bytes and metadata."""
        pass