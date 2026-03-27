# FastAI System Design Document

## 1. Document Purpose
This document is the implementation blueprint for FastAI MVP.
It translates requirements and architecture decisions into concrete system design, interfaces, and execution flows.

## 2. Scope
In scope:
1. AI endpoint abstraction with decorator-based route registration.
2. Ingestion for local text and PDF files.
3. Retrieval-augmented generation pipeline.
4. Provider-agnostic LLM and embeddings integration.
5. HTTP API exposure with answer and sources response.
6. Debug observability outputs for retrieved chunks, context, and final prompt.

Out of scope:
1. Full user auth platform.
2. Billing or usage invoicing.
3. UI dashboards.
4. Multi-service decomposition.

## 3. Design Goals
1. Minimize application code needed to create useful AI endpoints.
2. Enforce modular monolith boundaries to avoid coupling.
3. Keep retrieval deterministic under fixed corpus and parameters.
4. Keep generation provider-agnostic and replaceable.
5. Make pipeline internals observable with low operational complexity.
6. Be Docker-first for local and CI consistency.

## 4. Quality Attributes
1. Modularity: bounded modules with explicit dependency rules.
2. Extensibility: add providers or modules without redesign.
3. Reliability: request-level failures do not crash process.
4. Operability: structured logs and optional tracing.
5. Performance baseline: suitable for interactive use on MVP dataset size.

## 5. High-Level Architecture
The system is a single deployable Python service with internal modules.

Integration architecture principle:
1. FastAI must be adoptable without forcing host application rewrites.
2. Integration mode is a user choice, not a framework constraint.

Supported integration modes:
1. Library mode: host app calls FastAI APIs directly in existing routes.
2. Router plugin mode: host app mounts FastAI router under a namespace path.
3. Sidecar mode: host app calls FastAI over HTTP as a separate service.

Request path:
1. Client sends POST request to AI route.
2. API validates request schema.
3. Retrieval module computes query embedding and fetches top-k chunks.
4. LLM module builds prompt and calls provider adapter.
5. API returns answer and sources.
6. Observability module records debug artifacts.

Ingestion path:
1. Developer calls add_data(path).
2. Ingestion module extracts text from supported files.
3. Text is chunked deterministically.
4. Embeddings are generated and persisted with metadata.

## 6. Runtime Components

## 6.1 App Core
Responsibilities:
1. Initialize FastAPI app.
2. Load settings from environment.
3. Register middleware and exception handlers.
4. Wire modules using composition root.

Key files:
1. app/main.py
2. app/lifecycle.py
3. boot/container.py
4. boot/module_registry.py

## 6.2 API Module
Responsibilities:
1. Define transport contracts and route handlers.
2. Validate request/response schemas.
3. Invoke application use cases.
4. Map internal exceptions to HTTP errors.

Key files:
1. api/http/routers/ai_routes.py
2. api/http/schemas/request.py
3. api/http/schemas/response.py
4. api/http/middleware/exception_handlers.py

## 6.3 Ingestion Module
Responsibilities:
1. Enumerate files from local path.
2. Extract text from txt and PDF.
3. Chunk text with deterministic policy.
4. Request embeddings through adapter.
5. Persist documents/chunks/vectors and metadata.

Internal layers:
1. domain: chunking policies and document invariants.
2. application: ingestion commands and orchestration.
3. infrastructure: file extractors, embedding adapter, repository adapters.

## 6.4 Retrieval Module
Responsibilities:
1. Create query embedding.
2. Retrieve top-k chunks from vector store.
3. Apply ranking and filtering policy.
4. Build context payload for prompt construction.

Internal layers:
1. domain: ranking rules and retrieval constraints.
2. application: retrieval query handlers.
3. infrastructure: vector backend adapters (pgvector, qdrant, mongodb-atlas).

## 6.5 LLM Module
Responsibilities:
1. Build final prompt from system template and context.
2. Call provider via abstraction.
3. Return answer and provider metadata.

Internal layers:
1. domain: prompt policy and generation options.
2. application: generate-answer command handler.
3. infrastructure: LiteLLM-backed provider adapters.

## 6.6 Storage Module
Responsibilities:
1. Persist and fetch documents/chunks.
2. Persist embeddings and metadata.
3. Expose repository interfaces used by ingestion and retrieval.

Storage choice:
1. Default backend is PostgreSQL with pgvector.
2. Bring-your-own vector backend is supported through adapters: pgvector, qdrant, mongodb-atlas.
3. Metadata persistence remains developer-controlled; no framework-hosted storage is required.

Vector adapter contract:
1. upsert_embeddings(records)
2. similarity_search(query_vector, top_k, min_score)
3. delete_by_document(document_id)

## 6.7 Observability Module
Responsibilities:
1. Structured request logs.
2. Debug payload assembly for opted-in requests.
3. Optional tracing instrumentation.

Debug output fields:
1. retrieved_chunks
2. context
3. final_prompt

## 7. Detailed Data Model

## 7.1 Core Entities
1. Document
- id: string
- path: string
- checksum: string
- source_type: enum(local_file)
- created_at: datetime

2. Chunk
- id: string
- document_id: string
- index: int
- text: string
- token_count: int
- metadata: json

3. Embedding
- chunk_id: string
- vector: vector(n)
- model: string
- created_at: datetime

4. RouteDefinition
- route: string
- handler_name: string
- options: json

5. QueryTrace
- request_id: string
- route: string
- retrieved_chunk_ids: string[]
- context: text
- final_prompt: text
- created_at: datetime

## 7.2 Database Tables (MVP)
1. documents
2. chunks
3. embeddings
4. route_definitions
5. query_traces (optional persistence, can be log-only in initial cut)

## 8. Public API Design

## 8.1 Developer-Facing Framework API
1. app = AIApp(settings=...)
2. app.add_data(path: str)
3. @app.ai_route(path: str)
4. app.run(...)

SDK facade API:
1. sdk = FastAI(config=FastAIConfig(...))
2. sdk.add_data(path: str)
3. sdk.ask(query: str, debug: bool = false)
4. sdk.mount(app, path: str = "/ai")

Typed config object model:
1. FastAIConfig
2. RuntimeConfig
3. VectorStoreConfig (with backend-specific nested config)
4. RetrievalConfig
5. IngestionConfig
6. LLMConfig
7. AuthConfig

Contract notes:
1. add_data accepts local file or directory path.
2. Unsupported file types are skipped with warnings.
3. ai_route handlers accept query-like inputs and delegate to framework pipeline.
4. Config object usage is first-class and intended for application code.

## 8.2 HTTP API Contract
Request:
1. Method: POST
2. Body: { "query": "...", "debug": false }

Response:
1. answer: string
2. sources: array of source objects with id and text
3. debug: optional object included only when debug=true

Error model:
1. 400 for invalid payload.
2. 401/403 for auth failures only when request auth mode is enabled.
3. 500 for internal pipeline failures.
4. 502 for upstream provider failures.

## 8.3 Integration Contracts
Library mode contract:
1. Host app can instantiate FastAI client/app object from framework package.
2. Host app keeps existing route layout and calls FastAI from handler.

Router plugin contract:
1. Framework exposes mountable router.
2. Host app chooses mount path (for example /ai).

Sidecar contract:
1. Framework runs as independent HTTP service.
2. Host app consumes API contract defined in specs/api-contract.yaml.

Cross-mode invariants:
1. Query input shape is consistent.
2. Response shape includes answer and sources.
3. Debug payload is optional and opt-in.

## 8.4 Prompt Template Contract
Default prompt section order is fixed:
1. system_instructions
2. route_instructions
3. retrieved_context
4. user_query

Template variables:
1. route_name
2. query
3. context
4. max_context_tokens

Determinism rule:
1. Identical inputs must render byte-equivalent prompt text.

## 9. Key Flows

## 9.1 Ingestion Flow
1. Validate input path exists.
2. Discover supported files.
3. Extract raw text per file.
4. Normalize and chunk text.
5. Generate embeddings in batches.
6. Persist documents/chunks/embeddings.
7. Emit ingestion summary with counts and failures.

## 9.2 Query Flow
1. Validate request payload.
2. Resolve route configuration.
3. Embed query.
4. Retrieve top-k candidate chunks.
5. Rank/filter chunks.
6. Build context string.
7. Construct final prompt.
8. Call LLM provider adapter.
9. Map output into answer plus sources.
10. Optionally attach debug payload.

## 9.3 End User Setup Flow (Existing Project)
1. Install FastAI package in host project.
2. Configure provider credentials and retrieval settings via environment.
3. Add ingestion source path (local txt/pdf).
4. Choose integration mode (library, plugin, or sidecar).
5. Wire one initial endpoint/use case.
6. Validate response quality using answer plus sources.
7. Enable debug mode during tuning only.

## 10. Deterministic Retrieval Strategy
Determinism controls:
1. Stable chunking policy and ordering.
2. Fixed top-k and rank parameters per route.
3. Stable filter pipeline.
4. Stable context assembly ordering.

Non-deterministic area:
1. Final LLM generation.

## 11. Configuration Model
Configuration sources:
1. Environment variables.
2. Optional .env file for local development.

Configuration strategy:
1. Defaults-first: framework runs with minimal required settings.
2. Preset profiles: sane grouped defaults for common use (dev, balanced, quality, latency).
3. Explicit overrides: any specific variable can override profile defaults.
4. SDK config object values are the highest-precedence application-level overrides.

Minimal bootstrap contract:
1. Choose vector backend.
2. Choose generation model.
3. Provide provider credential.
4. All other settings use profile and built-in defaults unless overridden.

Override precedence:
1. SDK config object value
2. Explicit environment variable
3. Selected profile value
4. Built-in framework default

Config groups:
1. Server: host, port, workers.
2. Database: DSN and pool settings.
3. Embeddings: model name and batch size.
4. Retrieval: top_k, max_context_tokens, vector backend selector.
5. LLM: provider, model, timeout.
6. Auth: mode (disabled or api_key) and key material.
7. Observability: log level, tracing toggle.
8. Ingestion: recursive mode, include/exclude patterns, file limits, failure policy.
9. Vector backend advanced: backend-specific tuning options.

### 11.1 Vector Backend Tuning Options
Pgvector options (optional):
1. Schema and table names.
2. Index type selection (ivfflat or hnsw when supported).
3. Search tuning parameters.

Qdrant options (optional):
1. Collection name.
2. Distance metric.
3. Request timeout and transport settings.

MongoDB Atlas Vector Search options (optional):
1. Database and collection names.
2. Vector index name.
3. numCandidates and similarity settings.

### 11.2 Ingestion Tuning Options
1. Recursive discovery toggle.
2. Include and exclude glob patterns.
3. Max files per run.
4. Per-file failure policy: continue or fail_fast.
5. Deduplication mode by checksum and path.

## 12. Error Handling and Resilience
1. Use typed domain exceptions per module.
2. Translate exceptions once at API boundary.
3. Wrap provider/network calls with timeout and retry policy (MVP default: max_retries=2, exponential backoff with jitter, 0.5s base delay, retry on timeout/429/5xx).
4. Return clear, actionable error messages for missing API keys.
5. Continue ingestion on per-file failures and report partial results.

## 13. Security Baseline
1. Keep provider keys in environment variables or Docker secrets.
2. Never log secrets or full authorization headers.
3. Support mode-driven request auth: disabled by default, api_key when enabled.
4. Validate and bound request sizes.
5. Preserve user data ownership: corpus, embeddings, and metadata stay in user-managed stores.

## 14. Observability Design
1. Structured logs include request_id, route, latency_ms, provider, token_estimates.
2. Debug payload is opt-in per request and excluded by default.
3. Trace spans around extraction, embedding, retrieval, prompt-build, generation.
4. Metrics candidates:
- request_count
- request_latency_ms
- retrieval_latency_ms
- llm_latency_ms
- ingestion_files_processed

## 15. Testing Strategy
1. Unit tests per module domain/application logic.
2. Integration tests with PostgreSQL + pgvector in Docker.
3. Contract tests for HTTP schemas and provider adapters.
4. Golden tests for deterministic retrieval output ordering.
5. Failure tests for provider timeouts and invalid keys.

## 16. Deployment and Runtime Model
1. Build app image with multi-stage Dockerfile.
2. Run app and db via Docker Compose in development.
3. Apply migrations before app startup in CI/CD.
4. Expose health endpoint for readiness/liveness.

## 17. Tradeoffs and Risks
Tradeoffs:
1. PostgreSQL + pgvector favors operational simplicity over specialized vector features.
2. pypdf may underperform on complex layouts.
3. LiteLLM abstraction may limit access to provider-specific advanced features.

Risks and mitigation:
1. Risk: retrieval quality variability.
- Mitigation: add ranking policy tuning and golden retrieval tests.
2. Risk: prompt size overrun.
- Mitigation: strict context token budget and truncation policy.
3. Risk: provider outages.
- Mitigation: retries, fallback provider adapter optional in future.

## 18. Phase Plan
Phase 1:
1. App bootstrap, API skeleton, config, health endpoint.
2. Storage schema and migrations.
3. Ingestion for txt and PDF.

Phase 2:
1. Retrieval pipeline and deterministic context builder.
2. LLM provider adapter and response contract.
3. Debug observability payload.

Phase 3:
1. Auto docs polish and contract tests.
2. Integration and performance baseline validation.
3. Packaging and release hardening.

## 19. MVP Implementation Defaults (Locked)
1. Default embedding model for MVP is text-embedding-3-small unless explicitly overridden.
2. Provider retry policy defaults to max_retries=2 with exponential backoff and jitter.
3. Query traces are log-only in MVP; database persistence is deferred.
4. Request auth interface is mode-driven via FASTAI_API_AUTH_MODE with values disabled or api_key.
5. Router plugin public helper is mount_fastai_router(app, path="/ai") for MVP.
6. Default vector backend is pgvector; qdrant and mongodb-atlas are supported via adapters.
7. Default configuration profile is balanced with deterministic defaults.
8. Default ingestion policy is recursive=true, continue_on_error=true, and no explicit include/exclude filters.

## 20. Acceptance Criteria for This Design
This design is accepted when:
1. Every FR and NFR in requirements.md maps to a component or flow in this document.
2. Every module responsibility is unambiguous.
3. API contracts and debug behavior are explicit.
4. Implementation can begin without structural ambiguity.

## 21. Implementation Run Governance
This section defines how engineering runs execute against this design.

### 21.1 Run Modes
Every run must declare one mode before changes:
1. implement
2. stabilize
3. investigate
4. cleanup

Mode rules:
1. Implement runs add one scoped feature plus tests and validation.
2. Stabilize runs restore working state using minimal fixes.
3. Investigate runs are read-only unless explicit approval is provided.
4. Cleanup runs delete only explicitly requested assets.

### 21.2 Required Run Contract
Before changes:
1. objective
2. mode
3. exact steps to run
4. success criteria

After changes:
1. what changed
2. evidence (command and validation summary)
3. residual risk
4. next safe step

### 21.3 Required Execution Order
Default run sequence:
1. health checks
2. dependency readiness
3. bootstrap/provisioning
4. feature action
5. verification

Stop condition:
1. If any step fails, stop and report blocker before continuing.

### 21.4 Verification Completion Gate
A run is complete only when all are true:
1. Service health checks pass.
2. Target action succeeds.
3. User-visible behavior works.
4. No new blocking error appears in relevant logs.

### 21.5 Change Scope and Safety
1. Keep edits to the smallest file set possible.
2. Prefer patching existing orchestration scripts over creating parallel paths.
3. Do not combine destructive cleanup with feature work in one run unless explicitly requested.
4. If project state is inconsistent, stop and report.
