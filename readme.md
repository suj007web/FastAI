# FastAI: AI-Native RAG API Framework

## Problem Statement
Developers currently spend significant effort wiring together ingestion, chunking, embeddings, vector search, prompt construction, and LLM calls before they can expose one useful AI endpoint.

This project solves that by providing a Python framework where a developer defines an AI endpoint and adds data, and the framework handles the full RAG pipeline automatically.

## Product Goal
Convert data into a production-usable API endpoint with minimal framework-specific code.

## One-Line Pitch
A Python framework where developers define AI endpoints, and the framework automatically handles ingestion, retrieval, and LLM interaction.

## MVP Scope
The MVP must provide all of the following:

1. AI route definition through a decorator-based API.
2. Data ingestion from local text and PDF files.
3. Retrieval-augmented query processing for each AI route call.
4. LLM provider abstraction with bring-your-own-key support.
5. HTTP endpoint exposure for defined AI routes.
6. Response payload with both answer and source references.
7. Basic observability output for retrieved chunks, context, and final prompt.

## Explicit Non-Goals
The MVP must not include:

1. Full authentication and authorization systems.
2. Billing or subscription management.
3. Web UI dashboards.
4. General backend framework features unrelated to RAG (for example ORM layers).
5. Microservice decomposition.

## Core Runtime Behavior
When a client calls an AI endpoint:

1. The user query is embedded.
2. Relevant chunks are retrieved from the vector store.
3. Context is assembled from retrieved chunks.
4. The selected LLM provider is called.
5. The API responds with:

```json
{
    "answer": "...",
    "sources": [
        {
            "id": "chunk_or_doc_id",
            "text": "source snippet",
            "metadata": {
                "path": "docs/file.pdf",
                "page": 3
            }
        }
    ]
}
```

## Example API Usage
```python
from ai_framework import AIApp

app = AIApp()
app.add_data("docs/")

@app.ai_route("/ask")
def ask(query: str):
    return query
```

## SDK Usage Examples

Library query call:

```python
from fastai import FastAI

sdk = FastAI.from_profile("balanced", vector_backend="pgvector", model="gpt-4.1-mini")
result = sdk.ask("What is the refund policy?")
print(result["answer"])
```

Host route handler integration with library client:

```python
from fastapi import FastAPI
from fastai import FastAI, create_fastai_client

app = FastAPI()
client = create_fastai_client(
    FastAI.from_profile("balanced", vector_backend="pgvector", model="gpt-4.1-mini")
)

@app.post("/support/ask")
def support_ask(payload: dict[str, object]) -> dict[str, object]:
    query = str(payload.get("query", ""))
    debug = bool(payload.get("debug", False))
    return client.ask(query=query, debug=debug)
```

Mount FastAI router in host app:

```python
from fastapi import FastAPI
from fastai import FastAI, get_fastai_router

app = FastAPI()
sdk = FastAI.for_qdrant(
    url="http://localhost:6333",
    collection="fastai_chunks",
    model="gpt-4.1-mini",
)
app.include_router(get_fastai_router(sdk=sdk), prefix="/ai")
```

Mount FastAI plugin under custom path:

```python
from fastapi import FastAPI
from fastai import FastAI, mount_fastai_router

app = FastAPI()
sdk = FastAI()
mount_fastai_router(app, sdk=sdk, path="/assistant")
```

Register and call custom AI route:

```python
from fastai import FastAI

sdk = FastAI()

@sdk.ai_route("/support", name="support")
def support(query: str) -> str:
    return f"support: {query}"

reply = sdk.ask("How do I reset password?", route_name="support")
print(reply)
```

## Architecture (Modular Monolith)
1. App Core: app lifecycle and route registration.
2. Ingestion Engine: extract, chunk, embed, and index data.
3. Retrieval Engine: query embedding, retrieval, and context assembly.
4. LLM Engine: provider abstraction and generation calls.
5. Storage Layer: vector store and metadata store.
6. API Layer: endpoint exposure and request validation.

## Design Principles
1. AI-first abstraction: AI routes are first-class.
2. LLM-agnostic: no provider-specific hardcoding in public APIs.
3. Deterministic retrieval path: same inputs should produce same retrieved context.
4. Observable pipeline: debug data is accessible for each request.

## Integration Modes (Adopt By Choice)
FastAI must be non-invasive. Users should integrate based on their constraints, not rewrite their app architecture.

1. Library mode: call FastAI inside an existing endpoint in the user's app.
2. Router plugin mode: mount FastAI-provided routes under a path such as /ai.
3. Sidecar mode: run FastAI as a separate service and call it over HTTP.

## End User Setup Flow (Existing Project)
The expected setup for a developer integrating into an existing service is:

1. Install dependency.
2. Configure provider keys and retrieval settings in environment variables.
3. Add document corpus path for ingestion.
4. Wire one endpoint that calls FastAI logic.
5. Query endpoint and receive answer plus sources.

Example setup commands:

```powershell
pip install fastai-framework
Copy-Item .env.example .env
docker compose -f compose/docker-compose.yml up -d --build
Invoke-WebRequest http://localhost:8000/health | Select-Object -Expand Content
```

Example query command:

```bash
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"query":"What is refund policy?"}'
```

Expected response fields:
1. answer
2. sources
3. debug (optional, when enabled)

## Requirements Reference
Detailed, testable requirements are documented in specs/requirements.md.

## Tech Stack Reference
Technology choices, Docker-first architecture, and alternatives analysis are documented in specs/tech-stack.md.

## Project Structure Reference
Recommended modular monolith project layout, module boundaries, and folder ownership are documented in specs/project-structure.md.

## Integration Modes Reference
Non-invasive adoption patterns and end-user setup steps are documented in specs/integration-modes.md.

## Design Document Reference
End-to-end architecture, flows, data model, error handling, and phased implementation plan are documented in specs/design-doc.md.

## Execution Tasks Reference
Step-by-step MVP implementation tasks with dependencies and done criteria are documented in specs/tasks.md.

## Agentic Execution Pack
Execution readiness checklist: specs/execution-checklist.md.
Environment variable contract: specs/env-contract.md.
Copy-ready configuration profiles and flow: specs/config-examples.md.
Machine-readable API schema: specs/api-contract.yaml.
CI quality gates and merge policy: specs/ci-gates.md.
Test fixture and golden-case specification: specs/fixtures-spec.md.