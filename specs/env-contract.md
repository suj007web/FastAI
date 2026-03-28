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
| FASTAI_CONFIG_PROFILE | No | balanced | dev | Defaults profile: dev, balanced, quality, latency. |
| FASTAI_HOST | No | 0.0.0.0 | 0.0.0.0 | API bind host. |
| FASTAI_PORT | No | 8000 | 8000 | API bind port. |
| FASTAI_LOG_LEVEL | No | INFO | DEBUG | Log verbosity. |
| FASTAI_REQUEST_TIMEOUT_SEC | No | 60 | 45 | Request timeout baseline. |
| FASTAI_ENABLE_TRACING | No | false | true | Enable OpenTelemetry spans. |
| FASTAI_DEBUG_PAYLOAD_ENABLED | No | true | true | Allow debug output when requested. |
| FASTAI_DB_DSN | No | postgresql+psycopg://fastai:fastai@db:5432/fastai | postgresql+psycopg://user:pass@db:5432/fastai | Database DSN (override for external DB). |
| FASTAI_DB_POOL_SIZE | No | 10 | 20 | SQLAlchemy pool size. |
| FASTAI_DB_MAX_OVERFLOW | No | 20 | 30 | SQLAlchemy max overflow. |
| FASTAI_VECTOR_BACKEND | No | pgvector | pgvector | Vector backend selector: pgvector, qdrant, mongodb_atlas. |
| FASTAI_VECTOR_DIMENSION | No | 1536 | 1536 | Embedding vector size for vector indexes. |
| FASTAI_VECTOR_NAMESPACE | No | default | tenant-a | Logical namespace for multi-tenant separation in vector stores. |
| FASTAI_RETRIEVAL_TOP_K | No | 5 | 8 | Number of chunks retrieved per query. |
| FASTAI_RETRIEVAL_MIN_SCORE | No | 0.0 | 0.15 | Optional score threshold. |
| FASTAI_RETRIEVAL_NUM_CANDIDATES | No | 50 | 200 | Candidate pool size before final ranking. |
| FASTAI_MAX_CONTEXT_TOKENS | No | 3000 | 4000 | Max context token budget. |
| FASTAI_CHUNK_SIZE_TOKENS | No | 500 | 600 | Chunk size in tokens. |
| FASTAI_CHUNK_OVERLAP_TOKENS | No | 50 | 80 | Chunk overlap in tokens. |
| FASTAI_INGESTION_RECURSIVE | No | true | false | Enable recursive directory traversal. |
| FASTAI_INGESTION_MAX_FILES | No | 10000 | 2000 | Maximum files processed in one run. |
| FASTAI_INGESTION_INCLUDE_GLOBS | No | - | **/*.txt,**/*.pdf | Optional include patterns (comma-separated). |
| FASTAI_INGESTION_EXCLUDE_GLOBS | No | - | **/.git/**,**/node_modules/** | Optional exclude patterns (comma-separated). |
| FASTAI_INGESTION_FAILURE_POLICY | No | continue | fail_fast | continue or fail_fast for per-file errors. |
| FASTAI_INGESTION_DEDUPE_MODE | No | checksum_path | checksum_only | Deduping policy for repeated ingestion. |
| FASTAI_INGESTION_WATCH_DOCS | No | false | true | Enable docs folder change watcher that auto-runs ingestion. |
| FASTAI_INGESTION_WATCH_PATH | No | docs | knowledge | Folder watched for file additions/changes/deletions. |
| FASTAI_INGESTION_WATCH_INTERVAL_SEC | No | 2.0 | 1.0 | Polling interval (seconds) for docs watcher. |
| FASTAI_INGESTION_WATCH_DEBOUNCE_SEC | No | 1.0 | 0.5 | Minimum interval (seconds) between auto-ingestion runs. |
| FASTAI_LLM_PROVIDER | No | openai | openai | Active provider key for adapter routing. |
| FASTAI_LLM_MODEL | Yes | - | gpt-4.1-mini | Generation model name (primary model choice). |
| FASTAI_EMBEDDING_MODEL | No | text-embedding-3-small | text-embedding-3-small | Embedding model name. |
| FASTAI_LLM_TIMEOUT_SEC | No | 30 | 45 | Upstream provider timeout. |
| FASTAI_LLM_MAX_RETRIES | No | 2 | 3 | Provider retry attempts. |
| FASTAI_API_AUTH_MODE | No | disabled | api_key | Request auth mode: disabled or api_key. |
| FASTAI_API_KEY | No | - | local-dev-key | Request API key when auth mode is api_key. |
| QDRANT_URL | Conditional | - | http://localhost:6333 | Required when FASTAI_VECTOR_BACKEND=qdrant. |
| QDRANT_API_KEY | Conditional | - | qdr_... | Optional or required based on Qdrant deployment auth mode. |
| QDRANT_COLLECTION | No | fastai_chunks | support_kb | Qdrant collection name. |
| QDRANT_DISTANCE | No | cosine | dot | Qdrant distance metric. |
| QDRANT_TIMEOUT_SEC | No | 10 | 20 | Qdrant request timeout. |
| QDRANT_PREFER_GRPC | No | false | true | Prefer gRPC transport when available. |
| MONGODB_URI | Conditional | - | mongodb+srv://... | Required when FASTAI_VECTOR_BACKEND=mongodb_atlas. |
| MONGODB_DATABASE | Conditional | - | fastai | Required when FASTAI_VECTOR_BACKEND=mongodb_atlas. |
| MONGODB_VECTOR_COLLECTION | Conditional | - | chunks | Required when FASTAI_VECTOR_BACKEND=mongodb_atlas. |
| MONGODB_VECTOR_INDEX_NAME | No | vector_index | docs_vector_idx | Atlas vector index name. |
| MONGODB_VECTOR_NUM_CANDIDATES | No | 100 | 250 | Atlas vector search candidate count. |
| MONGODB_VECTOR_SIMILARITY | No | cosine | dotProduct | Atlas vector similarity mode. |
| PGVECTOR_SCHEMA | No | public | fastai | Schema name for pgvector tables. |
| PGVECTOR_EMBEDDINGS_TABLE | No | embeddings | kb_embeddings | Embeddings table name. |
| PGVECTOR_INDEX_TYPE | No | ivfflat | hnsw | Index strategy when supported. |
| PGVECTOR_IVFFLAT_LISTS | No | 100 | 200 | ivfflat lists parameter. |
| PGVECTOR_HNSW_EF_SEARCH | No | 40 | 100 | hnsw ef_search parameter. |
| OPENAI_API_KEY | Conditional | - | sk-... | Required when provider is openai. |
| ANTHROPIC_API_KEY | Conditional | - | sk-ant-... | Required when provider is anthropic. |

## Behavior Semantics
1. FASTAI_CONFIG_PROFILE applies defaults for developers who want minimal setup.
2. Explicit environment variables always override profile defaults.
3. FASTAI_API_AUTH_MODE=disabled means AI routes are accessible without X-API-Key.
4. FASTAI_API_AUTH_MODE=api_key means AI routes require X-API-Key and return 401/403 on auth failures.
5. FASTAI_LLM_MAX_RETRIES controls retry attempts for transient failures (network timeout, HTTP 429, HTTP 5xx).
6. Retry backoff baseline for MVP is exponential with jitter and a 0.5s base delay.
7. FASTAI_VECTOR_BACKEND selects the vector storage adapter without changing application route code.
8. Data ownership remains with the developer-selected backend.
9. FASTAI_INGESTION_FAILURE_POLICY=continue skips failed files and reports counts; fail_fast aborts ingestion immediately.
10. FASTAI_INGESTION_DEDUPE_MODE=checksum_path dedupes by resolved path identity.
11. FASTAI_INGESTION_DEDUPE_MODE=checksum_only dedupes by file content hash.
12. FASTAI_INGESTION_WATCH_DOCS=true enables a polling watcher that triggers add_data when docs files are added, changed, or deleted.
13. FASTAI_INGESTION_WATCH_PATH sets the watched root folder and defaults to docs.
14. FASTAI_INGESTION_WATCH_INTERVAL_SEC and FASTAI_INGESTION_WATCH_DEBOUNCE_SEC tune polling frequency and trigger burst control.

## Minimal Onboarding Contract
For default developer onboarding, change only:
1. FASTAI_VECTOR_BACKEND
2. FASTAI_LLM_MODEL

Plus credentials for the selected provider (for example OPENAI_API_KEY).

## Profile Defaults (Reference)
dev:
1. FASTAI_RETRIEVAL_TOP_K=3
2. FASTAI_MAX_CONTEXT_TOKENS=2000
3. FASTAI_LLM_TIMEOUT_SEC=20

balanced:
1. FASTAI_RETRIEVAL_TOP_K=5
2. FASTAI_MAX_CONTEXT_TOKENS=3000
3. FASTAI_LLM_TIMEOUT_SEC=30

quality:
1. FASTAI_RETRIEVAL_TOP_K=8
2. FASTAI_MAX_CONTEXT_TOKENS=4000
3. FASTAI_LLM_TIMEOUT_SEC=45

latency:
1. FASTAI_RETRIEVAL_TOP_K=3
2. FASTAI_MAX_CONTEXT_TOKENS=1800
3. FASTAI_LLM_TIMEOUT_SEC=15

## Conditional Requirements
1. OPENAI_API_KEY is required when FASTAI_LLM_PROVIDER=openai.
2. ANTHROPIC_API_KEY is required when FASTAI_LLM_PROVIDER=anthropic.
3. FASTAI_API_KEY is required when FASTAI_API_AUTH_MODE=api_key.
4. FASTAI_DB_DSN is required when FASTAI_VECTOR_BACKEND=pgvector.
5. QDRANT_URL is required when FASTAI_VECTOR_BACKEND=qdrant.
6. MONGODB_URI, MONGODB_DATABASE, and MONGODB_VECTOR_COLLECTION are required when FASTAI_VECTOR_BACKEND=mongodb_atlas.

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
