<#
Compatibility entry point. The old script called a stale bare-path Graphify CLI
form and could be mistaken for a safe project update. Keep the familiar filename,
but delegate to the same guarded fleet workflow as every other in-house mod.
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

    [switch] $UpdateGraphify
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$runner = Join-Path $projectRoot 'Graphify-Update-All.ps1'

if (-not (Test-Path -LiteralPath $runner -PathType Leaf)) {
    throw "Safe Graphify project runner not found: $runner"
}

Write-Host 'Using the guarded fleet Graphify update strategy.' -ForegroundColor Cyan
$invokeArgs = @{
    SemanticProvider = $SemanticProvider
    LocalModel = $LocalModel
    LocalBaseUrl = $LocalBaseUrl
}
if ($LocalKeyFile) { $invokeArgs.LocalKeyFile = $LocalKeyFile }
if ($Deep) { $invokeArgs.Deep = $true }
if ($Wiki) { $invokeArgs.Wiki = $true }
if ($Force) { $invokeArgs.Force = $true }
if ($UpdateGraphify) { $invokeArgs.UpdateGraphify = $true }

& $runner @invokeArgs
