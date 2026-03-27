"""FastAI framework package root."""

from .ai_app import AIApp, ai_route
from .client import FastAIClient, create_fastai_client
from .config import (
	AuthConfig,
	FastAIConfig,
	IngestionConfig,
	LLMConfig,
	RetrievalConfig,
	RuntimeConfig,
	VectorStoreConfig,
)
from .plugin import get_fastai_router, mount_fastai_router
from .sdk import FastAI

__all__ = [
	"AIApp",
	"AuthConfig",
	"FastAI",
	"FastAIClient",
	"FastAIConfig",
	"IngestionConfig",
	"LLMConfig",
	"RetrievalConfig",
	"RuntimeConfig",
	"VectorStoreConfig",
	"__version__",
	"ai_route",
	"create_fastai_client",
	"get_fastai_router",
	"mount_fastai_router",
]

__version__ = "0.1.0"
