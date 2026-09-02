<#
.SYNOPSIS
  Run graphify's semantic (docs) extraction using a Gemini key held outside any git repo.

.DESCRIPTION
  Reads the key from %LOCALAPPDATA%\graphify\gemini.key — deliberately OUTSIDE the
  repo, so no .gitignore mistake can ever commit it. The key is set only for this
  process (never `setx`, never printed, never written into the repo).

  Create the key file once (see SETUP below), then run this script any time.

.EXAMPLE
  # One project's docs:
  .\run-graphify.ps1 -Target "D:\Dev Debug\ss2vr-work\docs"

  # The staged cross-engine corpus:
  .\run-graphify.ps1 -Target ".\corpus"

  # Cheap dry run — see what it WOULD cost before spending anything:
  .\run-graphify.ps1 -Target "D:\Dev Debug\ss2vr-work\docs" -WhatIfCost

.NOTES
  SETUP (run once, in your own terminal — never paste the key into a chat):

    $dir = "$env:LOCALAPPDATA\graphify"
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    Read-Host "Paste Gemini API key" -AsSecureString |
      ConvertFrom-SecureString -AsPlainText |
      Set-Content -Path "$dir\gemini.key" -NoNewline -Encoding utf8

  `Read-Host -AsSecureString` masks the key as you type it, so it never appears
  on screen or in your PowerShell history.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $Target,

    # Richer INFERRED cross-document edges. Costs more; worth it for a comparison graph.
    [switch] $Deep,

    # Also emit the crawlable wiki (index.md + one article per community).
    [switch] $Wiki,

    # Estimate size and stop. Makes no API calls and spends nothing.
    [switch] $WhatIfCost
)

$ErrorActionPreference = 'Stop'

$keyFile = Join-Path $env:LOCALAPPDATA 'graphify\gemini.key'

# ---- Size the job first -----------------------------------------------------
if (-not (Test-Path $Target)) { throw "Target not found: $Target" }

$docs  = Get-ChildItem -Path $Target -Recurse -File -Include *.md, *.txt -ErrorAction SilentlyContinue
$chars = ($docs | Measure-Object -Property Length -Sum).Sum
$tok   = [math]::Round($chars / 3.75)   # technical prose tokenizes ~3.5-4 chars/token

Write-Host ""
Write-Host "Target : $Target"
Write-Host "Files  : $($docs.Count)"
Write-Host "Chars  : $('{0:N0}' -f $chars)"
Write-Host "Est. input tokens: ~$('{0:N0}' -f $tok)"
Write-Host ""

if ($WhatIfCost) {
    Write-Host "Dry run - nothing sent, nothing spent." -ForegroundColor Yellow
    Write-Host "Output tokens typically run 25-40% of input for entity/edge extraction."
    return
}

# ---- Load the key (process-scoped only) -------------------------------------
if (-not (Test-Path $keyFile)) {
    Write-Host "No key file at: $keyFile" -ForegroundColor Yellow
    Write-Host "Create it once with the SETUP block in this script's header (Get-Help .\run-graphify.ps1 -Full)."
    Write-Host ""
    Write-Host "Or skip Gemini entirely: run the /graphify skill, which dispatches" -ForegroundColor Cyan
    Write-Host "Claude Code subagents instead and needs no key at all."
    return
}

$key = (Get-Content -Path $keyFile -Raw).Trim()
if ([string]::IsNullOrWhiteSpace($key)) { throw "Key file is empty: $keyFile" }

# Process-scoped only: not persisted, not inherited by anything but graphify.
$env:GEMINI_API_KEY = $key

try {
    $graphifyArgs = @($Target, '--backend', 'gemini')
    if ($Deep) { $graphifyArgs += '--mode', 'deep' }
    if ($Wiki) { $graphifyArgs += '--wiki' }

    Write-Host "Running: graphify $($graphifyArgs -join ' ')" -ForegroundColor Green
    Write-Host ""
    & graphify @graphifyArgs
}
finally {
    # Clear from this process's environment regardless of outcome.
    Remove-Item Env:\GEMINI_API_KEY -ErrorAction SilentlyContinue
    $key = $null
}
