$ErrorActionPreference = "Stop"
$pythonExe = if ($env:FASTAI_PYTHON) { $env:FASTAI_PYTHON } else { "python" }

& $pythonExe -m pytest
if ($LASTEXITCODE -ne 0) { throw "pytest failed." }

Write-Host "Tests passed."
