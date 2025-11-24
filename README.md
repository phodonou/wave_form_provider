# Wave Form Provider

A universal TTS (Text-to-Speech) provider interface with unified expressive markup syntax. Write once, synthesize anywhere.

## 🎙️ Try it Live

**[Launch Waveform Studio →](https://www.waveformstudio.app/)**

Interactive script editor with autocomplete and playground to test all providers side-by-side. Write expressive text, compare voices, and generate audio instantly—no API setup required.

![Waveform Demo](auto_demo-ezgif.com-video-to-gif-converter.gif)

## Why Wave Form Provider?

Expressive voice models have reached near-human quality. Over the past year, both open-source and commercial TTS providers have exploded with models that let creators control emotion, expressiveness, and delivery with precision. They now handle tone, emotion, and non-verbal sounds (laughs, sighs, whispers) at incredible quality.

However, each provider has their own interface, API, studio, and markup syntax. That makes it hard to experiment, switch, fallback, compare, or mix outputs between models.

**Wave Form Provider** solves this by providing a unified interface that works across all the best voice models. Write your script once using a simple, consistent syntax, and let the library handle the provider-specific compilation.

- **Unified Syntax**: One markup language works across all TTS providers
- **Provider Agnostic**: Switch providers without rewriting your text
- **Expressive Control**: Add emotions, actions, speed, and more
- **Visual Playground**: Test and compare providers at [waveformstudio.app](https://www.waveformstudio.app/)
- **Type Safe**: Full type hints and async support
- **Well Tested**: 147+ tests across all providers

## Installation

Install from PyPI:

```bash
pip install wave-form-provider
```

Or install from source:

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

> 💡 **Try it live**: Test the syntax at [waveformstudio.app](https://www.waveformstudio.app/) and hear the results instantly across all providers.

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

### Try in the Playground

The fastest way to experiment is in the visual playground at **[waveformstudio.app](https://www.waveformstudio.app/)**. Compare providers side-by-side, test different voices, and hear the results instantly.

### Use Programmatically

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

## API Reference

### Method: `synthesize()`

Generate speech from text and return audio bytes.

```python
async def synthesize(
    voice_id: str,                    # Voice ID from provider (get from provider's dashboard/docs)
    text: str,                         # Text to synthesize (supports unified syntax)
    style_guidance: Optional[str] = None,  # Natural language style guidance (provider-specific)
    seed: Optional[float] = None,     # Random seed for reproducibility
    creativity: float = 0.5,          # Creativity/variation (0.0-1.0, default 0.5)
) -> SynthesisResponse
```

**Returns:** `SynthesisResponse` object with:
- `response.audio` - `bytes`: Audio data (MP3, WAV, etc. depending on provider)
- `response.metadata` - `SynthesisMetadata` object containing:
  - `voice_id`: The voice used
  - `model`: Model name
  - `size_bytes`: Audio file size
  - `streaming`: Always `False` for `synthesize()`
  - `duration_seconds`: Audio duration (if available)
  - `sample_rate`: Sample rate in Hz (if available)

**Example:**
```python
response = await provider.synthesize(
    voice_id="voice-123",
    text="Hello! [laugh] (excited) This is amazing!",
    creativity=0.7
)

# Save audio
with open("output.mp3", "wb") as f:
    f.write(response.audio)

# Access metadata
print(f"Generated {response.metadata.size_bytes} bytes")
print(f"Model: {response.metadata.model}")
```

### Method: `synthesize_stream()`

Generate speech with streaming audio chunks (not yet implemented for most providers).

```python
async def synthesize_stream(
    voice_id: str,
    text: str,
    style_guidance: Optional[str] = None,
    seed: Optional[float] = None,
    creativity: float = 0.5,
) -> SynthesisStreamResponse
```

**Returns:** `SynthesisStreamResponse` with `audio` as an `AsyncIterator[bytes]`.

### Getting Voice IDs

**Tip:** Use [Waveform Studio](https://www.waveformstudio.app/) to browse and test voices from all providers in one place.

Voice IDs are provider-specific. Get them from:
- **Cartesia**: [Cartesia Dashboard](https://play.cartesia.ai/voices?tab=Default+Voices)
- **ElevenLabs**: [ElevenLabs Voice Library](https://elevenlabs.io/app/voice-library)
- **Hume**: [Hume Dashboard](https://platform.hume.ai/voices)
- **OpenAI**: [OpenAI Voice Models](https://platform.openai.com/docs/guides/text-to-speech)
- **Google Gemini**: [Google Cloud Console](https://docs.cloud.google.com/text-to-speech/docs/gemini-tts)
- **Inworld**: [Inworld Studio](https://platform.inworld.ai/tts-playground)
- **Orpheus**: Use voice names like `"tara"`, `"dan"`, `"josh"`, `"emma"` (see [Replicate model docs](https://replicate.com/lucataco/orpheus-3b-0.1-ft))

### Error Handling

Providers may raise:
- `ValueError`: Invalid parameters (e.g., missing API key, invalid voice_id)
- `RuntimeError`: API request failed or synthesis error
- `ImportError`: Provider dependencies not installed

```python
try:
    response = await provider.synthesize(voice_id="...", text="...")
except ValueError as e:
    print(f"Invalid input: {e}")
except RuntimeError as e:
    print(f"Synthesis failed: {e}")
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

- [x] Generate proper documentation
- [x] Publish to PyPI as installable package
- [x] Create web playground
- [ ] Streaming support
- [ ] Different lang support
- [ ] CLI interface
- [ ] Auto chunk and re-stitch based on character limit
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

