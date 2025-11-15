"""Hume AI TTS Provider implementation."""

import os
import base64
import re
from typing import Optional
from hume import HumeClient
from hume.tts import (
    PostedUtterance,
    PostedUtteranceVoiceWithName,
    PostedUtteranceVoiceWithId,
)
from .tts_provider import TTSProvider, SynthesisResponse, SynthesisStreamResponse, SynthesisMetadata


class HumeProvider(TTSProvider):
    """Hume AI TTS provider implementation."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("HUME_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Hume API key is required. Set HUME_API_KEY env var or pass api_key parameter."
            )

        self.client = HumeClient(api_key=self.api_key)
        
        self.speed_map = {
            "slow": 0.6,
            "normal": 1.0,
            "fast": 1.5,
            "really fast": 2.0,
        }

    def compile_text(self, text: str) -> str:
        return text
    
    def _parse_to_utterances(self, text: str) -> list[dict]:
        utterances = []
        current_text_parts = []
        current_speed = None
        current_descriptions = []
        
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
                    if current_text_parts or current_descriptions:
                        utterances.append({
                            'text': ' '.join(current_text_parts).strip(),
                            'speed': current_speed,
                            'description': ', '.join(current_descriptions) if current_descriptions else None,
                        })
                        current_text_parts = []
                        current_descriptions = []
                    current_speed = self.speed_map[cmd]
                else:
                    if current_text_parts or current_descriptions:
                        utterances.append({
                            'text': ' '.join(current_text_parts).strip(),
                            'speed': current_speed,
                            'description': ', '.join(current_descriptions) if current_descriptions else None,
                        })
                        current_text_parts = []
                        current_descriptions = []
                    current_descriptions.append(cmd)
            
            elif command.startswith('['):
                action = command[1:-1].strip().lower()
                if action in ['pause', 'long pause']:
                    current_text_parts.append(command)
                else:
                    current_descriptions.append(action)
        
        if current_text_parts or current_descriptions:
            utterances.append({
                'text': ' '.join(current_text_parts).strip(),
                'speed': current_speed,
                'description': ', '.join(current_descriptions) if current_descriptions else None,
            })
        
        filtered = [u for u in utterances if u['text'] or u['description']]
        
        for utterance in filtered:
            text = utterance['text']
            if text.endswith('[long pause]'):
                utterance['text'] = text[:-len('[long pause]')].strip()
                utterance['trailing_silence'] = 4
            elif text.endswith('[pause]'):
                utterance['text'] = text[:-len('[pause]')].strip()
                utterance['trailing_silence'] = 2
        
        return filtered

    async def synthesize(
        self,
        voice_id: str,
        text: str,
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: float = 0.5,
    ) -> SynthesisResponse:
        compiled_text = self.compile_text(text)
        utterance_dicts = self._parse_to_utterances(compiled_text)

        voice = PostedUtteranceVoiceWithId(
            id=voice_id,
            provider="HUME_AI",
        )

        utterances = []
        for u_dict in utterance_dicts:
            description = u_dict['description']
            if style_guidance:
                if description:
                    description = f"{style_guidance}, {description}"
                else:
                    description = style_guidance
            
            utterance_params = {
                'text': u_dict['text'],
                'voice': voice,
                'description': description,
            }
            
            if u_dict.get('speed') is not None:
                utterance_params['speed'] = u_dict['speed']
            
            if u_dict.get('trailing_silence') is not None:
                utterance_params['trailing_silence'] = u_dict['trailing_silence']
            
            utterance = PostedUtterance(**utterance_params)
            utterances.append(utterance)

        try:
            response = self.client.tts.synthesize_json_streaming(
                utterances=utterances,
            )


            audio_bytes = b""
            audio_format = None
            sample_rate = 22050

            chunk_count = 0
            try:
                for chunk in response:
                    chunk_count += 1

                    chunk_dict = (
                        chunk
                        if isinstance(chunk, dict)
                        else (
                            chunk.model_dump()
                            if hasattr(chunk, "model_dump")
                            else vars(chunk) if hasattr(chunk, "__dict__") else None
                        )
                    )

                    if chunk_dict and chunk_dict.get("type") == "audio":
                        audio_data = chunk_dict.get("audio")
                        if audio_data:
                            chunk_audio = base64.b64decode(audio_data)
                            audio_bytes += chunk_audio

                        if chunk_dict.get("audio_format"):
                            audio_format = chunk_dict["audio_format"]
            except Exception as e:
                print(f"Error iterating chunks: {e}")
                import traceback

                traceback.print_exc()

            return SynthesisResponse(
                audio=audio_bytes,
                metadata=SynthesisMetadata(
                    voice_id=voice_id,
                    model="octave",
                    streaming=False,
                    size_bytes=len(audio_bytes),
                    sample_rate=sample_rate,
                ),
            )

        except Exception as e:
            raise RuntimeError(f"Hume TTS synthesis failed: {str(e)}") from e
    
    async def synthesize_stream(
        self,
        voice_id: str,
        text: str,
        style_guidance: Optional[str] = None,
        seed: Optional[float] = None,
        creativity: float = 0.5,
    ) -> SynthesisStreamResponse:
        raise NotImplementedError("Streaming not supported by Hume provider")
    
