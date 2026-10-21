"""Provider adapters for the video-model-router skill."""
from .base import Provider, ProviderError, VideoRequest, TaskResult
from .seedance import SeedanceProvider
from .agnes import AgnesProvider

PROVIDERS = {
    "seedance": SeedanceProvider(),
    "agnes": AgnesProvider(),
}

__all__ = [
    "Provider", "ProviderError", "VideoRequest", "TaskResult",
    "SeedanceProvider", "AgnesProvider", "PROVIDERS",
]
