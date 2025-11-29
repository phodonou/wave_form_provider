import audioop
import io
import re
import wave

TARGET_SAMPLE_RATE = 24000


def resample_wav(audio_bytes: bytes, target_rate: int = TARGET_SAMPLE_RATE) -> tuple[bytes, int]:
    """
    Resample WAV audio to target sample rate.
    
    Args:
        audio_bytes: WAV audio as bytes
        target_rate: Target sample rate (default 24000 Hz)
        
    Returns:
        Tuple of (resampled WAV bytes, actual sample rate used)
    """
    with wave.open(io.BytesIO(audio_bytes), 'rb') as wav_in:
        params = wav_in.getparams()
        frames = wav_in.readframes(params.nframes)
        
    if params.framerate == target_rate:
        return audio_bytes, target_rate
    
    converted, _ = audioop.ratecv(
        frames,
        params.sampwidth,
        params.nchannels,
        params.framerate,
        target_rate,
        None
    )
    
    output_buffer = io.BytesIO()
    with wave.open(output_buffer, 'wb') as wav_out:
        wav_out.setnchannels(params.nchannels)
        wav_out.setsampwidth(params.sampwidth)
        wav_out.setframerate(target_rate)
        wav_out.writeframes(converted)
    
    return output_buffer.getvalue(), target_rate


def convert_parentheses_to_brackets(text: str) -> str:
    """
    Convert parentheses to brackets for ElevenLabs.
    
    Converts () style markers to [] format:
    - (sarcastically) → [sarcastically]
    - (whispers) → [whispers]
    - [chuckle] stays as [chuckle]
    
    Args:
        text: Input text with () and [] markers
        
    Returns:
        Text with all markers converted to [] format
    """
    cleaned = re.sub(r'\(([^)]+)\)', r'[\1]', text)
    return cleaned


def remove_ssml(text: str) -> str:
    """
    Remove SSML-like annotations from text.
    
    Removes content within square brackets [] and parentheses () like 
    [laughter], [sigh], (sarcastically), (whispers), etc.
    Handles edge cases like brackets at start/end of text and multiple spaces.
    
    Args:
        text: Input text with potential SSML annotations
        
    Returns:
        Clean text without SSML annotations, with normalized spacing
        
    """
    cleaned = re.sub(r'\[([^\]]+)\]', '', text)
    cleaned = re.sub(r'\(([^)]+)\)', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r'\s+([,.!?;:])', r'\1', cleaned)
    return cleaned.strip()