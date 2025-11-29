"""Cartesia TTS Provider implementation."""

import io
import os
import re
import wave
from typing import Optional, List
import requests
from .tts_provider import (
    TTSProvider,
    SynthesisResponse,
    SynthesisStreamResponse,
    SynthesisMetadata,
    DialogueLine,
)


class CartesiaProvider(TTSProvider):
    """Cartesia TTS provider implementation."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("CARTESIA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Cartesia API key is required. Set CARTESIA_API_KEY env var or pass api_key parameter."
            )
        
        self.base_url = "https://api.cartesia.ai/tts/bytes"
        
        self.speed_map = {
            "slow": 0.6,
            "normal": 1.0,
            "fast": 1.3,
            "really fast": 1.5,
        }
        
        self.volume_map = {
            "quiet": 0.5,
            "normal": 1.0,
            "loud": 1.5,
            "shout": 2.0,
        }
        
        self.pause_map = {
            "short pause": "0.5s",
            "pause": "1s",
            "long pause": "2s",
        }

    def compile_text(self, text: str) -> str:
        """
        Compile unified syntax to Cartesia-specific format.
        
        Converts:
        - (slow), (fast), etc. → <speed ratio="X"/>
        - (quiet), (shout), etc. → <volume ratio="X"/>
        - (pause), (long pause), etc. → <break time="Xs"/>
        - (spell) word → <spell>word</spell>
        - (angry), (sad), etc. → <emotion value="angry" />
        - [laughter], [sigh], etc. → kept as [action] (insert actions)
        - Provider-specific tags → passed through
        """
        result = text
        
        for command, ratio in self.speed_map.items():
            pattern = rf'\({re.escape(command)}\)'
            replacement = f'<speed ratio="{ratio}"/>'
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        for command, ratio in self.volume_map.items():
            pattern = rf'\({re.escape(command)}\)'
            replacement = f'<volume ratio="{ratio}"/>'
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        for command, time_value in self.pause_map.items():
            pattern = rf'\({re.escape(command)}\)'
            replacement = f'<break time="{time_value}"/>'
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        def replace_spell(match):
            word = match.group(1)
            return f'<spell>{word}</spell>'
        
        result = re.sub(r'\(spell\)\s*([A-Za-z0-9\-\(\)]+)', replace_spell, result, flags=re.IGNORECASE)
        
        def replace_emotion(match):
            pos = match.start()
            before = result[:pos]
            if '<spell>' in before:
                last_spell_open = before.rfind('<spell>')
                last_spell_close = before.rfind('</spell>')
                if last_spell_close < last_spell_open:
                    return match.group(0)
            
            emotion = match.group(1).strip().lower()
            if emotion in self.speed_map or emotion in self.volume_map or emotion in self.pause_map or emotion == 'spell':
                return match.group(0)
            return f'<emotion value="{match.group(1).strip()}" />'
        
        result = re.sub(r'\(([^)]+)\)', replace_emotion, result)
        
        return result

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
            "model_id": "sonic-3",
            "transcript": text,
            "voice": {
                "mode": "id",
                "id": voice_id
            },
            "language": "en",
            "output_format": {
                "container": "wav",
                "encoding": "pcm_s16le",
                "sample_rate": 24000
            },
        }
        
        headers = {
            "Cartesia-Version": "2024-06-10",
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(self.base_url, json=payload, headers=headers)
            if not response.ok:
                error_detail = response.text
                raise RuntimeError(f"Cartesia API error {response.status_code}: {error_detail}")
            response.raise_for_status()
            
            audio_bytes = response.content
            
            return SynthesisResponse(
                audio=audio_bytes,
                metadata=SynthesisMetadata(
                    voice_id=voice_id,
                    model="sonic-3",
                    streaming=False,
                    size_bytes=len(audio_bytes),
                    sample_rate=24000,
                )
            )
            
        except Exception as e:
            raise RuntimeError(f"Cartesia TTS synthesis failed: {str(e)}") from e
    
    async def synthesize_dialogue(
        self,
        dialogue_lines: List[DialogueLine],
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: float = 0.5,
    ) -> SynthesisResponse:
        """
        Generate speech for multiple dialogue lines by composing individual Cartesia TTS calls.
        """
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
                model="sonic-3",
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
        raise NotImplementedError("Streaming not supported by Cartesia provider")

