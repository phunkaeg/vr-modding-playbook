<#
.SYNOPSIS
  Run Graphify semantic extraction through Gemini or the trusted LAN LLM host.

.DESCRIPTION
  Gemini reads its key from %LOCALAPPDATA%\graphify\gemini.key. The local route
  uses Graphify's zero-cost OpenAI-compatible local backend and reads
  LOCAL_LLM_API_KEY from the process, %LOCALAPPDATA%\graphify\local-ai.key, or
  the existing Codex local-llm
  MCP configuration. Credentials are never printed, persisted in this repo, or
  passed on a command line.

.EXAMPLE
  # One project's docs through Gemini:
  .\run-graphify.ps1 -Target "D:\Dev Debug\ss2vr-work\docs" `
    -Out ".\per-project\ss2vr"

.EXAMPLE
  # Use the LAN AI box for semantics:
  .\run-graphify.ps1 -Target ".\corpus" -SemanticProvider local -LocalModel coder-next

.EXAMPLE
  # Cheap dry run — see what it WOULD cost before spending anything:
  .\run-graphify.ps1 -Target "D:\Dev Debug\ss2vr-work\docs" -WhatIfCost

.NOTES
  GEMINI SETUP (run once, in your own terminal — never paste the key into chat):

    $dir = "$env:LOCALAPPDATA\graphify"
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    Read-Host "Paste Gemini API key" -AsSecureString |
      ConvertFrom-SecureString -AsPlainText |
      Set-Content -Path "$dir\gemini.key" -NoNewline -Encoding utf8

  The local route normally reuses the local-llm MCP credential. It can instead
  read %LOCALAPPDATA%\graphify\local-ai.key or an explicit -LocalKeyFile.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $Target,

    # Keep the graph outside the staged corpus so a later restage cannot delete it.
    [string] $Out,

    [ValidateSet('gemini', 'local')]
    [string] $SemanticProvider = 'gemini',

    # Model id advertised by the OpenAI-compatible LAN endpoint.
    [string] $LocalModel = 'coder-next',

    [ValidatePattern('^https?://')]
    [string] $LocalBaseUrl = 'http://192.168.0.161:8080/v1',

    # Optional explicit credential file. When omitted, the runner checks the
    # standard local Graphify key file and then the Codex local-llm MCP config.
    [string] $LocalKeyFile,

    # These are intentionally conservative. Larger chunks silently omitted small
    # documents in the measured fleet extraction; higher concurrency hit Gemini TPM.
    [ValidateRange(1000, 1000000)]
    [int] $TokenBudget = 20000,

    [ValidateRange(1, 32)]
    [int] $MaxConcurrency = 2,

    # Richer INFERRED cross-document edges. Costs more; worth it for a comparison graph.
    [switch] $Deep,

    # Also emit the crawlable wiki (index.md + one article per community).
    [switch] $Wiki,

    # Estimate size and stop. Makes no API calls and spends nothing.
    [switch] $WhatIfCost,

    # Ignore Graphify's incremental manifest and re-extract every document.
    [switch] $Force
)

$ErrorActionPreference = 'Stop'

$geminiKeyFile = Join-Path $env:LOCALAPPDATA 'graphify\gemini.key'
if ($SemanticProvider -eq 'local' -and -not $PSBoundParameters.ContainsKey('MaxConcurrency')) {
    # One GPU/model server: parallel requests add contention and make hollow
    # responses more likely. Callers can override this deliberately.
    $MaxConcurrency = 1
}

function Get-LocalLlmApiKey {
    if (-not [string]::IsNullOrWhiteSpace($env:LOCAL_LLM_API_KEY)) {
        return $env:LOCAL_LLM_API_KEY
    }

    $candidate = if ($LocalKeyFile) {
        $LocalKeyFile
    } else {
        Join-Path $env:LOCALAPPDATA 'graphify\local-ai.key'
    }
    if (Test-Path -LiteralPath $candidate -PathType Leaf) {
        $value = (Get-Content -LiteralPath $candidate -Raw).Trim()
        if (-not [string]::IsNullOrWhiteSpace($value)) { return $value }
    }

    # Reuse the credential already scoped to the local-llm MCP without exposing
    # or duplicating it. Restrict the regex to that one TOML section.
    $codexConfig = Join-Path $HOME '.codex\config.toml'
    if (Test-Path -LiteralPath $codexConfig -PathType Leaf) {
        $configText = Get-Content -LiteralPath $codexConfig -Raw
        $section = [regex]::Match(
            $configText,
            '(?ms)^\[mcp_servers\.local-llm\.env\]\s*(.*?)(?=^\[|\z)'
        ).Groups[1].Value
        if ($section) {
            $match = [regex]::Match(
                $section,
                '(?m)^LOCAL_LLM_API_KEY\s*=\s*["'']([^"'']+)["'']'
            )
            if ($match.Success -and -not [string]::IsNullOrWhiteSpace($match.Groups[1].Value)) {
                return $match.Groups[1].Value
            }
        }
    }

    throw @"
No local AI credential was found. Set LOCAL_LLM_API_KEY for this process or create:
  $candidate
The value is the same bearer token used by the local-llm MCP. Never put it in a repo.
"@
}

# ---- Size the job first -----------------------------------------------------
if (-not (Test-Path -LiteralPath $Target)) { throw "Target not found: $Target" }

$docs = Get-ChildItem -LiteralPath $Target -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Extension -in @('.md', '.txt') }
$chars = [long](($docs | Measure-Object -Property Length -Sum).Sum)
$tok = [math]::Round($chars / 3.75) # technical prose tokenizes ~3.5-4 chars/token

Write-Host ''
Write-Host "Target : $Target"
Write-Host "Files  : $($docs.Count)"
Write-Host "Chars  : $('{0:N0}' -f $chars)"
Write-Host "Est. input tokens: ~$('{0:N0}' -f $tok)"
Write-Host ''

if ($WhatIfCost) {
    Write-Host 'Dry run - nothing sent, nothing spent.' -ForegroundColor Yellow
    Write-Host 'Output tokens typically run 25-40% of input for entity/edge extraction.'
    return
}

# ---- Load credentials (process-scoped only) ---------------------------------
$key = $null
$backend = 'gemini'
$model = $null
$previousGeminiKey = $env:GEMINI_API_KEY
$previousOllamaKey = $env:OLLAMA_API_KEY
$previousOllamaBaseUrl = $env:OLLAMA_BASE_URL

if ($SemanticProvider -eq 'gemini') {
    if (-not (Test-Path -LiteralPath $geminiKeyFile -PathType Leaf)) {
        throw "No key file at: $geminiKeyFile. Use the masked SETUP command in this script's header; never paste the key into chat."
    }
    $key = (Get-Content -LiteralPath $geminiKeyFile -Raw).Trim()
    if ([string]::IsNullOrWhiteSpace($key)) { throw "Key file is empty: $geminiKeyFile" }
    $env:GEMINI_API_KEY = $key
} else {
    $key = Get-LocalLlmApiKey
    # Graphify's ollama backend is still an OpenAI-compatible HTTP client, but
    # carries zero pricing and local-model context controls. It has been smoke-
    # tested against the llama-swap endpoint used by this box.
    $backend = 'ollama'
    $model = $LocalModel
    $env:OLLAMA_API_KEY = $key
    $env:OLLAMA_BASE_URL = $LocalBaseUrl.TrimEnd('/')
    Write-Host ("Semantic provider: LAN endpoint {0}, model {1} (actual API cost: `$0)" -f $env:OLLAMA_BASE_URL, $LocalModel) -ForegroundColor Cyan
}

try {
    $graphifyArgs = @(
        'extract', $Target,
        '--backend', $backend,
        '--max-concurrency', $MaxConcurrency,
        '--token-budget', $TokenBudget
    )
    if ($model) { $graphifyArgs += @('--model', $model) }
    if ($Out) { $graphifyArgs += @('--out', $Out) }
    if ($Deep) { $graphifyArgs += @('--mode', 'deep') }
    if ($Wiki) { $graphifyArgs += '--wiki' }
    if ($Force) { $graphifyArgs += '--force' }

    Write-Host "Running Graphify semantic extraction ($SemanticProvider)..." -ForegroundColor Green
    Write-Host ''
    & graphify @graphifyArgs
    if ($LASTEXITCODE -ne 0) {
        throw "graphify exited with code $LASTEXITCODE"
    }
}
finally {
    if ($null -eq $previousGeminiKey) {
        Remove-Item Env:\GEMINI_API_KEY -ErrorAction SilentlyContinue
    } else {
        $env:GEMINI_API_KEY = $previousGeminiKey
    }
    if ($null -eq $previousOllamaKey) {
        Remove-Item Env:\OLLAMA_API_KEY -ErrorAction SilentlyContinue
    } else {
        $env:OLLAMA_API_KEY = $previousOllamaKey
    }
    if ($null -eq $previousOllamaBaseUrl) {
        Remove-Item Env:\OLLAMA_BASE_URL -ErrorAction SilentlyContinue
    } else {
        $env:OLLAMA_BASE_URL = $previousOllamaBaseUrl
    }
    $key = $null
}
