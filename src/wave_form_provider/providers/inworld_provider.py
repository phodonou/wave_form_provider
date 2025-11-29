"""Inworld AI TTS Provider implementation."""

import os
import base64
import io
import wave
from typing import Optional, List
import requests
from .tts_provider import TTSProvider, SynthesisResponse, SynthesisStreamResponse, SynthesisMetadata, DialogueLine
from ..util.util import convert_parentheses_to_brackets, resample_wav, TARGET_SAMPLE_RATE


class InworldProvider(TTSProvider):
    """Inworld AI TTS provider implementation."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("INWORLD_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Inworld API key is required. Set INWORLD_API_KEY env var or pass api_key parameter."
            )
        
        self.base_url = "https://api.inworld.ai/tts/v1/voice"

    def compile_text(self, text: str) -> str:
        """Convert () to [] for Inworld - it uses [emotion] format."""
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
        
        payload = {
            "text": text,
            "voiceId": voice_id,
            "modelId": "inworld-tts-1",
            "audioConfig": {
                "audioEncoding": "LINEAR16"
            }
        }
        
        if creativity != 0.5:
            payload["audioConfig"]["temperature"] = creativity * 2.0
        
        headers = {
            "Authorization": f"Basic {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            audio_bytes = base64.b64decode(result["audioContent"])
            audio_bytes, sample_rate = resample_wav(audio_bytes, TARGET_SAMPLE_RATE)
        
            return SynthesisResponse(
                audio=audio_bytes,
                metadata=SynthesisMetadata(
                    voice_id=voice_id,
                    model="inworld-tts-1",
                    audio_format="wav",
                    streaming=False,
                    size_bytes=len(audio_bytes),
                    sample_rate=sample_rate,
                )
            )
            
        except Exception as e:
            raise RuntimeError(f"Inworld TTS synthesis failed: {str(e)}") from e

    async def synthesize_dialogue(
        self,
        dialogue_lines: List[DialogueLine],
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: float = 0.5,
    ) -> SynthesisResponse:
        if not dialogue_lines:
            raise ValueError("dialogue_lines must contain at least one item")

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
            meta_voice_id = "multiple"
        else:
            meta_voice_id = dialogue_lines[0].voice_id
        
        return SynthesisResponse(
            audio=audio_bytes,
            metadata=SynthesisMetadata(
                voice_id=meta_voice_id,
                model="inworld-tts-1",
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
        raise NotImplementedError("Streaming not supported by Inworld provider")
