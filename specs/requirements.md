# Requirements Specification: FastAI RAG API Framework

## 1. Objective
Build a Python framework that allows developers to define AI endpoints while the framework automatically executes ingestion, retrieval, and LLM generation.

## 2. Problem Definition
Teams building RAG APIs repeatedly implement the same infrastructure glue:
- Data extraction and chunking
- Embedding generation
- Vector storage and retrieval
- Prompt construction
- LLM provider integration
- API endpoint exposure

This framework standardizes that workflow into a reusable API-first developer experience.

## 3. Target Users
- Backend developers building domain-specific AI APIs
- Teams needing fast RAG endpoint delivery without building full AI infrastructure from scratch

## 4. In-Scope (MVP)
1. Define AI endpoints via a Python decorator.
2. Ingest local text and PDF files from a file or directory path.
3. Build and store vector embeddings for ingested chunks.
4. Retrieve relevant chunks for each query.
5. Construct LLM context from retrieved chunks.
6. Support at least one LLM provider in a provider-agnostic interface.
7. Allow bring-your-own-key provider credentials.
8. Expose HTTP endpoints for AI routes.
9. Return answer plus sources in endpoint response.
10. Expose request-level observability details (retrieved chunks, context, final prompt).
11. Support bring-your-own vector database via pluggable adapters.

## 5. Out-of-Scope (MVP)
1. Full user account management (signup/login/password flows).
2. Billing, metering, invoicing, or subscription logic.
3. UI dashboards.
4. Generic backend platform concerns not required for RAG MVP (for example ORM abstractions).
5. Microservice deployment architecture.

## 6. Ambiguities Resolved (Design Decisions)
The source notes had ambiguous areas. The following decisions remove ambiguity for implementation:

1. Supported ingestion formats in MVP are strictly plain text and PDF only.
2. Ingestion source in MVP is local filesystem paths only (no web crawling, cloud bucket ingestion, or database connectors).
3. Query API input is JSON with a required string field named query.
4. Query API output must always include answer and sources fields.
5. sources must contain at least source id and source text, with optional metadata.
6. Observability is available through a debug flag per request and not always returned by default.
7. Deterministic retrieval means fixed retrieval parameters produce stable retrieved chunks for identical corpus and query.
8. Only LLM generation is probabilistic.
9. Request auth is mode-driven: disabled by default, api_key when explicitly enabled.

## 7. Functional Requirements

### FR-1 App Initialization
- The framework must provide an application object (for example AIApp) to initialize runtime and register AI routes.
- The framework must provide an SDK facade (for example FastAI) that accepts structured config objects.

Acceptance criteria:
- A developer can instantiate the app with default non-secret settings.
- A developer can instantiate the SDK facade with config objects and without direct environment variable access in application code.
- App startup fails fast with actionable validation errors when required environment variables are missing.
- The app can start an HTTP server exposing registered routes when required variables are present.

### FR-2 Route Definition
- The framework must provide a decorator (for example ai_route) to register AI endpoints.

Acceptance criteria:
- A decorated Python function mapped to /ask is callable over HTTP.
- The route accepts a query value and returns a generated response.

### FR-3 Data Ingestion
- The framework must provide add_data(path) for file or directory ingestion.
- The ingestion pipeline must extract text, chunk text, generate embeddings, and persist vectors.

Acceptance criteria:
- Calling add_data on a directory containing .txt and .pdf files indexes content successfully.
- Unsupported file types are skipped with a warning and do not crash ingestion.

### FR-4 Retrieval
- For each query, the framework must embed the query and retrieve top-k relevant chunks from vector storage.

Acceptance criteria:
- Retrieval executes for each AI route request.
- Retrieved chunks are rank-ordered by relevance score.

### FR-4A Bring-Your-Own Vector Database
- The framework must expose a vector store interface and backend selector.
- The framework must support at least these backends in MVP: PostgreSQL pgvector, Qdrant, MongoDB Atlas Vector Search.

Acceptance criteria:
- Developers can configure vector backend through environment variables without changing route code.
- Vector operations use one common contract for upsert and similarity search.
- Response contract (answer, sources, optional debug) remains identical across vector backends.

### FR-5 Context Building
- The framework must construct a context payload from retrieved chunks for LLM input.

Acceptance criteria:
- Context includes chunk text and minimal source metadata.
- Context length is constrained by configurable limits.

### FR-6 LLM Abstraction
- The framework must expose a provider-agnostic LLM interface.
- The framework must support BYOK.

Acceptance criteria:
- Switching provider adapter does not change route decorator usage.
- Missing API key fails with a clear, actionable error.

### FR-7 API Response Contract
- AI route responses must include answer and sources.

Acceptance criteria:
- Successful response JSON schema:
  - answer: string
  - sources: array of source objects
- Each source object includes id and text; metadata is optional.

### FR-8 Observability
- The framework must expose retrieval and prompt internals for debugging.

Acceptance criteria:
- Debug output includes:
  - retrieved_chunks
  - context
  - final_prompt
- Debug output is returned when debug mode is enabled.

### FR-9 Auto Docs
- The framework should auto-generate endpoint documentation for registered routes.

Acceptance criteria:
- Route and request schema are visible in generated API docs.

### FR-10 Non-Invasive Integration Modes
- The framework must support integration without forcing application rewrites.
- The framework must provide at least these adoption paths:
  - Library mode (call from existing endpoint)
  - Router plugin mode (mount FastAI routes)
  - Sidecar mode (HTTP service consumption)

Acceptance criteria:
- Existing FastAPI application can call FastAI in one endpoint without replacing existing routing structure.
- Sidecar mode can be consumed via HTTP from a separate service.
- Core response contract (answer, sources) is consistent across integration modes.

### FR-11 Prompt Template Contract
- The framework must define a default prompt template contract with deterministic section order.

Acceptance criteria:
- Default prompt sections are fixed in this order: system_instructions, route_instructions, retrieved_context, user_query.
- Prompt rendering is deterministic for identical inputs.
- Prompt template variables are documented and test-covered.

### FR-12 Configuration Experience (Defaults First)
- The framework must support a defaults-first configuration pattern across all modules.
- The framework must provide simple baseline defaults for developers who do not want deep tuning.
- The framework must expose advanced options for developers who need precise control.

Acceptance criteria:
- A developer can run with minimal configuration by selecting only vector backend and generation model plus credentials.
- Optional advanced settings are available for vector backend behavior, ingestion behavior, and retrieval tuning.
- Configuration behavior is consistent across modules: preset defaults plus explicit overrides.

### FR-13 Ingestion Configurability
- The framework must expose ingestion controls with safe defaults.

Acceptance criteria:
- Developers can configure recursive discovery, max file count, include/exclude patterns, and failure policy.
- Developers can keep defaults and still ingest txt/pdf successfully.
- Ingestion options are documented in the environment contract.

### FR-14 SDK Config Object API
- The framework must expose typed config objects for major domains: runtime, vector backend, retrieval, ingestion, and llm.

Acceptance criteria:
- A developer can create FastAI(...) using typed config objects.
- Config object values override environment variables when both are supplied.
- Partial config objects are allowed; unspecified fields fall back to profile and built-in defaults.

## 8. Non-Functional Requirements

### NFR-1 Modularity
- Internal modules must be separated into ingestion, retrieval, llm, storage, and api components.

### NFR-2 Extensibility
- Adding a new LLM provider should require implementing a provider adapter only.

### NFR-2A Vector Backend Extensibility
- Adding a new vector database should require implementing a vector adapter only.

### NFR-2B Data Ownership
- User data must remain in developer-controlled infrastructure.
- The framework must not copy indexed corpus data to framework-managed hosted storage.

### NFR-3 Reliability
- Failures in a single request should not crash the server process.

### NFR-4 Observability Quality
- Debug payload must be human-readable and sufficient to reproduce prompt assembly logic.

### NFR-4A Configuration Predictability
- Default values must be deterministic and documented.
- Override precedence must be deterministic and documented.

### NFR-5 Performance (MVP Baseline)
- For small corpora (up to 5,000 chunks), median retrieval plus generation latency should be practical for interactive API use.
- MVP provisional target: median end-to-end latency <= 5 seconds on local reference dataset and default configuration.

## 9. API Contract (MVP)

Request example:
```json
{
  "query": "What does the policy say about refunds?"
}
```

Response example:
```json
{
  "answer": "Refunds are allowed within 30 days with proof of purchase.",
  "sources": [
    {
      "id": "doc_12_chunk_4",
      "text": "Refunds are allowed within 30 days...",
      "metadata": {
        "path": "docs/policy.pdf",
        "page": 7
      }
    }
  ]
}
```

Debug response extension (when enabled):
```json
{
  "answer": "...",
  "sources": [
    {
      "id": "doc_12_chunk_4",
      "text": "Refunds are allowed within 30 days..."
    }
  ],
  "debug": {
    "retrieved_chunks": ["..."],
    "context": "...",
    "final_prompt": "..."
  }
}
```

## 10. MVP Exit Criteria
The MVP is complete when all conditions are true:
1. Developer can ingest .txt and .pdf documents from local paths.
2. Developer can define an AI route using a decorator.
3. HTTP request to that route returns answer plus sources.
4. Retrieval, context construction, and LLM call are executed automatically.
5. BYOK works for at least one LLM provider.
6. Debug mode exposes retrieved chunks, context, and final prompt.
7. Public behavior matches this requirements document without introducing out-of-scope systems.

## 11. Delivery Governance Requirements

### DGR-1 Single-Objective Runs
- Implementation runs must target one objective at a time.

Acceptance criteria:
- Each run log declares exactly one objective and one mode.

### DGR-2 Required Task Mode Declaration
- Every implementation run must declare mode before changes: implement, stabilize, investigate, or cleanup.

Acceptance criteria:
- Run metadata includes mode and mode-consistent actions.
- Investigate runs are read-only unless explicit approval exists.

### DGR-3 Required Run Contract
- Before changes, each run must document objective, exact steps, and success criteria.
- After changes, each run must document changes made, evidence, residual risk, and next safe step.

Acceptance criteria:
- Delivery artifacts include both pre-change and post-change contract sections.

### DGR-4 Required Execution Order
- Operational and implementation runs must follow this order:
  - health checks
  - dependency readiness
  - bootstrap/provisioning
  - feature action
  - verification

Acceptance criteria:
- If a step fails, execution stops and blocker is reported before continuation.

### DGR-5 Verification Completion Standard
- A run is complete only when all are true:
  - service health checks pass
  - target action succeeds
  - user-visible behavior works
  - no new blocking error appears in relevant logs

Acceptance criteria:
- Evidence includes command outputs or summaries proving all four checks.
