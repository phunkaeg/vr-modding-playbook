<#
.SYNOPSIS
  Refresh this in-house mod's code structure and document semantics.

.DESCRIPTION
  First normalizes the deterministic code tier, preserving semantic nodes, then
  incrementally refreshes document semantics in this project's mixed graph.
  Gemini is the default. Use -SemanticProvider local to run coder-next,
  gemma4-26b, or another model advertised by the trusted LAN endpoint.

.EXAMPLE
  .\Graphify-Update-All.ps1

.EXAMPLE
  .\Graphify-Update-All.ps1 -SemanticProvider local -LocalModel coder-next

.EXAMPLE
  .\Graphify-Update-All.ps1 -SemanticProvider local -LocalModel gemma4-26b -Deep
#>

[CmdletBinding()]
param(
    [ValidateSet('gemini', 'local')]
    [string] $SemanticProvider = 'gemini',

    [string] $LocalModel = 'coder-next',

    [ValidatePattern('^https?://')]
    [string] $LocalBaseUrl = 'http://192.168.0.161:8080/v1',

    [string] $LocalKeyFile,

    [switch] $Deep,

    [switch] $Wiki,

    [switch] $Force,

    [switch] $UpdateGraphify,

    [ValidateRange(1000, 1000000)]
    [int] $TokenBudget = 20000,

    [ValidateRange(1, 32)]
    [int] $MaxConcurrency = 2
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSCommandPath
$fleetUpdater = 'D:\Dev Debug\VR Modding\cross-engine-graph\update-fleet-docs.ps1'

if (-not (Test-Path -LiteralPath $fleetUpdater -PathType Leaf)) {
    throw "Fleet Graphify updater not found: $fleetUpdater"
}

$invokeArgs = @{
    ProjectRoot = $projectRoot
    NormalizeCode = $true
    ProjectGraph = $true
    SemanticProvider = $SemanticProvider
    LocalModel = $LocalModel
    LocalBaseUrl = $LocalBaseUrl
    TokenBudget = $TokenBudget
}
if ($PSBoundParameters.ContainsKey('MaxConcurrency')) {
    $invokeArgs.MaxConcurrency = $MaxConcurrency
}
if ($LocalKeyFile) { $invokeArgs.LocalKeyFile = $LocalKeyFile }
if ($Deep) { $invokeArgs.Deep = $true }
if ($Wiki) { $invokeArgs.Wiki = $true }
if ($Force) { $invokeArgs.Force = $true }
if ($UpdateGraphify) { $invokeArgs.UpdateGraphify = $true }

& $fleetUpdater @invokeArgs
