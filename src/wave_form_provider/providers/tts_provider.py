"""TTS Provider abstract interface."""
from abc import ABC, abstractmethod
from typing import Optional, AsyncIterator
from pydantic import BaseModel, Field, ConfigDict
from typing import List

class SynthesisMetadata(BaseModel):
    """Metadata about the synthesized audio."""
    voice_id: str
    model: str
    audio_format: str = "wav"
    size_bytes: Optional[int] = None
    streaming: bool = False
    duration_seconds: Optional[float] = None
    sample_rate: Optional[int] = None

class DialogueLine(BaseModel):
    text: str
    voice_id: str

class SynthesisResponse(BaseModel):
    """Response from TTS synthesis."""
    audio: bytes
    metadata: SynthesisMetadata

class SynthesisStreamResponse(BaseModel):
    """Response from TTS synthesis stream."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    audio: AsyncIterator[bytes]
    metadata: SynthesisMetadata

class VoiceSegment(BaseModel):
    voice_id: str
    start_time_seconds: float
    end_time_seconds: float
    character_start_index: int
    character_end_index: int
    dialogue_input_index: int

class Alignment(BaseModel):
    characters: List[str]
    character_start_times_seconds: List[float]
    character_end_times_seconds: List[float]

class SynthesisWithTimestampsResponse(BaseModel):
    audio: bytes
    metadata: SynthesisMetadata
    voice_segments: Optional[List[VoiceSegment]] = None
    alignment: Alignment
    normalized_alignment: Alignment
    
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
    async def synthesize_dialogue(
        self,
        dialogue_lines: List[DialogueLine],
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: float = 0.5,
    ) -> SynthesisResponse:
        """Generate speech from dialogue lines. Returns SynthesisResponse with audio in bytes and metadata."""
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

    async def synthesize_with_timestamps(
        self,
        voice_id: str,
        text: str,
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: float = 0.5,
    ) -> SynthesisWithTimestampsResponse:
        raise NotImplementedError(f"{self.__class__.__name__} does not support synthesize_with_timestamps")

    async def synthesize_dialogue_with_timestamps(
        self,
        dialogue_lines: List[DialogueLine],
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: float = 0.5,
    ) -> SynthesisWithTimestampsResponse:
        raise NotImplementedError(f"{self.__class__.__name__} does not support synthesize_dialogue_with_timestamps")