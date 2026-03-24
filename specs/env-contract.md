# Environment Contract

## Purpose
Defines all environment variables required or supported by FastAI MVP.

## Rules
1. Required variables must be present at startup.
2. Optional variables must have documented defaults.
3. Unknown variables are ignored unless explicitly consumed.
4. Secret variables must never be logged.

## Environment Variables

| Name | Required | Default | Example | Description |
|---|---|---|---|---|
| FASTAI_ENV | No | development | production | Runtime mode. |
| FASTAI_HOST | No | 0.0.0.0 | 0.0.0.0 | API bind host. |
| FASTAI_PORT | No | 8000 | 8000 | API bind port. |
| FASTAI_LOG_LEVEL | No | INFO | DEBUG | Log verbosity. |
| FASTAI_REQUEST_TIMEOUT_SEC | No | 60 | 45 | Request timeout baseline. |
| FASTAI_ENABLE_TRACING | No | false | true | Enable OpenTelemetry spans. |
| FASTAI_DEBUG_PAYLOAD_ENABLED | No | true | true | Allow debug output when requested. |
| FASTAI_DB_DSN | Yes | - | postgresql+psycopg://user:pass@db:5432/fastai | Database DSN. |
| FASTAI_DB_POOL_SIZE | No | 10 | 20 | SQLAlchemy pool size. |
| FASTAI_DB_MAX_OVERFLOW | No | 20 | 30 | SQLAlchemy max overflow. |
| FASTAI_VECTOR_DIMENSION | Yes | - | 1536 | Embedding vector size for pgvector column. |
| FASTAI_RETRIEVAL_TOP_K | No | 5 | 8 | Number of chunks retrieved per query. |
| FASTAI_RETRIEVAL_MIN_SCORE | No | 0.0 | 0.15 | Optional score threshold. |
| FASTAI_MAX_CONTEXT_TOKENS | No | 3000 | 4000 | Max context token budget. |
| FASTAI_CHUNK_SIZE_TOKENS | No | 500 | 600 | Chunk size in tokens. |
| FASTAI_CHUNK_OVERLAP_TOKENS | No | 50 | 80 | Chunk overlap in tokens. |
| FASTAI_LLM_PROVIDER | Yes | - | openai | Active provider key for adapter routing. |
| FASTAI_LLM_MODEL | Yes | - | gpt-4.1-mini | Generation model name. |
| FASTAI_EMBEDDING_MODEL | Yes | - | text-embedding-3-small | Embedding model name. |
| FASTAI_LLM_TIMEOUT_SEC | No | 30 | 45 | Upstream provider timeout. |
| FASTAI_LLM_MAX_RETRIES | No | 2 | 3 | Provider retry attempts. |
| FASTAI_API_AUTH_MODE | No | disabled | api_key | API auth hook mode. |
| FASTAI_API_KEY | No | - | local-dev-key | Request API key when auth mode is api_key. |
| OPENAI_API_KEY | Conditional | - | sk-... | Required when provider is openai. |
| ANTHROPIC_API_KEY | Conditional | - | sk-ant-... | Required when provider is anthropic. |

## Conditional Requirements
1. OPENAI_API_KEY is required when FASTAI_LLM_PROVIDER=openai.
2. ANTHROPIC_API_KEY is required when FASTAI_LLM_PROVIDER=anthropic.
3. FASTAI_API_KEY is required when FASTAI_API_AUTH_MODE=api_key.

## Startup Validation Requirements
1. App must fail fast if required variables are missing.
2. App must emit a single sanitized config summary at startup.
3. Secret values must be redacted in logs.

## Local Development Example
FASTAI_ENV=development
FASTAI_HOST=0.0.0.0
FASTAI_PORT=8000
FASTAI_LOG_LEVEL=DEBUG
FASTAI_DB_DSN=postgresql+psycopg://fastai:fastai@db:5432/fastai
FASTAI_VECTOR_DIMENSION=1536
FASTAI_RETRIEVAL_TOP_K=5
FASTAI_MAX_CONTEXT_TOKENS=3000
FASTAI_CHUNK_SIZE_TOKENS=500
FASTAI_CHUNK_OVERLAP_TOKENS=50
FASTAI_LLM_PROVIDER=openai
FASTAI_LLM_MODEL=gpt-4.1-mini
FASTAI_EMBEDDING_MODEL=text-embedding-3-small
FASTAI_LLM_TIMEOUT_SEC=30
FASTAI_LLM_MAX_RETRIES=2
OPENAI_API_KEY=replace_me
