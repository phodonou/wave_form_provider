"""Orpheus TTS Provider implementation via Replicate."""

import io
import os
import re
import wave
from typing import Optional, List
import replicate
from .tts_provider import TTSProvider, SynthesisResponse, SynthesisStreamResponse, SynthesisMetadata, DialogueLine
from ..util.util import resample_wav, TARGET_SAMPLE_RATE


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
            
            audio_bytes, sample_rate = resample_wav(audio_bytes, TARGET_SAMPLE_RATE)
            
            return SynthesisResponse(
                audio=audio_bytes,
                metadata=SynthesisMetadata(
                    voice_id=voice_id,
                    model="orpheus-3b",
                    audio_format="wav",
                    streaming=False,
                    size_bytes=len(audio_bytes),
                    sample_rate=sample_rate,
                )
            )
            
        except Exception as e:
            raise RuntimeError(f"Orpheus TTS synthesis failed: {str(e)}") from e
    
    async def synthesize_dialogue(
        self,
        dialogue_lines: List[DialogueLine],
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: float = 0.5,
    ) -> SynthesisResponse:
        if not dialogue_lines:
            raise ValueError("dialogue_lines cannot be empty")

        pcm_frames: List[bytes] = []
        params = None

        for line in dialogue_lines:
            response = await self.synthesize(
                voice_id=line.voice_id,
                text=line.text,
                style_guidance=style_guidance,
                seed=seed,
                creativity=creativity,
            )
            
            with wave.open(io.BytesIO(response.audio), 'rb') as wav_in:
                if params is None:
                    params = wav_in.getparams()
                pcm_frames.append(wav_in.readframes(wav_in.getnframes()))

        sample_rate = params.framerate
        num_channels = params.nchannels
        sample_width = params.sampwidth

        pause_seconds = 0.5
        silence_samples = int(sample_rate * pause_seconds)
        silence = b"\x00" * (silence_samples * num_channels * sample_width)

        combined_pcm = pcm_frames[0]
        for frame in pcm_frames[1:]:
            combined_pcm += silence + frame

        output_buffer = io.BytesIO()
        with wave.open(output_buffer, 'wb') as wav_out:
            wav_out.setnchannels(num_channels)
            wav_out.setsampwidth(sample_width)
            wav_out.setframerate(sample_rate)
            wav_out.writeframes(combined_pcm)

        audio_bytes = output_buffer.getvalue()

        if len({line.voice_id for line in dialogue_lines}) > 1:
            meta_voice_id = "multi-voice"
        else:
            meta_voice_id = dialogue_lines[0].voice_id

        return SynthesisResponse(
            audio=audio_bytes,
            metadata=SynthesisMetadata(
                voice_id=meta_voice_id,
                model="orpheus-3b",
                audio_format="wav",
                streaming=False,
                size_bytes=len(audio_bytes),
                sample_rate=sample_rate,
            ),
        )
    
    async def synthesize_stream(
        self,
        voice_id: str,
        text: str,
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: float = 0.5,
    ) -> SynthesisStreamResponse:
        raise NotImplementedError("Streaming not supported by Orpheus provider")
    

