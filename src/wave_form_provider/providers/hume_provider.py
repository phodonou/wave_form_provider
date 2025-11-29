"""Hume AI TTS Provider implementation."""

import os
import base64
import io
import re
import wave
from typing import Optional, List
from hume import HumeClient
from hume.tts import (
    PostedUtterance,
    PostedUtteranceVoiceWithName,
    PostedUtteranceVoiceWithId,
    FormatWav,
    PostedContextWithUtterances,
)
from .tts_provider import TTSProvider, SynthesisResponse, SynthesisStreamResponse, SynthesisMetadata, DialogueLine
from ..util.util import resample_wav, TARGET_SAMPLE_RATE


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
                        current_text_parts = []
                        current_descriptions = []
        
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
            response = self.client.tts.synthesize_json(
                utterances=utterances,
                format=FormatWav(),
                num_generations=1,
            )

            audio_bytes = b""
            sample_rate = 22050

            if hasattr(response, "generations") and response.generations:
                generation = response.generations[0]
                if hasattr(generation, "audio") and generation.audio:
                    audio_bytes = base64.b64decode(generation.audio)
                
                if hasattr(generation, "encoding") and generation.encoding:
                    if hasattr(generation.encoding, "sample_rate"):
                        sample_rate = generation.encoding.sample_rate
            elif isinstance(response, dict):
                if "generations" in response and response["generations"]:
                    generation = response["generations"][0]
                    if "audio" in generation:
                        audio_bytes = base64.b64decode(generation["audio"])
                    if "encoding" in generation and "sample_rate" in generation["encoding"]:
                        sample_rate = generation["encoding"]["sample_rate"]

            audio_bytes, sample_rate = resample_wav(audio_bytes, TARGET_SAMPLE_RATE)

            return SynthesisResponse(
                audio=audio_bytes,
                metadata=SynthesisMetadata(
                    voice_id=voice_id,
                    model="octave",
                    audio_format="wav",
                    streaming=False,
                    size_bytes=len(audio_bytes),
                    sample_rate=sample_rate,
                ),
            )

        except Exception as e:
            raise RuntimeError(f"Hume TTS synthesis failed: {str(e)}") from e

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
                model="octave",
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
        raise NotImplementedError("Streaming not supported by Hume provider")
    
