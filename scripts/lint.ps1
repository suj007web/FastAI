$ErrorActionPreference = "Stop"
$pythonExe = if ($env:FASTAI_PYTHON) { $env:FASTAI_PYTHON } else { "python" }

& $pythonExe -m ruff check .
if ($LASTEXITCODE -ne 0) { throw "ruff check failed." }

& $pythonExe -m ruff format --check .
if ($LASTEXITCODE -ne 0) { throw "ruff format check failed." }

Write-Host "Lint and format checks passed."
