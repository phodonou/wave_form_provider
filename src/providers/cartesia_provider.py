"""Cartesia TTS Provider implementation."""

import os
import re
from typing import Optional
import requests
from .tts_provider import TTSProvider, SynthesisResponse, SynthesisStreamResponse, SynthesisMetadata


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
                "sample_rate": 44100
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
                    sample_rate=44100,
                )
            )
            
        except Exception as e:
            raise RuntimeError(f"Cartesia TTS synthesis failed: {str(e)}") from e
    
    async def synthesize_stream(
        self,
        voice_id: str,
        text: str,
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: float = 0.5,
    ) -> SynthesisStreamResponse:
        raise NotImplementedError("Streaming not supported by Cartesia provider")
    
    async def list_voices(self) -> list[str]:
        raise NotImplementedError("Voice listing not supported by Cartesia provider")
    
    async def clone_voice(self, voice_id: str) -> str:
        raise NotImplementedError("Voice cloning not supported by Cartesia provider")

