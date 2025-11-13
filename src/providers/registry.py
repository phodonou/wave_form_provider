"""Provider registry mapping IDs to provider classes."""

from typing import Dict, Type
from .tts_provider import TTSProvider
from .constants import (
    ELEVENLABS,
    INWORLD,
    CARTESIA,
    ORPHEUS,
    OPENAI,
    HUME,
    GOOGLE_GEMINI,
)


PROVIDER_MODULES: Dict[str, str] = {
    ELEVENLABS: "elevenlabs_provider.ElevenLabsProvider",
    INWORLD: "inworld_provider.InworldProvider",
    CARTESIA: "cartesia_provider.CartesiaProvider",
    ORPHEUS: "orpheus_provider.OrpheusProvider",
    OPENAI: "openai_provider.OpenAIProvider",
    HUME: "hume_provider.HumeProvider",
    GOOGLE_GEMINI: "google_gemini_provider.GoogleGeminiProvider",
}


def _load_provider_class(module_path: str) -> Type[TTSProvider]:
    """Lazy-load a provider class from its module path."""
    module_name, class_name = module_path.rsplit(".", 1)
    
    try:
        from importlib import import_module
        module = import_module(f".{module_name}", package="src.providers")
        return getattr(module, class_name)
    except ImportError as e:
        raise ImportError(
            f"Failed to import provider from {module_path}. "
            f"Make sure required dependencies are installed. Error: {e}"
        ) from e


def get_provider(provider_id: str, **kwargs) -> TTSProvider:
    """
    Get a provider instance by ID.
    
    Args:
        provider_id: The provider identifier (e.g., "elevenlabs", "openai")
        **kwargs: Keyword arguments to pass to the provider constructor
        
    Returns:
        An instance of the requested provider
        
    Raises:
        ValueError: If provider_id is not registered
        ImportError: If provider dependencies are not installed
    """
    if provider_id not in PROVIDER_MODULES:
        raise ValueError(
            f"Unknown provider: {provider_id}. Available: {list(PROVIDER_MODULES.keys())}"
        )

    provider_class = _load_provider_class(PROVIDER_MODULES[provider_id])
    return provider_class(**kwargs)


def list_providers() -> list[str]:
    """List all available provider IDs."""
    return list(PROVIDER_MODULES.keys())
