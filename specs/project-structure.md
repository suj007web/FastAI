# Project Structure Blueprint: Modular Monolith

## 1. Goal
Define a scalable modular monolith structure for FastAI that:
- Keeps ingestion, retrieval, llm, storage, and api concerns isolated
- Enables independent development per module
- Avoids accidental cross-module coupling
- Supports Docker-first local and CI workflows

This is a documentation blueprint only. It does not create folders yet.

## 2. Recommended Pattern
Use a hybrid of:
1. Layered architecture inside each module
2. Vertical module boundaries at the top level
3. Shared kernel for cross-cutting utilities and contracts

Why this pattern:
- Vertical modules reduce cognitive load and domain leakage.
- Internal layering keeps domain logic separate from adapters/framework code.
- Shared kernel avoids duplicate utility code while preventing module-to-module shortcuts.

## 3. Proposed Directory Structure
```text
fastai/
  pyproject.toml
  README.md

  specs/
    requirements.md
    tech-stack.md
    project-structure.md
    design-doc.md
    tasks.md
    execution-checklist.md
    env-contract.md
    ci-gates.md
    fixtures-spec.md
    api-contract.yaml

  docker/
    app/
      Dockerfile
    db/
      init.sql

  compose/
    docker-compose.yml
    docker-compose.override.yml

  scripts/
    dev.sh
    test.sh
    lint.sh
    migrate.sh

  migrations/
    versions/

  src/
    fastai/
      app/
        main.py
        lifecycle.py
        settings.py
        dependencies.py

      api/
        http/
          routers/
            health.py
            ai_routes.py
          schemas/
            request.py
            response.py
          middleware/
            request_id.py
            exception_handlers.py

      modules/
        ingestion/
          domain/
            models.py
            services.py
            policies.py
          application/
            commands.py
            handlers.py
            dto.py
          infrastructure/
            extractors/
              text_extractor.py
              pdf_extractor.py
            chunking/
              chunker.py
            embedding/
              embedder_adapter.py
            repositories/
              ingestion_job_repo.py

        retrieval/
          domain/
            models.py
            ranking.py
          application/
            queries.py
            handlers.py
            dto.py
          infrastructure/
            vector_search/
              pgvector_search.py
            reranking/
              simple_ranker.py

        llm/
          domain/
            models.py
            prompting.py
          application/
            commands.py
            handlers.py
            dto.py
          infrastructure/
            providers/
              litellm_provider.py
            prompt_templates/
              default_prompt.py

        storage/
          domain/
            models.py
          application/
            commands.py
            handlers.py
          infrastructure/
            db/
              session.py
              models.py
              repositories/
                chunk_repo.py
                document_repo.py

        observability/
          domain/
            events.py
          application/
            services.py
          infrastructure/
            logging/
              logger.py
            tracing/
              otel.py

      shared/
        contracts/
          interfaces.py
          errors.py
        types/
          ids.py
          pagination.py
        utils/
          hashing.py
          time.py
          text.py
        config/
          constants.py

      boot/
        container.py
        module_registry.py

  tests/
    unit/
      modules/
        ingestion/
        retrieval/
        llm/
        storage/
      shared/
    integration/
      api/
      workflows/
    contract/
      api/
      providers/

  docs/
    architecture/
      decision-records/
    api/
```

## 4. What Lives Where (Explicit Ownership)

## 4.1 src/fastai/app
Contains app bootstrap concerns only.
- main.py: FastAPI app creation and startup wiring.
- lifecycle.py: startup/shutdown hooks.
- settings.py: environment-driven configuration.
- dependencies.py: request-scoped dependency providers.

Must not contain business rules.

## 4.2 src/fastai/api
Contains transport concerns only.
- routers/: HTTP route declarations and endpoint handlers.
- schemas/: Pydantic request/response models.
- middleware/: cross-cutting HTTP behavior (request ids, error mapping).

Must not execute domain logic directly; delegates to application handlers.

## 4.3 src/fastai/modules/<module>
Each module is a bounded context with three layers:
- domain/: core business rules, entities, value objects, policies.
- application/: use cases, commands/queries, orchestration, DTO mapping.
- infrastructure/: framework and external integrations (DB, provider SDKs, file I/O).

Module responsibilities:
- ingestion: data extraction, chunking, embedding orchestration.
- retrieval: query embedding, candidate retrieval, ranking.
- llm: prompt assembly, provider invocation, generation behavior.
- storage: persistence abstractions and DB adapters.
- observability: structured logs, traces, pipeline diagnostics.

## 4.4 src/fastai/shared
Contains code that is generic and reusable across modules.
- contracts/: stable interfaces and shared exceptions.
- types/: common value types (ids, generic pagination types).
- utils/: pure utility helpers with no module-specific semantics.
- config/: cross-module constants and flags.

Rule: shared is allowed to be imported by modules; modules should not import each other directly unless through contracts.

## 4.5 src/fastai/boot
Composition root.
- container.py: dependency injection wiring.
- module_registry.py: registers module handlers/adapters into app runtime.

All cross-module wiring happens here, not inside domain code.

## 4.6 tests
- unit/: tests module internals with dependencies mocked.
- integration/: tests module collaboration and DB interactions.
- contract/: validates public API schema and provider adapter contracts.

Mirror production package names as much as possible.

## 4.7 docker and compose
- docker/: build/runtime image definitions.
- compose/: local orchestration definitions and optional overrides.

Keep environment-specific compose overrides isolated from base compose file.

## 4.8 migrations
Single source of schema evolution truth (Alembic versions).

## 4.9 docs
Long-lived design docs and ADRs, not ephemeral notes.

## 5. Module Dependency Rules
1. api can depend on application layer interfaces only.
2. application can depend on domain and shared.
3. domain can depend only on shared types/contracts.
4. infrastructure can depend on domain/application/shared and external libraries.
5. module A cannot import module B domain directly; communicate through shared contracts and boot wiring.
6. shared must stay framework-light and domain-neutral.

## 6. Naming Conventions
1. Commands use imperative names: IngestDocumentsCommand.
2. Queries use question/fetch names: RetrieveContextQuery.
3. Handlers end with Handler.
4. Repositories end with Repository.
5. Provider adapters end with Provider.

## 7. Request Flow Mapping to Structure
1. HTTP request enters api/http/routers.
2. Router validates payload with api/http/schemas.
3. Router calls module application handler.
4. Handler executes domain rules.
5. Handler uses infrastructure adapters for DB/vector/LLM.
6. Observability module captures debug artifacts.
7. Router returns response schema.

## 8. Why This Structure Over Common Alternatives
Alternative 1: Pure horizontal layers (controllers/services/repositories globally)
- Rejected because domain boundaries blur quickly and create tight coupling.

Alternative 2: Microservices from day one
- Rejected for MVP due to operational complexity and slower iteration.

Alternative 3: Single flat package
- Rejected because module ownership and testing boundaries become unclear as code grows.

Chosen structure gives microservice-like boundaries inside one deployable unit.

## 9. Growth Path Without Restructure
1. Add new module under src/fastai/modules.
2. Register adapters in boot/module_registry.py.
3. Expose routes in api/http/routers.
4. Add tests under tests/unit and tests/integration.

No major folder redesign required for near-term scaling.

## 10. Common Utilities Policy
Use shared/utils only for:
1. Stateless, pure helpers.
2. Generic logic used by 2+ modules.
3. Logic with no domain ownership.

Do not put business rules in shared/utils. If logic belongs to one module, keep it in that module.
