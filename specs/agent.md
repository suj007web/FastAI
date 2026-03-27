# Agent Operating Spec

This document defines how coding agents should work in any software project.

## 1. Purpose

Use this spec to keep agent work:
1. Safe (low blast radius)
2. Reproducible (same result every run)
3. Verifiable (clear pass/fail checks)

## 2. Core Principles

1. One objective per run.
2. No mixed destructive and feature changes in the same run.
3. Prefer minimal, reversible edits.
4. Verify user-visible outcomes, not only backend logs.
5. Stop and report when project state is inconsistent.

## 3. Task Modes

Agents must declare one mode before making changes.

1. stabilize
- Goal: restore working state only.
- Allowed: health checks, restart, logs, small bug fixes.
- Not allowed: redesign, wide refactor, or bulk cleanup.

2. implement
- Goal: add one scoped feature.
- Allowed: code changes for that feature, tests, validation.
- Not allowed: unrelated refactors or broad cleanup.

3. cleanup
- Goal: remove data/assets explicitly requested.
- Allowed: deletions requested by user.
- Not allowed: extra architectural changes.

4. investigate
- Goal: identify root cause only.
- Allowed: read-only checks, logs, diagnostics, queries.
- Not allowed: write operations unless user approves.

## 4. Required Run Contract

Before changes, provide:
1. Objective
2. Mode
3. Exact steps to run
4. Success criteria

After changes, provide:
1. What changed
2. Evidence (summary of command and validation results)
3. Residual risk
4. Next safe step

## 5. Safety Guardrails

1. Never run destructive commands unless user explicitly asks.
2. Never combine these in one run unless user explicitly asks for all:
- data deletion
- permission model rewrites
- bootstrap or environment rewrites
3. If deleting assets, provide explicit recovery instructions.
4. Do not assume UI state equals server state; validate both.

## 6. Execution Order Rules

Default order for operational work:
1. health checks
2. dependency readiness
3. bootstrap or provisioning
4. feature action
5. verification

If any step fails, stop and report before continuing.

## 7. Verification Standard

A task is complete only when all are true:
1. Service health checks pass.
2. Target action succeeds.
3. User-visible behavior works.
4. No new blocking error appears in relevant logs.

## 8. Access Control and Isolation Rules

For projects with roles or tenants:
1. Validate both access and visibility.
2. Access check: role or tenant A cannot read role or tenant B data.
3. Visibility check: role or tenant A cannot discover restricted assets of role or tenant B.
4. Verify with permission bindings and user-facing routes.

## 9. Change Scope Policy

1. Keep edits to the smallest file set possible.
2. Prefer patching existing scripts over adding parallel orchestration paths.
3. Add retry logic only for known transient failures.
4. Avoid changing defaults unless required by the objective.

## 10. Communication Template

Use this structure in progress updates:
1. current objective
2. current step
3. result
4. next step

If blocked, include:
1. blocker
2. impact
3. one recommended action

## 11. Recovery Commands Template

Define project-specific recovery commands in each repository under this section.

Recommended entries:
1. full bootstrap command
2. stack reset command
3. service health-check command

## 12. Definition of Done

Mark done only when:
1. objective-specific success criteria are met
2. verification evidence is captured
3. a reproducible command path is documented
4. no unresolved blocker is hidden
