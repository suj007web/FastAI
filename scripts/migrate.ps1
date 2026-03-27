param(
    [ValidateSet("upgrade", "downgrade", "current", "history", "heads", "stamp")]
    [string]$Action = "upgrade",
    [string]$Revision = "head"
)

$ErrorActionPreference = "Stop"

if (-not $env:FASTAI_DB_DSN) {
    $env:FASTAI_DB_DSN = "postgresql+psycopg://fastai:fastai@localhost:5432/fastai"
}

if ($Action -in @("upgrade", "downgrade", "stamp")) {
    python -m alembic -c alembic.ini $Action $Revision
} else {
    python -m alembic -c alembic.ini $Action
}
