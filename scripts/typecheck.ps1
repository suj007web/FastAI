$ErrorActionPreference = "Stop"
$pythonExe = if ($env:FASTAI_PYTHON) { $env:FASTAI_PYTHON } else { "python" }

& $pythonExe -m mypy
if ($LASTEXITCODE -ne 0) { throw "mypy type-check failed." }

Write-Host "Type-check passed."
