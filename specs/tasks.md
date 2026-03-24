# FastAI MVP Execution Tasks

## How to Use This File
1. Execute tasks strictly in order.
2. Do not start a task until all listed dependencies are complete.
3. Mark each task as done only when all done criteria are satisfied.
4. If a task fails, resolve blockers before moving ahead.

## Status Legend
- [ ] Not started
- [x] Completed

## Phase 0: Foundation and Tooling

### T-001 Initialize Python Project Skeleton
Status: [x]

Objective:
Create base Python project with package metadata and minimal app entrypoint.

Dependencies:
None.

Work:
1. Add pyproject.toml with project metadata.
2. Add src package root for fastai.
3. Add minimal app bootstrap file and package init files.

Done criteria:
1. Project installs in editable mode.
2. App module imports without error.

### T-002 Configure Dev Toolchain
Status: [x]

Objective:
Set up linting, formatting, and static typing.

Dependencies:
T-001

Work:
1. Configure Ruff.
2. Configure mypy.
3. Add pytest baseline config.
4. Add scripts or make-like commands for lint/type/test.

Done criteria:
1. Lint command runs successfully.
2. Type-check command runs successfully.
3. Test command executes baseline test suite.

### T-003 Add Docker-First Runtime
Status: [x]

Objective:
Create reproducible local runtime for app and db from day one.

Dependencies:
T-001

Work:
1. Add multi-stage Dockerfile for app.
2. Add docker compose with app and PostgreSQL + pgvector.
3. Add environment template for local development.

Done criteria:
1. docker compose up starts app and db.
2. App is reachable from host.

## Phase 1: Core App and API Shell

### T-004 Implement Configuration and Lifecycle
Status: [ ]

Objective:
Build runtime settings and startup/shutdown lifecycle hooks.

Dependencies:
T-001, T-003

Work:
1. Add typed settings model.
2. Add startup and shutdown event handling.
3. Add health endpoint wiring.

Done criteria:
1. App starts with env-driven config.
2. Health endpoint returns success.

### T-005 Implement HTTP API Base Layer
Status: [ ]

Objective:
Create transport layer with schema validation and error mapping.

Dependencies:
T-004

Work:
1. Add request and response schemas.
2. Add API router structure.
3. Add global exception handling.
4. Add request-id middleware.

Done criteria:
1. Invalid payload returns 400.
2. Unhandled errors map to stable 500 response shape.

### T-006 Implement AIApp Public API Skeleton
Status: [ ]

Objective:
Expose framework surface: AIApp, ai_route decorator, add_data placeholder.

Dependencies:
T-004, T-005

Work:
1. Add AIApp class.
2. Add ai_route decorator registration.
3. Add route registry and runtime binding.
4. Add add_data method stub with clear NotImplemented path.

Done criteria:
1. Developer can define a route with decorator.
2. Route appears in API docs.

## Phase 2: Storage and Migrations

### T-007 Design Initial Database Schema
Status: [ ]

Objective:
Create schema for documents, chunks, embeddings, and route definitions.

Dependencies:
T-003, T-006

Work:
1. Define SQLAlchemy models.
2. Add pgvector column for embeddings.
3. Define indexes for retrieval queries.

Done criteria:
1. Models map cleanly to intended tables.
2. Index plan supports top-k similarity queries.

### T-008 Add Alembic Migration Pipeline
Status: [ ]

Objective:
Version and apply database schema changes.

Dependencies:
T-007

Work:
1. Initialize Alembic.
2. Generate initial migration.
3. Add migration run command for local and CI.

Done criteria:
1. Fresh database can be migrated to latest revision.
2. Migration command is repeatable in Docker workflow.

### T-009 Implement Storage Repositories
Status: [ ]

Objective:
Implement repositories for document/chunk/embedding persistence.

Dependencies:
T-008

Work:
1. Add repository interfaces in shared contracts.
2. Add PostgreSQL repository implementations.
3. Add transaction and session management.

Done criteria:
1. Repository integration tests pass for create/read flows.
2. Rollback behavior works on simulated failure.

## Phase 3: Ingestion Pipeline

### T-010 Implement File Discovery and Validation
Status: [ ]

Objective:
Support local file and directory ingestion for txt and PDF.

Dependencies:
T-006, T-009

Work:
1. Add path validator.
2. Add recursive file discovery.
3. Add supported-file filter and skip warnings.

Done criteria:
1. txt and PDF files are discovered.
2. Unsupported files are skipped without crash.

### T-011 Implement Text Extraction
Status: [ ]

Objective:
Extract normalized text from txt and PDF files.

Dependencies:
T-010

Work:
1. Build txt extractor.
2. Build PDF extractor using pypdf.
3. Normalize whitespace and encoding edge cases.

Done criteria:
1. Extracted text is non-empty for valid sample files.
2. Extraction failures are isolated per-file.

### T-012 Implement Deterministic Chunking
Status: [ ]

Objective:
Chunk extracted text with stable ordering and policy.

Dependencies:
T-011

Work:
1. Define chunk size and overlap policy.
2. Implement token-aware chunking utility.
3. Attach chunk metadata (source path, chunk index, optional page).

Done criteria:
1. Same input always yields same chunk sequence.
2. Chunk metadata is complete for source reconstruction.

### T-013 Implement Embedding Adapter Integration
Status: [ ]

Objective:
Generate embeddings through provider-agnostic adapter.

Dependencies:
T-012

Work:
1. Add embedding adapter interface.
2. Add LiteLLM-backed embedding implementation.
3. Add API key validation and clear error messages.

Done criteria:
1. Embeddings generated for all chunks in test dataset.
2. Missing/invalid key produces actionable error.

### T-014 Complete add_data End-to-End
Status: [ ]

Objective:
Wire discovery, extraction, chunking, embedding, and persistence.

Dependencies:
T-013, T-009

Work:
1. Replace add_data stub with full ingestion pipeline.
2. Add ingestion summary response (processed, skipped, failed counts).
3. Add structured ingestion logs.

Done criteria:
1. add_data indexes txt and PDF corpus end-to-end.
2. Ingestion summary is accurate and test-covered.

## Phase 4: Retrieval and Context Building

### T-015 Implement Query Embedding and Vector Search
Status: [ ]

Objective:
Retrieve top-k relevant chunks for incoming query.

Dependencies:
T-014

Work:
1. Embed user query.
2. Run pgvector similarity search.
3. Return ranked chunk candidates.

Done criteria:
1. Top-k retrieval returns deterministic ordering under fixed params.
2. Retrieval integration test passes on sample corpus.

### T-016 Implement Ranking and Filtering Policy
Status: [ ]

Objective:
Apply relevance thresholds and source filtering before context build.

Dependencies:
T-015

Work:
1. Add score threshold policy.
2. Add deduplication by chunk/document strategy.
3. Finalize sorted candidate list.

Done criteria:
1. Filtering behavior is deterministic and documented.
2. Unit tests cover threshold and dedupe logic.

### T-017 Implement Context Builder
Status: [ ]

Objective:
Build bounded context payload from selected chunks.

Dependencies:
T-016

Work:
1. Add max context token budget.
2. Concatenate chunks in stable order.
3. Preserve source mapping for response citations.

Done criteria:
1. Context remains within configured budget.
2. Source mapping supports answer plus sources output contract.

## Phase 5: LLM Generation and Route Execution

### T-018 Implement LLM Provider Abstraction
Status: [ ]

Objective:
Create provider-agnostic generation interface backed by LiteLLM.

Dependencies:
T-017

Work:
1. Add generation provider interface.
2. Add LiteLLM implementation.
3. Add timeout and retry policy baseline.

Done criteria:
1. Generation works with configured provider model.
2. Provider errors surface as structured internal exceptions.

### T-019 Implement Prompt Construction Pipeline
Status: [ ]

Objective:
Assemble final prompt from query, instructions, and retrieved context.

Dependencies:
T-017, T-018

Work:
1. Define default prompt template.
2. Add prompt assembly service.
3. Ensure deterministic prompt ordering and sectioning.

Done criteria:
1. Prompt includes expected sections in stable order.
2. Prompt assembly unit tests pass.

### T-020 Wire AI Route Runtime End-to-End
Status: [ ]

Objective:
Execute query embedding, retrieval, context build, and generation on API call.

Dependencies:
T-019

Work:
1. Route handler calls orchestration use case.
2. Return answer with sources.
3. Add route-level config options for retrieval parameters.

Done criteria:
1. POST request returns answer and sources contract.
2. End-to-end integration test passes.

## Phase 6: Observability and Reliability

### T-021 Implement Request-Level Debug Output
Status: [ ]

Objective:
Expose retrieved_chunks, context, and final_prompt in debug mode.

Dependencies:
T-020

Work:
1. Add debug flag to request schema.
2. Attach debug payload conditionally.
3. Ensure debug output excludes secrets.

Done criteria:
1. debug=true includes required debug object.
2. debug=false omits debug object.

### T-022 Add Structured Logging and Error Taxonomy
Status: [ ]

Objective:
Provide actionable logs and consistent error classes across modules.

Dependencies:
T-020

Work:
1. Add structured log fields (request_id, route, latency, module).
2. Define module error classes.
3. Map errors to stable API responses.

Done criteria:
1. Logs are parseable and include required fields.
2. Error mapping tests pass.

### T-023 Add Optional OpenTelemetry Instrumentation
Status: [ ]

Objective:
Instrument key spans without making tracing mandatory.

Dependencies:
T-022

Work:
1. Add tracing toggle in config.
2. Instrument ingestion and query pipeline spans.
3. Validate no startup failure when tracing disabled.

Done criteria:
1. App runs with tracing on and off.
2. Core spans emitted when enabled.

## Phase 7: Quality Gates and MVP Exit

### T-024 Build Comprehensive Test Matrix
Status: [ ]

Objective:
Cover unit, integration, contract, and failure-path tests.

Dependencies:
T-021

Work:
1. Add unit tests for domain/application logic.
2. Add integration tests for db and retrieval flows.
3. Add contract tests for API schema and provider interface.
4. Add failure tests for invalid key, provider timeout, bad input.

Done criteria:
1. All core flows and failure paths have automated tests.
2. Test suite is runnable in Docker-based CI.

### T-025 Finalize API Docs and Developer Quickstart
Status: [ ]

Objective:
Make MVP usable by external developers with minimal confusion.

Dependencies:
T-020, T-024

Work:
1. Validate OpenAPI output for AI routes.
2. Add quickstart snippet using AIApp and add_data.
3. Document env vars and docker-first startup.

Done criteria:
1. New developer can run stack and hit /ask successfully.
2. Docs match actual runtime behavior.

### T-026 MVP Readiness Review
Status: [ ]

Objective:
Validate all MVP requirements and close remaining gaps.

Dependencies:
T-025

Work:
1. Verify completion against requirements.md MVP exit criteria.
2. Run full lint, type-check, tests, and integration run.
3. Record known limitations and deferred items.

Done criteria:
1. Every MVP exit criterion is validated.
2. MVP sign-off checklist is complete.

## Optional Post-MVP Backlog (Do Not Block MVP)
1. Add reranker integration.
2. Add provider fallback routing.
3. Add ingestion for additional formats.
4. Add retrieval caching layer.
5. Add persistent query trace storage and analytics.
