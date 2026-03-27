# Tech Stack Decision Document: FastAI

## 1. Context
FastAI is an AI-native RAG backend framework. The MVP needs:
- Fast developer onboarding
- Provider-agnostic LLM integration
- Deterministic retrieval pipeline
- Good observability
- Docker-first local and CI environments from day one

## 2. Architecture Principles for Stack Selection
1. Docker-first execution for consistency across local, CI, and deployment.
2. Minimal moving parts in MVP.
3. Explicit module boundaries (ingestion, retrieval, llm, storage, api).
4. Replaceable provider and storage adapters.
5. Strong Python typing and schema validation.

## 3. Chosen Stack (MVP)

| Layer | Chosen | Why this choice |
|---|---|---|
| Language | Python 3.12 | Best ecosystem for AI and document processing; strong async support and typing improvements. |
| API Framework | FastAPI | Native typing, automatic OpenAPI docs, clean dependency model, high developer velocity. |
| ASGI Server | Uvicorn | Lightweight, production-proven ASGI server for FastAPI. |
| Validation | Pydantic v2 | Fast and explicit request/response schema validation with excellent FastAPI integration. |
| LLM/Embeddings Adapter | LiteLLM | Single interface across multiple providers, enables BYOK and provider-agnostic design. |
| PDF Parsing | pypdf | Simple, stable, and enough for MVP PDF text extraction. |
| Text Chunking/Token Utilities | tiktoken + internal chunker | Deterministic chunk sizing and direct control over retrieval behavior. |
| Vector + Metadata Storage | BYO backend via adapter (default: PostgreSQL 16 + pgvector; also Qdrant and MongoDB Atlas Vector Search) | Developers keep ownership of data and choose backend by environment configuration. |
| ORM/Data Access | SQLAlchemy 2.x | Mature Python data layer with good control and portability. |
| Migrations | Alembic | Standard, reliable schema migration workflow for team development. |
| Logging | structlog + standard logging | Structured logs with low complexity and good compatibility. |
| Tracing/Metrics | OpenTelemetry SDK (initially optional) | Future-proof observability without locking into one backend vendor. |
| Testing | pytest, pytest-asyncio, httpx | Strong async API testing and broad Python ecosystem support. |
| Lint/Format | Ruff | Very fast linting and formatting in one tool; easy CI integration. |
| Type Checking | mypy | Static checks to protect module contracts and adapter interfaces. |
| Packaging/Env | pyproject.toml + uv | Fast, reproducible dependency management and install speed. |
| Containerization | Docker + Docker Compose | Repeatable local stack and service orchestration from the beginning. |
| CI | GitHub Actions | Native integration with repository workflow and container-based checks. |

## 4. Docker-First Development Model

### 4.1 Why Docker From Day One
1. Eliminates machine-specific setup drift.
2. Gives one reproducible runtime for app plus dependencies.
3. Makes integration tests realistic by running against actual services.
4. Reduces deployment friction by shipping the same image shape used in development.

### 4.2 Baseline Container Topology
- app: FastAPI framework service
- db: PostgreSQL with pgvector extension

Optional later services:
- otel-collector for distributed tracing export
- redis for caching (only if profiling shows need)

### 4.3 Standard Workflow
1. Build images with a multi-stage Dockerfile.
2. Start stack via docker compose up.
3. Run migrations on startup or CI migration step.
4. Execute tests inside containerized environment in CI.

## 5. Alternatives Evaluated and Rationale

## 5.1 API Layer
### Chosen: FastAPI
- Pros: type-driven API design, auto docs, async-first, broad adoption.

Alternatives:
- Flask
  - Pros: very simple and flexible.
  - Why not now: weaker native typing and async ergonomics for this use case.
- Django / Django REST Framework
  - Pros: batteries-included ecosystem.
  - Why not now: heavier than needed for RAG-focused framework MVP.

## 5.2 LLM Integration Layer
### Chosen: LiteLLM adapter
- Pros: provider abstraction, BYOK support, unified call interface.

Alternatives:
- Direct provider SDKs (OpenAI, Anthropic, etc.)
  - Pros: full provider-specific control.
  - Why not now: duplicates integration logic and weakens provider-agnostic design.
- LangChain high-level abstractions
  - Pros: many built-ins and integrations.
  - Why not now: adds framework coupling and complexity for a core framework product.

## 5.3 Vector Storage
### Chosen: Adapter strategy with pgvector default
- Pros: supports data ownership and backend portability while keeping a simple default path.

Supported backends in MVP:
- PostgreSQL + pgvector (default)
- Qdrant
- MongoDB Atlas Vector Search

Future candidates:
- Weaviate / Milvus
- Chroma/FAISS local-first stores

## 5.4 Ingestion and Parsing
### Chosen: pypdf + internal extractors
- Pros: low dependency footprint, direct control over ingestion behavior.

Alternatives:
- unstructured
  - Pros: broad file-format support.
  - Why not now: heavier dependency chain than needed for text and PDF-only MVP.
- PyMuPDF
  - Pros: strong PDF capabilities and speed.
  - Why not now: pypdf is sufficient for MVP, keep parser complexity minimal initially.

## 5.5 Observability
### Chosen: structured logging first, OpenTelemetry-ready
- Pros: low setup cost now, scalable observability path later.

Alternatives:
- Full observability stack from start (Prometheus, Grafana, Jaeger)
  - Pros: rich telemetry from day one.
  - Why not now: operational overhead before product behavior stabilizes.

## 6. Tradeoffs Accepted in MVP
1. Maintaining multiple vector adapters increases testing scope, accepted to preserve user data ownership.
2. pypdf extraction quality may be lower on complex PDF layouts; acceptable for MVP scope.
3. LiteLLM abstraction may hide some provider-specific features; acceptable to keep API stable.
4. OpenTelemetry is optional at first to keep setup lean.

## 7. Initial Version Targets
1. Python: 3.12
2. FastAPI: latest stable 0.x compatible with Pydantic v2
3. Pydantic: v2
4. SQLAlchemy: 2.x
5. Vector backend: pgvector default; qdrant and mongodb atlas supported via adapters
6. Docker Compose spec: v3.9+

## 8. Security and Operations Baseline
1. Secrets passed via environment variables and Docker secrets where available.
2. No provider keys committed to repository.
3. Health endpoint for container readiness/liveness.
4. Resource limits configured for db and app in compose profiles for CI stability.

## 9. Decision Summary
This stack is chosen to maximize speed-to-MVP while preserving long-term extensibility and user data ownership. The key strategy is Docker-first reproducibility, a clean modular Python core, provider-agnostic LLM integration, and pluggable vector backends with a simple pgvector default.
