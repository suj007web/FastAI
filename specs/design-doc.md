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
3. infrastructure: pgvector search adapter.

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
1. PostgreSQL with pgvector for vectors and metadata in one system.

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

Contract notes:
1. add_data accepts local file or directory path.
2. Unsupported file types are skipped with warnings.
3. ai_route handlers accept query-like inputs and delegate to framework pipeline.

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
2. 401/403 for configured auth hook failures.
3. 500 for internal pipeline failures.
4. 502 for upstream provider failures.

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

Config groups:
1. Server: host, port, workers.
2. Database: DSN and pool settings.
3. Embeddings: model name and batch size.
4. Retrieval: top_k, max_context_tokens.
5. LLM: provider, model, timeout.
6. Observability: log level, tracing toggle.

## 12. Error Handling and Resilience
1. Use typed domain exceptions per module.
2. Translate exceptions once at API boundary.
3. Wrap provider/network calls with timeout and retry policy.
4. Return clear, actionable error messages for missing API keys.
5. Continue ingestion on per-file failures and report partial results.

## 13. Security Baseline
1. Keep provider keys in environment variables or Docker secrets.
2. Never log secrets or full authorization headers.
3. Support optional API key hook for route access control.
4. Validate and bound request sizes.

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

## 19. Open Decisions
1. Exact default embedding model by provider.
2. Initial retry policy parameters for provider calls.
3. Whether query traces are persisted in DB or emitted as logs only in MVP.
4. Route-level auth hook interface shape.

## 20. Acceptance Criteria for This Design
This design is accepted when:
1. Every FR and NFR in requirements.md maps to a component or flow in this document.
2. Every module responsibility is unambiguous.
3. API contracts and debug behavior are explicit.
4. Implementation can begin without structural ambiguity.
