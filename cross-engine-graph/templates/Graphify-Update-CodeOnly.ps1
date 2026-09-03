<#
.SYNOPSIS
  Refresh this in-house mod's deterministic code graph without an LLM.

.DESCRIPTION
  Delegates to the fleet updater so every project uses the same Graphify command,
  shrink guards, document-provenance check, and optional package upgrade path.
  Existing semantic/document nodes are carried forward.

.EXAMPLE
  .\Graphify-Update-CodeOnly.ps1

.EXAMPLE
  .\Graphify-Update-CodeOnly.ps1 -UpdateGraphify
#>

[CmdletBinding()]
param(
    [switch] $UpdateGraphify
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSCommandPath
$fleetUpdater = 'D:\Dev Debug\VR Modding\cross-engine-graph\update-fleet-docs.ps1'

if (-not (Test-Path -LiteralPath $fleetUpdater -PathType Leaf)) {
    throw "Fleet Graphify updater not found: $fleetUpdater"
}

$invokeArgs = @{
    ProjectRoot = $projectRoot
    CodeOnly = $true
}
if ($UpdateGraphify) { $invokeArgs.UpdateGraphify = $true }

& $fleetUpdater @invokeArgs
