# Git Commit Message Guidelines

## Format
Use this structure for every commit:

<type>(<scope>): <short summary>

<body>

## Header Rules
1. Use lowercase type.
2. Keep summary in imperative voice.
3. Keep summary concise (target <= 72 characters).
4. Use one clear scope when possible.

## Recommended Types
1. feat: new user-visible functionality.
2. fix: bug fix or regression fix.
3. docs: documentation-only changes.
4. refactor: internal code improvements without behavior change.
5. test: added/updated tests.
6. chore: tooling, config, or maintenance.
7. perf: performance improvement.
8. ci: CI/CD pipeline changes.

## Scope Examples
1. app
2. api
3. ingestion
4. retrieval
5. llm
6. storage
7. docker
8. docs
9. tests
10. tooling

## Body Rules
1. Explain what changed and why.
2. Group by impact area.
3. Mention any important constraints or known follow-ups.
4. Avoid implementation noise.

## Multi-Area Commit Guidance
If a commit spans multiple areas, choose the primary intent for type/scope and summarize the rest in the body.

## Good Examples
1. feat(app): add FastAPI bootstrap and root endpoint
2. chore(docker): add compose stack with pgvector postgres
3. docs(specs): add MVP requirements and architecture package
4. test(app): add bootstrap endpoint smoke test

## Progress Commit Template
chore(bootstrap): initialize MVP foundation and specs pack

- scaffold Python package and FastAPI app bootstrap
- add Ruff/mypy/pytest tooling scripts and baseline test
- add Docker multi-stage image and compose stack with pgvector db
- add gitignore and environment template for local setup
- move product docs and contracts into specs and update references
