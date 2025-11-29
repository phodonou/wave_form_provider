"""Test Hume _parse_to_utterances to understand why audio is choppy."""

import re


def _parse_to_utterances(text: str, speed_map: dict) -> list[dict]:
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
            
            if cmd in speed_map:
                if current_text_parts or current_descriptions:
                    utterances.append({
                        'text': ' '.join(current_text_parts).strip(),
                        'speed': current_speed,
                        'description': ', '.join(current_descriptions) if current_descriptions else None,
                    })
                    current_text_parts = []
                    current_descriptions = []
                current_speed = speed_map[cmd]
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


def test_parse(text: str):
    speed_map = {
        "slow": 0.6,
        "normal": 1.0,
        "fast": 1.5,
        "really fast": 2.0,
    }
    
    print(f"\n{'='*60}")
    print(f"Input text: {text!r}")
    print(f"{'='*60}\n")
    
    utterances = _parse_to_utterances(text, speed_map)
    
    print(f"Parsed into {len(utterances)} utterance(s):\n")
    for i, u in enumerate(utterances, 1):
        print(f"Utterance {i}:")
        print(f"  text: {u['text']!r}")
        print(f"  speed: {u.get('speed')}")
        print(f"  description: {u.get('description')}")
        print(f"  trailing_silence: {u.get('trailing_silence')}")
        print()


if __name__ == "__main__":
    # Test with both () and [] to see splitting behavior
    test_text = "Hello there! [laugh] This is amazing! (happy) I'm glad you're here."
    test_parse(test_text)
    
    print("\n" + "="*60)
    print("More test cases:")
    print("="*60)
    
    test_cases = [
        "Hello world",
        "(happy) Hello! [laugh] Ha ha! (sad) Goodbye.",
        "[sigh] I don't know. [laugh] Just kidding!",
    ]
    
    for text in test_cases:
        test_parse(text)

