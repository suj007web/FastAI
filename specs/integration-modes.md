# Integration Modes and User Setup

## Goal
Allow users to adopt FastAI without rewriting their application architecture.

## Mode 1: Library Integration (Least Invasive)
Use FastAI inside an existing endpoint in the user's app.

Typical setup steps:
1. Install FastAI package.
2. Configure environment variables.
3. Ingest docs path.
4. Call FastAI from existing route handler.

Example host app flow:
1. Existing /support/ask route receives query.
2. Route calls FastAI retrieval and generation API.
3. Route returns answer and sources in host service response.

## Mode 2: Router Plugin Integration
Mount FastAI routes into existing app namespace.

Typical setup steps:
1. Import FastAI router/plugin.
2. Mount under path like /ai.
3. Keep all existing app routes unchanged.

Example host app flow:
1. Existing application continues serving current routes.
2. FastAI routes are available at /ai/ask.

## Mode 3: Sidecar Service Integration
Run FastAI independently and consume via HTTP.

Typical setup steps:
1. Start FastAI service via Docker Compose.
2. Host app calls FastAI /ask endpoint.
3. Host app maps response to product UX.

This mode avoids framework coupling in host codebase.

## End User Setup Commands (PowerShell)

1. Clone and enter repo:
```powershell
git clone https://github.com/suj007web/FastAI.git
cd FastAI
```

2. Configure environment:
```powershell
Copy-Item .env.example .env
notepad .env
```

3. Start services:
```powershell
docker compose -f compose/docker-compose.yml up -d --build
```

4. Verify service:
```powershell
Invoke-WebRequest http://localhost:8000/health | Select-Object -Expand Content
```

5. Query API:
```bash
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"query":"What is refund policy?"}'
```

## Response Contract Invariants
All integration modes must preserve:
1. answer: string
2. sources: array
3. debug: optional object when enabled
4. Auth behavior: no API key when auth mode is disabled; X-API-Key required when auth mode is api_key

## When To Choose Which Mode
1. Library mode: fastest adoption in existing service code.
2. Router plugin mode: best when users want built-in FastAI routes.
3. Sidecar mode: best when users want strict service separation.
