# FastAI MVP Execution Tasks

## How to Use This File
1. Execute tasks strictly in order.
2. Do not start a task until all listed dependencies are complete.
3. Mark each task as done only when all done criteria are satisfied.
4. If a task fails, resolve blockers before moving ahead.
5. Preserve non-invasive adoption: implementation must support library, router plugin, and sidecar modes.

## Run Contract (Required Per Task Run)
Before making changes, record:
1. Objective for this run (single objective only).
2. Mode: implement, stabilize, investigate, or cleanup.
3. Exact commands to run.
4. Success criteria for this run.

After changes, record:
1. What changed.
2. Evidence (command summary and validation results).
3. Residual risk.
4. Next safe step.

## Execution Order (Required)
For each task run, execute this order:
1. Health checks.
2. Dependency readiness.
3. Bootstrap or provisioning.
4. Feature action.
5. Verification.

If any step fails, stop and report before continuing.

## Verification Standard (Task Completion Gate)
A task run is complete only when all are true:
1. Service health checks pass.
2. Target action succeeds.
3. User-visible behavior works.
4. No new blocking error appears in relevant logs.

## Safety Guardrails (Required)
1. Never run destructive commands unless explicitly requested.
2. Do not combine destructive cleanup and feature implementation in one run unless explicitly requested.
3. If deleting assets, record recovery instructions before deletion.
4. Do not assume UI-visible state equals backend state; verify both.

## Access and Isolation Checks (Conditional)
Apply this section when features include roles, tenants, or scoped data visibility.

Required checks:
1. Access check: scope A cannot read scope B data.
2. Visibility check: scope A cannot discover restricted assets of scope B.
3. Verification must include both API-level and user-visible route-level evidence.

Completion note:
1. Any task that introduces scoped access controls must include tests for both access and visibility checks.

## Communication Template (Run Updates)
Use this update template for task run progress:
1. current objective
2. current step
3. result
4. next step

If blocked, report:
1. blocker
2. impact
3. one recommended action

## Recovery Commands Template
Record project-specific recovery commands here before major operational changes.

1. full bootstrap command
2. stack reset command
3. service health-check command

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
1. App starts with env and SDK-config-driven resolution.
2. Health endpoint returns success.

### T-004A Implement Defaults-First Config Profiles
Status: [ ]

Objective:
Provide simple presets for most developers and explicit overrides for advanced tuning.

Dependencies:
T-004

Work:
1. Add profile selector (dev, balanced, quality, latency).
2. Implement precedence: explicit env > profile default > built-in default.
3. Add startup config summary showing effective values and overridden keys.

Done criteria:
1. App runs with minimal config using default profile.
2. Overridden values deterministically replace profile defaults.
3. Profile behavior is test-covered.

### T-005 Implement HTTP API Base Layer
Status: [x]

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
Status: [x]

Objective:
Expose framework surface: AIApp, ai_route decorator, add_data placeholder, and integration-ready public contracts.

Dependencies:
T-004, T-005

Work:
1. Add AIApp class.
2. Add ai_route decorator registration.
3. Add route registry and runtime binding.
4. Add add_data method stub with clear NotImplemented path.
5. Define stable public interfaces for library and router plugin consumption.

Done criteria:
1. Developer can define a route with decorator.
2. Route appears in API docs.
3. Public API is usable from an existing host app without replacing host routing.

### T-006D Implement FastAI SDK Config Object Facade
Status: [ ]

Objective:
Expose a developer-first SDK surface that accepts typed config objects.

Dependencies:
T-004A, T-006

Work:
1. Add FastAI facade class wrapping core runtime behaviors.
2. Add typed config objects for runtime, vector backend, retrieval, ingestion, llm, and auth.
3. Implement config precedence: constructor args > config object > env > profile > built-in default.
4. Add SDK usage examples for library, mount, and query calls.
5. Implement and document constructor matrix:
	- FastAI()
	- FastAI(config=FastAIConfig(...))
	- FastAI.from_env()
	- FastAI.from_profile(profile, **overrides)
	- FastAI.for_pgvector(...)
	- FastAI.for_qdrant(...)
	- FastAI.for_mongodb_atlas(...)

Done criteria:
1. Developer can initialize FastAI(config=FastAIConfig(...)) with partial config objects.
2. SDK behavior is equivalent to env-based setup under matching values.
3. Constructor matrix behavior and precedence are covered by tests.
4. Minimal onboarding path works by setting backend and model plus provider credential.

### T-006A Implement Library Integration Mode
Status: [ ]

Objective:
Allow existing services to call FastAI from existing endpoints with minimal code changes.

Dependencies:
T-006

Work:
1. Add library/client entrypoint for host application route handlers.
2. Keep request and response contracts consistent with framework-native routes.
3. Add minimal example for host app integration.

Done criteria:
1. Existing FastAPI route can call FastAI logic without route migration.
2. Response contains answer and sources contract.

### T-006B Implement Router Plugin Mode
Status: [ ]

Objective:
Allow host apps to mount FastAI routes under a chosen namespace path.

Dependencies:
T-006

Work:
1. Expose mountable router/plugin entrypoint.
2. Support configurable mount path (for example /ai).
3. Add host app mounting example.

Done criteria:
1. Host app can mount FastAI router without replacing existing routes.
2. Mounted route returns answer and sources contract.

### T-006C Validate Sidecar Integration Mode
Status: [ ]

Objective:
Ensure FastAI can be consumed as an independent HTTP service by external host apps.

Dependencies:
T-005, T-006

Work:
1. Validate API compatibility with specs/api-contract.yaml.
2. Add example client call from external service context.
3. Verify cross-service error mapping behavior.

Done criteria:
1. Sidecar service is callable from another app over HTTP.
2. Response and error contracts match API specification.

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
4. Add vector store adapter interface with common operations.

Done criteria:
1. Repository integration tests pass for create/read flows.
2. Rollback behavior works on simulated failure.
3. Vector adapter contract tests pass against default backend.

### T-009A Implement Vector Backend Adapters
Status: [ ]

Objective:
Support bring-your-own vector databases through interchangeable adapters.

Dependencies:
T-009

Work:
1. Implement pgvector adapter.
2. Implement qdrant adapter.
3. Implement mongodb atlas vector search adapter.
4. Add backend selector wiring from configuration.

Done criteria:
1. Same ingest and query flow works across all supported backends.
2. No API contract changes are required when switching backend.

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

### T-010A Implement Ingestion Configuration Controls
Status: [ ]

Objective:
Expose ingestion tuning for advanced users while preserving safe defaults.

Dependencies:
T-010

Work:
1. Add recursive toggle, include/exclude globs, and max file limit.
2. Add failure policy (continue or fail_fast).
3. Add dedupe mode controls.

Done criteria:
1. Defaults work without extra tuning.
2. Advanced options are validated and documented.
3. Ingestion behavior is deterministic under fixed config.

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
2. Run similarity search via selected vector adapter.
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
1. Define default prompt template sections in fixed order: system_instructions, route_instructions, retrieved_context, user_query.
2. Add prompt assembly service.
3. Ensure deterministic prompt ordering and sectioning.

Done criteria:
1. Prompt includes expected sections in stable order.
2. Prompt assembly unit tests pass.
3. Template variables and section order are documented.

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
4. Preserve cross-mode response invariants (library, plugin, sidecar).
5. Enforce auth-mode behavior parity with env contract and API contract.

Done criteria:
1. POST request returns answer and sources contract.
2. End-to-end integration test passes.
3. Contract parity is validated across all integration modes.
4. Auth mode tests cover disabled and api_key behavior.

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
5. Add integration-mode tests for library, plugin, and sidecar flows.

Done criteria:
1. All core flows and failure paths have automated tests.
2. Test suite is runnable in Docker-based CI.
3. Integration-mode parity tests pass.

### T-025 Finalize API Docs and Developer Quickstart
Status: [ ]

Objective:
Make MVP usable by external developers with minimal confusion.

Dependencies:
T-020, T-024

Work:
1. Validate OpenAPI output for AI routes.
2. Add quickstart snippets for library, router plugin, and sidecar setup.
3. Document env vars and docker-first startup.

Done criteria:
1. New developer can run stack and hit /ask successfully.
2. Docs match actual runtime behavior.
3. Non-invasive integration paths are documented with copyable commands.

### T-026 MVP Readiness Review
Status: [ ]

Objective:
Validate all MVP requirements and close remaining gaps.

Dependencies:
T-025

Work:
1. Verify completion against specs/requirements.md MVP exit criteria.
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
