# Wave Form Provider

A universal TTS (Text-to-Speech) provider interface with unified expressive markup syntax. Write once, synthesize anywhere.

## Why Wave Form Provider?

Expressive voice models have reached near-human quality. Over the past year, both open-source and commercial TTS providers have exploded with models that let creators control emotion, expressiveness, and delivery with precision. They now handle tone, emotion, and non-verbal sounds (laughs, sighs, whispers) at incredible quality.

However, each provider has their own interface, API, studio, and markup syntax. That makes it hard to experiment, switch, fallback, compare, or mix outputs between models.

**Wave Form Provider** solves this by providing a unified interface that works across all the best voice models. Write your script once using a simple, consistent syntax, and let the library handle the provider-specific compilation.

- **Unified Syntax**: One markup language works across all TTS providers
- **Provider Agnostic**: Switch providers without rewriting your text
- **Expressive Control**: Add emotions, actions, speed, and more
- **Type Safe**: Full type hints and async support
- **Well Tested**: 147+ tests across all providers

## Installation

```bash
# Clone the repository
git clone https://github.com/phodonou/wave_form_provider.git
cd wave_form_provider

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Example: Cartesia Quick Test

Sign up for a Cartesia Sonic API key at [cartesia.ai/sonic](https://cartesia.ai/sonic) before running the example.

Set `CARTESIA_API_KEY` in your environment (or pass `api_key="..."`) and run the script below:

```python
import asyncio
from wave_form_provider.providers import CartesiaProvider

async def main():
    provider = CartesiaProvider()  # Reads CARTESIA_API_KEY from env, or pass api_key="..."

    response = await provider.synthesize(
        voice_id="6ccbfb76-1fc6-48f7-b71d-91ac6298247b", 
        text="Hello there! [laughter] (excited) This is amazing!"
    )

    with open("output_cartesia.mp3", "wb") as f:
        f.write(response.audio)

asyncio.run(main())
```

## Supported Providers

- Cartesia
- Hume
- Inworld
- ElevenLabs
- Google Gemini
- OpenAI
- Orpheus

## Unified Syntax

The syntax is simple: write what you want to say and how you want to say it using a universal format. Use `[]` for things that can be inserted into speech, like actions. Use `()` to dictate how to say the subsequent speech. The library automatically compiles this into the right format for each TTS provider.

### Actions (Inserts) - `[]`
Actions that happen *during* speech:
```python
"Hello! [laugh] How are you? [sigh]"
"That's interesting [pause] tell me more."
```

Common actions: `[laugh]`, `[chuckle]`, `[sigh]`, `[gasp]`, `[pause]`, `[long pause]`

### Delivery (Style) - `()`
Control *how* the text is spoken:

#### Emotions
```python
"(excited) I got the job! (sad) But I have to move."
```

#### Speed
```python
"(fast) Quick announcement: (slow) Now speaking slowly."
```

#### Volume
```python
"(quiet) Whisper this. (shout) Shout this!"
```

#### Special
```python
"My name is (spell) Bob."
```

### Combined Example
```python
text = "Hello! [laugh] (excited) I have great news! (fast) Let me tell you more."
```

## Provider-Specific Compilation

The library automatically compiles the unified syntax for each provider:

### Cartesia
- **Actions**: Passed through as `[action]`
- **Emotions**: Compiled to `<emotion value="angry" />`
- **Speed**: Maps to `<speed ratio="X"/>` (`(slow)` → 0.6, `(fast)` → 1.3, `(really fast)` → 1.5)
- **Volume**: Maps to `<volume ratio="X"/>` (`(quiet)` → 0.5, `(loud)` → 1.5, `(shout)` → 2.0)
- **Pauses**: Maps to `<break time="X"/>` (`(pause)` → 1s, `(long pause)` → 2s)
- **Special**: `(spell)word` → `<spell>word</spell>`

### Hume
- **Actions**: Added to `description` field
- **Emotions**: Added to `description` field
- **Speed**: Maps to `speed` parameter (`(slow)` → 0.6, `(fast)` → 1.5, `(really fast)` → 2.0)
- **Volume**: Not supported
- **Pauses**: `[pause]` at end → `trailing_silence: 2`, `[long pause]` → `trailing_silence: 4`. Preserved in text when in the middle

### Inworld
- **Actions**: Passed through as `[action]`
- **Emotions**: Prepended as `[emotion]` to each segment
- **Speed**: Maps to `speakingRate` parameter (`(slow)` → 0.7, `(fast)` → 1.3, `(really fast)` → 1.5)
- **Volume**: Not supported
- **Pauses**: Not supported

### ElevenLabs
- **Actions**: Converted `[action]` → `[action]` (preserved)
- **Emotions**: Converted `(emotion)` → `[emotion]`
- **Speed**: Converted `(speed)` → `[speed]` (provider interprets)
- **Volume**: Converted `(volume)` → `[volume]` (provider interprets)
- **Pauses**: Converted `[pause]` → `[pause]` (preserved)

### Google Gemini
- **Actions**: Converted `[action]` → `[action]` (preserved)
- **Emotions**: Converted `(emotion)` → `[emotion]`
- **Speed**: Converted `(speed)` → `[speed]` (provider interprets)
- **Volume**: Converted `(volume)` → `[volume]` (provider interprets)
- **Pauses**: Converted `[pause]` → `[pause]` (preserved)

### Orpheus
- **Actions**: Converted `[action]` → `<action>`
- **Emotions**: Stripped (not supported)
- **Speed**: Stripped (not supported)
- **Volume**: Stripped (not supported)
- **Pauses**: Converted `[pause]` → `<pause>`

### OpenAI
- **Actions**: Controlled via `style_guidance` parameter
- **Emotions**: Controlled via `style_guidance` parameter
- **Speed**: Controlled via `style_guidance` parameter
- **Volume**: Controlled via `style_guidance` parameter
- **Pauses**: Controlled via `style_guidance` parameter
- *Note: All markup is stripped from text. Use natural language in `style_guidance` like "speak with excitement and laugh occasionally"*

## Using Different Providers

Import any provider directly:

```python
from wave_form_provider.providers import CartesiaProvider, ElevenLabsProvider, HumeProvider

# Use Cartesia
cartesia = CartesiaProvider()
response = await cartesia.synthesize(voice_id="...", text="...")

# Use ElevenLabs
elevenlabs = ElevenLabsProvider(api_key="...")
response = await elevenlabs.synthesize(voice_id="...", text="...")
```

## Environment Variables

Set API keys via environment variables:

```bash
export CARTESIA_API_KEY="your-key"
export HUME_API_KEY="your-key"
export INWORLD_API_KEY="your-key"
export ELEVENLABS_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
export REPLICATE_API_TOKEN="your-key"  # For Orpheus
export GOOGLE_GENERATIVE_AI_API_KEY="your-key"
```

## Testing

```bash
# Run all tests
pytest tests/

# Run specific provider tests
pytest tests/test_cartesia_provider.py -v

```

## Roadmap

- [ ] Generate proper documentation
- [ ] Publish to PyPI as installable package
- [ ] Create web playground
- [ ] List voices
- [ ] Streaming support
- [ ] Different lang support
- [ ] CLI interface
- [ ] Auto chunk and re-stitch based on character limit
- [ ] Voice cloning interfaces
- [ ] Multi speaker support
- [ ] Get audio back along with timestamps
- [ ] Audio format conversion utilities
- [ ] Cost tracking utilities
- [ ] More OSS providers 

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

Built with love for the voice AI community. Special thanks to all the TTS provider teams for their amazing APIs.

