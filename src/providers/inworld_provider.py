"""Inworld AI TTS Provider implementation."""

import os
import base64
import re
from typing import Optional
import requests
from .tts_provider import TTSProvider, SynthesisResponse, SynthesisStreamResponse, SynthesisMetadata


class InworldProvider(TTSProvider):
    """Inworld AI TTS provider implementation."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("INWORLD_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Inworld API key is required. Set INWORLD_API_KEY env var or pass api_key parameter."
            )
        
        self.base_url = "https://api.inworld.ai/tts/v1/voice"
        
        self.speed_map = {
            "slow": 0.7,
            "normal": 1.0,
            "fast": 1.3,
            "really fast": 1.5,
        }

    def compile_text(self, text: str) -> str:
        """Pass text through - processing happens in _parse_to_segments."""
        return text
    
    def _parse_to_segments(self, text: str) -> list[dict]:
        """
        Parse text into segments, splitting on emotion/speed changes.
        
        Returns list of segments with:
        - text: The text content (with [] actions preserved)
        - emotion: Emotion marker to prepend (or None)
        - speed: Speed value for audioConfig.speakingRate (or None)
        """
        segments = []
        current_text_parts = []
        current_speed = None
        current_emotion = None
        
        pattern = r'(\([^)]+\)|\[[^\]]+\])'
        
        i = 0
        while i < len(text):
            match = re.search(pattern, text[i:])
            if not match:
                remaining = text[i:].strip()
                if remaining:
                    current_text_parts.append(remaining)
                break
            
            before = text[i:i+match.start()].strip()
            if before:
                current_text_parts.append(before)
            
            command = match.group(1)
            i += match.end()
            
            if command.startswith('('):
                cmd = command[1:-1].strip().lower()
                
                if cmd in self.speed_map:
                    # Speed change - create new segment
                    if current_text_parts:
                        segments.append({
                            'text': ' '.join(current_text_parts).strip(),
                            'emotion': current_emotion,
                            'speed': current_speed,
                        })
                        current_text_parts = []
                        current_emotion = None  # Emotion doesn't persist
                    current_speed = self.speed_map[cmd]
                else:
                    # Emotion change - create new segment
                    if current_text_parts:
                        segments.append({
                            'text': ' '.join(current_text_parts).strip(),
                            'emotion': current_emotion,
                            'speed': current_speed,
                        })
                        current_text_parts = []
                        current_speed = None  # Speed doesn't persist
                    current_emotion = cmd
            
            elif command.startswith('['):
                # Action - keep in text
                current_text_parts.append(command)
        
        if current_text_parts:
            segments.append({
                'text': ' '.join(current_text_parts).strip(),
                'emotion': current_emotion,
                'speed': current_speed,
            })
        
        return [s for s in segments if s['text']]

    async def synthesize(
        self,
        voice_id: str,
        text: str,
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: float = 0.5,
    ) -> SynthesisResponse:
        compiled_text = self.compile_text(text)
        segments = self._parse_to_segments(compiled_text)
        
        if len(segments) > 3:
            print(f"Warning: {len(segments)} emotion/speed changes detected. This will result in {len(segments)} API calls.")
        
        audio_chunks = []
        total_size = 0
        
        for segment in segments:
            segment_text = segment['text']
            
            # Prepend emotion marker if present
            if segment['emotion']:
                segment_text = f"[{segment['emotion']}] {segment_text}"
            
            payload = {
                "text": segment_text,
                "voiceId": voice_id,
                "modelId": "inworld-tts-1",
                "audioConfig": {}
            }
            
            # Add speaking rate if present
            if segment.get('speed') is not None:
                payload["audioConfig"]["speakingRate"] = segment['speed']
            
            # Add temperature (creativity)
            if creativity != 0.5:
                payload["audioConfig"]["temperature"] = creativity * 2.0  # Map 0.5 to 1.0 (Inworld default)
            
            headers = {
                "Authorization": f"Basic {self.api_key}",
                "Content-Type": "application/json"
            }
            
            try:
                response = requests.post(self.base_url, json=payload, headers=headers)
                response.raise_for_status()
                
                result = response.json()
                audio_bytes = base64.b64decode(result["audioContent"])
                audio_chunks.append(audio_bytes)
                total_size += len(audio_bytes)
                
            except Exception as e:
                raise RuntimeError(f"Inworld TTS synthesis failed on segment '{segment_text[:50]}...': {str(e)}") from e
        
        # Concatenate all audio chunks
        combined_audio = b"".join(audio_chunks)
        
        return SynthesisResponse(
            audio=combined_audio,
            metadata=SynthesisMetadata(
                voice_id=voice_id,
                model="inworld-tts-1",
                streaming=False,
                size_bytes=total_size,
            )
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
    
    async def list_voices(self) -> list[str]:
        raise NotImplementedError("Voice listing not supported by Inworld provider")
    
    async def clone_voice(self, voice_id: str) -> str:
        raise NotImplementedError("Voice cloning not supported by Inworld provider")

