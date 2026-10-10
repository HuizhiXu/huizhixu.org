$ErrorActionPreference = 'Stop'
# Use the same checked publishing entrypoint (Git for Windows includes bash).
& bash (Join-Path $PSScriptRoot 'deploy.sh') @args
exit $LASTEXITCODE
