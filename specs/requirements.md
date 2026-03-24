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
9. API key validation means provider key presence and basic request auth hook support, not a complete auth system.

## 7. Functional Requirements

### FR-1 App Initialization
- The framework must provide an application object (for example AIApp) to initialize runtime and register AI routes.

Acceptance criteria:
- A developer can instantiate the app with default settings.
- The app can start an HTTP server exposing registered routes.

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

## 8. Non-Functional Requirements

### NFR-1 Modularity
- Internal modules must be separated into ingestion, retrieval, llm, storage, and api components.

### NFR-2 Extensibility
- Adding a new LLM provider should require implementing a provider adapter only.

### NFR-3 Reliability
- Failures in a single request should not crash the server process.

### NFR-4 Observability Quality
- Debug payload must be human-readable and sufficient to reproduce prompt assembly logic.

### NFR-5 Performance (MVP Baseline)
- For small corpora (up to 5,000 chunks), median retrieval plus generation latency should be practical for interactive API use.
- Exact SLA targets are deferred post-MVP.

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
