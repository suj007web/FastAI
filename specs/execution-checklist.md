# Execution Checklist for Autonomous MVP Delivery

## Purpose
This checklist defines the minimum controls required for reliable agentic execution of FastAI MVP.

## Usage
1. Run this checklist at the start of each implementation cycle.
2. Re-run after every major merge.
3. Mark items complete only with evidence (tests, logs, artifacts).

## A. Prerequisites
- [ ] All baseline docs exist and are current:
  - readme.md
  - specs/requirements.md
  - specs/tech-stack.md
  - specs/project-structure.md
  - specs/design-doc.md
  - specs/tasks.md
- [ ] Open decisions in specs/design-doc.md are resolved or explicitly deferred with owner and date.
- [ ] API contract is machine-readable and versioned.
- [ ] Environment variable contract exists and is validated at startup.

## B. Task Execution Controls
- [ ] Task order follows specs/tasks.md dependencies exactly.
- [ ] Every task has explicit done evidence.
- [ ] Blocked tasks are marked with blocker description and next action.
- [ ] No out-of-scope work is added during MVP execution.

## C. Quality Gates
- [ ] Ruff lint passes.
- [ ] mypy type-check passes.
- [ ] Unit tests pass.
- [ ] Integration tests pass against Docker services.
- [ ] Contract tests pass for HTTP and provider adapters.
- [ ] Deterministic retrieval golden tests pass.

## D. Runtime Verification
- [ ] docker compose up starts app and db successfully.
- [ ] /health endpoint is healthy.
- [ ] add_data ingests txt and PDF corpus end-to-end.
- [ ] /ask returns answer plus sources contract.
- [ ] debug mode returns retrieved_chunks, context, and final_prompt.

## E. Security and Ops Baseline
- [ ] No secrets in repository.
- [ ] Startup fails fast on missing required env vars.
- [ ] Logs include request_id and module context.
- [ ] Error responses do not leak provider keys or internals.

## F. MVP Sign-Off Checklist
- [ ] All MVP exit criteria in specs/requirements.md validated.
- [ ] Known limitations documented.
- [ ] Deferred items documented in post-MVP backlog.
- [ ] Release candidate tag created with CI artifacts.

## Required Evidence Artifacts
1. CI run URL or log bundle.
2. Test summary output.
3. Ingestion run summary on sample corpus.
4. Example successful /ask response.
5. Example debug=true response.
