# CI Gates and Pipeline Policy

## Purpose
Defines the mandatory CI pipeline stages and pass criteria for MVP merges.

## Branch Protection Recommendation
1. Require status checks before merge.
2. Require linear history or squash merges.
3. Disallow direct pushes to main.

## Pipeline Stages

## Stage 1: Static Checks
Checks:
1. Ruff lint
2. Ruff format check
3. mypy type-check

Pass criteria:
1. Zero lint errors.
2. No formatting diffs.
3. No mypy errors.

## Stage 2: Unit Tests
Checks:
1. pytest unit suite

Pass criteria:
1. All unit tests pass.
2. No flaky retries allowed in protected branch runs.

## Stage 3: Integration Tests (Docker)
Checks:
1. Start app + db via Docker Compose.
2. Apply migrations.
3. Run integration tests against live services.

Pass criteria:
1. All integration tests pass.
2. Health check endpoint passes before test run.

## Stage 4: Contract Tests
Checks:
1. HTTP contract tests against api-contract.yaml
2. Provider adapter contract tests

Pass criteria:
1. Request/response schemas match contract.
2. Provider adapters satisfy interface contract.

## Stage 5: Determinism and Regression
Checks:
1. Golden tests for retrieval ordering
2. Snapshot checks for debug payload shape

Pass criteria:
1. Retrieval outputs match approved golden fixtures.
2. Debug contract remains backward compatible for MVP.

## Stage 6: Build Artifact Validation
Checks:
1. Build production image
2. Run smoke test container startup

Pass criteria:
1. Image builds successfully.
2. Container starts and responds on /health.

## Required Workflow Outputs
1. Test report artifact (junit or equivalent)
2. Coverage report artifact
3. Docker image digest
4. Migration run log

## Coverage Policy (MVP)
1. Unit test line coverage target: 70 percent minimum.
2. Critical path modules (ingestion, retrieval, llm) target: 80 percent minimum.

## Failure Policy
1. Any failed required stage blocks merge.
2. Temporary bypass requires explicit maintainer approval and follow-up issue.

## Suggested GitHub Actions Jobs
1. quality-checks
2. unit-tests
3. integration-tests
4. contract-tests
5. determinism-tests
6. docker-build-smoke
