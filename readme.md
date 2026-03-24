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

## Requirements Reference
Detailed, testable requirements are documented in specs/requirements.md.

## Tech Stack Reference
Technology choices, Docker-first architecture, and alternatives analysis are documented in specs/tech-stack.md.

## Project Structure Reference
Recommended modular monolith project layout, module boundaries, and folder ownership are documented in specs/project-structure.md.

## Design Document Reference
End-to-end architecture, flows, data model, error handling, and phased implementation plan are documented in specs/design-doc.md.

## Execution Tasks Reference
Step-by-step MVP implementation tasks with dependencies and done criteria are documented in specs/tasks.md.

## Agentic Execution Pack
Execution readiness checklist: specs/execution-checklist.md.
Environment variable contract: specs/env-contract.md.
Machine-readable API schema: specs/api-contract.yaml.
CI quality gates and merge policy: specs/ci-gates.md.
Test fixture and golden-case specification: specs/fixtures-spec.md.