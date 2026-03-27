"""FastAI framework package root."""

from .ai_app import AIApp, ai_route
from .config import (
	AuthConfig,
	FastAIConfig,
	IngestionConfig,
	LLMConfig,
	RetrievalConfig,
	RuntimeConfig,
	VectorStoreConfig,
)
from .sdk import FastAI, mount_fastai_router

__all__ = [
	"AIApp",
	"AuthConfig",
	"FastAI",
	"FastAIConfig",
	"IngestionConfig",
	"LLMConfig",
	"RetrievalConfig",
	"RuntimeConfig",
	"VectorStoreConfig",
	"__version__",
	"ai_route",
	"mount_fastai_router",
]

__version__ = "0.1.0"
