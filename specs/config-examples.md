# Configuration Examples and Build Flow

## Goal
Provide practical, copy-ready configuration examples with sane defaults for fast onboarding and optional advanced controls for tuning.

## How To Use
1. Copy .env.example to .env.
2. Pick one example profile below.
3. Override only the settings you care about.
4. Keep everything else on defaults.

## SDK Config Object Style (Developer-First)
Use this style when you want configuration in code with typing and autocomplete.

```python
from fastai import FastAI, FastAIConfig
from fastai.config import RuntimeConfig, VectorStoreConfig, RetrievalConfig, IngestionConfig, LLMConfig

sdk = FastAI(
	config=FastAIConfig(
		runtime=RuntimeConfig(profile="balanced"),
		vector_store=VectorStoreConfig(backend="pgvector", namespace="default"),
		retrieval=RetrievalConfig(top_k=5, num_candidates=50, min_score=0.0),
		ingestion=IngestionConfig(recursive=True, max_files=10000, failure_policy="continue"),
		llm=LLMConfig(provider="openai", model="gpt-4.1-mini", embedding_model="text-embedding-3-small"),
	)
)

sdk.add_data("docs/")
result = sdk.ask("What is our refund policy?")
```

What this gives you:
1. Typed config in application code.
2. Minimal env dependence for non-secret settings.
3. Same defaults-first behavior as env configuration.

## SDK Constructor Examples
These are the constructors to expose in the SDK surface.

### Constructor 1: FastAI()
Use full defaults and environment resolution.

```python
from fastai import FastAI

sdk = FastAI()
```

Best for:
1. Quick local start.
2. Teams relying on .env and profile defaults.

### Constructor 2: FastAI(config=FastAIConfig(...))
Use typed config objects with explicit overrides in code.

```python
from fastai import FastAI, FastAIConfig
from fastai.config import RuntimeConfig, VectorStoreConfig, LLMConfig

sdk = FastAI(
	config=FastAIConfig(
		runtime=RuntimeConfig(profile="balanced"),
		vector_store=VectorStoreConfig(backend="pgvector"),
		llm=LLMConfig(model="gpt-4.1-mini"),
	)
)
```

Best for:
1. App-owned configuration.
2. Strong typing and autocomplete.

### Constructor 3: FastAI.from_env()
Force explicit env-only initialization path.

```python
from fastai import FastAI

sdk = FastAI.from_env()
```

Best for:
1. Operational parity with container environments.
2. Twelve-factor style deployments.

### Constructor 4: FastAI.from_profile(profile, **overrides)
Start from a preset (dev, balanced, quality, latency) and override selected values.

```python
from fastai import FastAI

sdk = FastAI.from_profile(
	profile="quality",
	vector_backend="qdrant",
	model="gpt-4.1-mini",
)
```

Best for:
1. Simple tuning with predictable behavior.
2. Teams who want profile-driven defaults.

### Constructor 5: FastAI.for_pgvector(...)
Backend convenience constructor for pgvector.

```python
from fastai import FastAI

sdk = FastAI.for_pgvector(
	dsn="postgresql+psycopg://fastai:fastai@db:5432/fastai",
	model="gpt-4.1-mini",
)
```

### Constructor 6: FastAI.for_qdrant(...)
Backend convenience constructor for qdrant.

```python
from fastai import FastAI

sdk = FastAI.for_qdrant(
	url="http://localhost:6333",
	collection="fastai_chunks",
	model="gpt-4.1-mini",
)
```

### Constructor 7: FastAI.for_mongodb_atlas(...)
Backend convenience constructor for MongoDB Atlas Vector Search.

```python
from fastai import FastAI

sdk = FastAI.for_mongodb_atlas(
	uri="mongodb+srv://<user>:<pass>@cluster.mongodb.net/",
	database="fastai",
	collection="chunks",
	model="gpt-4.1-mini",
)
```

Constructor precedence:
1. Explicit constructor arguments
2. SDK config object fields
3. Environment variables
4. Profile defaults
5. Built-in defaults

## Example A: Minimal Local Setup (Default pgvector)
Use this when you want to start quickly with minimal decisions.
In this mode, the only primary choices are DB backend and generation model.

```env
FASTAI_CONFIG_PROFILE=balanced

# Choice 1: database backend
FASTAI_VECTOR_BACKEND=pgvector

# Choice 2: generation model
FASTAI_LLM_PROVIDER=openai
FASTAI_LLM_MODEL=gpt-4.1-mini

# Required credential for provider
OPENAI_API_KEY=replace_me
```

What this gives you:
1. Fast bootstrap by setting only backend and model.
2. Stable answer and sources output contract.
3. Retrieval, ingestion, and embedding settings come from defaults/profile.

## Example B: Qdrant with Quality Bias
Use this when you already run Qdrant and want higher retrieval quality.

```env
FASTAI_CONFIG_PROFILE=quality
FASTAI_VECTOR_BACKEND=qdrant
FASTAI_VECTOR_DIMENSION=1536
FASTAI_VECTOR_NAMESPACE=support-kb

QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=support_chunks
QDRANT_DISTANCE=cosine
QDRANT_TIMEOUT_SEC=15
QDRANT_PREFER_GRPC=true

FASTAI_RETRIEVAL_TOP_K=8
FASTAI_RETRIEVAL_NUM_CANDIDATES=200
FASTAI_MAX_CONTEXT_TOKENS=4000

FASTAI_LLM_PROVIDER=openai
FASTAI_LLM_MODEL=gpt-4.1-mini
FASTAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=replace_me
```

What this gives you:
1. Better recall from a larger candidate pool.
2. More context in generation.
3. Higher latency/cost tradeoff accepted.

## Example C: MongoDB Atlas with Latency Bias
Use this when data is already in MongoDB and fast responses are prioritized.

```env
FASTAI_CONFIG_PROFILE=latency
FASTAI_VECTOR_BACKEND=mongodb_atlas
FASTAI_VECTOR_DIMENSION=1536
FASTAI_VECTOR_NAMESPACE=default

MONGODB_URI=mongodb+srv://<user>:<pass>@cluster0.mongodb.net/
MONGODB_DATABASE=fastai
MONGODB_VECTOR_COLLECTION=chunks
MONGODB_VECTOR_INDEX_NAME=vector_index
MONGODB_VECTOR_NUM_CANDIDATES=80
MONGODB_VECTOR_SIMILARITY=cosine

FASTAI_RETRIEVAL_TOP_K=3
FASTAI_MAX_CONTEXT_TOKENS=1800

FASTAI_LLM_PROVIDER=openai
FASTAI_LLM_MODEL=gpt-4.1-mini
FASTAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=replace_me
```

What this gives you:
1. Mongo-native storage path.
2. Lower response latency profile.
3. Conservative context and retrieval defaults.

## Example D: Strict Ingestion Policy
Use this for highly controlled corpora where ingest failures should stop the pipeline.

```env
FASTAI_INGESTION_RECURSIVE=true
FASTAI_INGESTION_MAX_FILES=2000
FASTAI_INGESTION_INCLUDE_GLOBS=**/*.txt,**/*.pdf
FASTAI_INGESTION_EXCLUDE_GLOBS=**/.git/**,**/node_modules/**,**/archive/**
FASTAI_INGESTION_FAILURE_POLICY=fail_fast
FASTAI_INGESTION_DEDUPE_MODE=checksum_path

FASTAI_CHUNK_SIZE_TOKENS=450
FASTAI_CHUNK_OVERLAP_TOKENS=60
```

What this gives you:
1. Deterministic ingestion scope.
2. Immediate halt on extraction/indexing errors.
3. Better control over chunking quality.

Validated ingestion control values:
1. FASTAI_INGESTION_FAILURE_POLICY: continue or fail_fast.
2. FASTAI_INGESTION_DEDUPE_MODE: checksum_path or checksum_only.
3. FASTAI_INGESTION_MAX_FILES: positive integer greater than zero.

## Effective Config Resolution
1. SDK config object override
2. Explicit environment variable override
3. Selected profile defaults (dev, balanced, quality, latency)
4. Built-in framework defaults

## Integration Mode Playbook (How It Actually Feels To Build)

### Mode 1: Library Integration (Least Invasive)
When to choose:
1. You already have FastAPI routes and do not want to move them.
2. You want FastAI to be an internal dependency, not a separate service.

What you write:
```python
from fastapi import FastAPI
from fastai import FastAI

app = FastAPI()
sdk = FastAI.from_profile(profile="balanced", vector_backend="pgvector", model="gpt-4.1-mini")

@app.post("/support/ask")
def support_ask(payload: dict) -> dict:
	return sdk.ask(query=payload["query"], debug=payload.get("debug", False))
```

Why this is good for a developer:
1. You keep your existing endpoint names and middleware.
2. You do not rewrite transport code.
3. You can adopt FastAI route-by-route.

### Mode 2: Router Plugin Integration
When to choose:
1. You want FastAI routes available immediately under a namespace like /ai.
2. You want less handler code in your host app.

What you write:
```python
from fastapi import FastAPI
from fastai import FastAI, mount_fastai_router

app = FastAPI()
sdk = FastAI.for_qdrant(url="http://localhost:6333", collection="fastai_chunks", model="gpt-4.1-mini")
mount_fastai_router(app, sdk=sdk, path="/ai")
```

Why this is good for a developer:
1. FastAI owns its route stack and contracts.
2. Your app just mounts once and moves on.
3. Switching vector backends does not change mounted API shape.

### Mode 3: Sidecar Service Integration
When to choose:
1. You want strict service boundaries and independent scaling.
2. Multiple services should consume the same AI API contract.

What you write in host service:
```python
import requests

def ask_fastai(query: str) -> dict:
	resp = requests.post(
		"http://fastai-sidecar:8000/ask",
		json={"query": query, "debug": False},
		timeout=30,
	)
	resp.raise_for_status()
	return resp.json()
```

Why this is good for a developer:
1. No framework coupling in host code.
2. Independent deploy/rollback for AI behavior.
3. One HTTP contract for all consuming apps.

## Why This Is Credible For Dev Teams
1. Same SDK constructors and config model across all integration modes.
2. Same output contract (`answer`, `sources`, optional `debug`) in every mode.
3. Start with two decisions (DB backend + model), then tune only when needed.
4. Your data stays in your chosen backend (pgvector, qdrant, mongodb atlas).

## End-to-End Developer Flow
1. Copy .env.example to .env.
2. Pick one backend: pgvector, qdrant, or mongodb_atlas.
3. Pick one generation model.
4. Set provider credentials (and backend connection only if non-default environment).
5. Start stack with docker compose.
6. Call add_data(path) to ingest corpus.
7. Execute first /ask query.
8. Inspect answer and sources.
9. Enable debug only during tuning.
10. Tune retrieval, ingestion, and backend-specific knobs only if needed.
11. Freeze chosen profile and overrides for production.

## Build Start Agreement Checklist
1. Config profile strategy approved (dev, balanced, quality, latency).
2. Backend support scope approved (pgvector, qdrant, mongodb_atlas).
3. Ingestion controls approved (recursive, patterns, failure policy, dedupe).
4. Output contract approved (answer, sources, optional debug).
5. Data ownership model approved (all corpus and vectors remain in user-managed stores).
