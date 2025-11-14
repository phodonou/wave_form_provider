import re


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