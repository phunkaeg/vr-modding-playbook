<#
.SYNOPSIS
  Re-extract every fleet document graph on the LAN model, one project at a time,
  without stopping at the first failure. Then reconcile.

.DESCRIPTION
  update-fleet-docs.ps1 throws on the first project that fails, which skips every
  project after it. Measured 2026-09-18: SOMAVR blocked the run and the remaining
  five never ran. This driver invokes it once per project so a block costs you
  that project and nothing else, logs everything, and prints a before/after table.

  WHY -Force IS NOT OPTIONAL HERE.
  The semantic cache is keyed by a fingerprint of the extraction PROMPT only
  (graphify cache.py, _resolve_prompt_fp). It does NOT record the backend or the
  model. So a cache entry written by Gemini is served to a later local run as if
  it were local output. Without -Force this script would replay yesterday's thin
  Gemini extractions and appear to have done the work.

  WHY LOCAL AT ALL. Measured on SOMAVR, 2026-09-18/19, same corpus, same prompt
  fingerprint (p5e80268fecd6), same graphify 0.9.63:
      gemini-3-flash-preview   354 nodes    744k in /  79k out  (ratio 0.11)
      coder-next (LAN)        1302 nodes    410k in / 653k out  (ratio 1.59)
  Gemini reads a batch of five documents and writes a summary; the local model
  truncates, gets recursively split down to one file per response, and enumerates.
  The variable is how much output each model spends per document, not quality.

  KNOWN CEILING. coder-next truncates on the largest documents even as a
  single-file chunk (ADDRESS_REGISTRY.md, BUILD_HISTORY.md). Those keep a partial
  result and are not cached as complete, so a later run retries them. Expect some
  large-document loss regardless of how long this runs.

  EXPECT GUARD TRIPS AND DO NOT FORCE PAST THEM. graphify refuses to replace a
  graph with a smaller one. That is correct behaviour and it has already saved two
  graphs. A trip here means the project keeps what it had.

.EXAMPLE
  pwsh -NoProfile -File .\run-fleet-local.ps1
  pwsh -NoProfile -File .\run-fleet-local.ps1 -Project somavr,preyvr
  pwsh -NoProfile -File .\run-fleet-local.ps1 -SkipReconcile
#>
#Requires -Version 7.0
[CmdletBinding()]
param(
    # Default order puts the small projects first, so an overnight run that is
    # interrupted has still finished something. The three biggest corpora
    # (ss2vr, preyvr, somavr) are last.
    [string[]] $Project = @('mohvr', 'sofvr', 'sims4vr', 'swat4vr', 'dishonoredvr',
                            'farcry2vr', 'bioshockvr', 'somavr', 'preyvr', 'ss2vr'),

    # Skip the cross-project pass. Note it uses GEMINI, not the LAN model, and
    # costs about $0.035 - it is the only paid step in this script.
    [switch] $SkipReconcile,

    # Bypass the semantic cache. On by default and you almost never want it off;
    # see WHY -Force IS NOT OPTIONAL above.
    [bool] $Force = $true
)

$ErrorActionPreference = 'Continue'
$here     = $PSScriptRoot
$driver   = Join-Path $here 'update-fleet-docs.ps1'
$stamp    = Get-Date -Format 'yyyy-MM-dd_HHmmss'
$logDir   = Join-Path $here 'logs'
$logFile  = Join-Path $logDir "fleet-local_$stamp.log"

if (-not (Test-Path -LiteralPath $driver)) { throw "driver not found: $driver" }
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Get-NodeCount([string] $proj) {
    $g = Join-Path $here "per-project\$proj\graphify-out\graph.json"
    if (-not (Test-Path -LiteralPath $g)) { return $null }
    try { return (Get-Content -LiteralPath $g -Raw | ConvertFrom-Json).nodes.Count }
    catch { return $null }
}

function Write-Both([string] $text, [string] $colour = 'Gray') {
    Write-Host $text -ForegroundColor $colour
    Add-Content -LiteralPath $logFile -Value $text
}

Write-Both "fleet local re-extraction  $stamp" 'Cyan'
Write-Both "log: $logFile"
Write-Both "projects: $($Project -join ', ')"
Write-Both ("force: {0}   reconcile: {1}" -f $Force, (-not $SkipReconcile))
Write-Both ''

$before = @{}
foreach ($p in $Project) { $before[$p] = Get-NodeCount $p }

$results = [System.Collections.Generic.List[object]]::new()
$i = 0
foreach ($p in $Project) {
    $i++
    $t0 = Get-Date
    Write-Both ("[{0}/{1}] {2}  starting {3}" -f $i, $Project.Count, $p, $t0.ToString('HH:mm:ss')) 'Cyan'

    # One invocation per project. The driver throws on failure; & with a try/catch
    # here turns that into a recorded result instead of the end of the run.
    $argsList = @('-Project', $p, '-SemanticProvider', 'local')
    if ($Force) { $argsList += '-Force' }

    $status = 'ok'
    try {
        & $driver @argsList 2>&1 | Tee-Object -FilePath $logFile -Append
        if ($LASTEXITCODE -ne 0) { $status = "exit $LASTEXITCODE" }
    } catch {
        # The driver's own `throw` lands here. The shrink guard is the usual
        # cause and it means the previous graph was preserved, not lost.
        $status = 'blocked'
        Add-Content -LiteralPath $logFile -Value ("EXCEPTION: " + $_.Exception.Message)
    }

    $mins  = [int]((Get-Date) - $t0).TotalMinutes
    $after = Get-NodeCount $p
    $delta = if ($null -ne $after -and $null -ne $before[$p]) { $after - $before[$p] } else { $null }

    # A "blocked" project whose count still rose means an early attempt WROTE and
    # a later retry was refused - that is a success, not a failure. Measured on
    # SOMAVR 2026-09-19: it reported failure after writing 410 -> 1302.
    if ($status -ne 'ok' -and $null -ne $delta -and $delta -gt 0) { $status = "wrote, retries refused" }

    $results.Add([pscustomobject]@{
        Project = $p; Before = $before[$p]; After = $after; Delta = $delta
        Minutes = $mins; Status = $status
    })
    Write-Both ("[{0}/{1}] {2}  {3}  {4} -> {5}  ({6} min)" -f `
        $i, $Project.Count, $p, $status, $before[$p], $after, $mins) `
        $(if ($status -eq 'ok' -or $status -like 'wrote*') { 'Green' } else { 'Yellow' })
    Write-Both ''
}

if (-not $SkipReconcile) {
    Write-Both '=== reconcile (GEMINI, ~$0.035) ===' 'Cyan'
    # -Reconcile only runs when a semantic pass ran in the same invocation, so it
    # rides on the smallest project. Everything is cached by now, so that pass is
    # free and instant; only the cross-project resolution costs anything.
    try {
        & $driver -Project mohvr -Reconcile 2>&1 | Tee-Object -FilePath $logFile -Append
    } catch {
        Write-Both ("reconcile failed: " + $_.Exception.Message) 'Red'
    }
}

Write-Both ''
Write-Both '================ summary ================' 'Cyan'
$table = $results | Format-Table -AutoSize | Out-String
Write-Both $table
$grew = ($results | Where-Object { $_.Delta -gt 0 }).Count
$held = ($results | Where-Object { $_.Status -eq 'blocked' }).Count
Write-Both ("{0} grew, {1} held by the shrink guard, {2} total" -f $grew, $held, $results.Count)
Write-Both "full log: $logFile"
Write-Both ''
Write-Both 'A held project kept its previous graph. Do NOT pass --allow-partial to' 'Yellow'
Write-Both 'force one through: the guard has blocked a real 56-node regression and a' 'Yellow'
Write-Both 'harmless 5-node wobble this week, and it cannot tell you which is which.' 'Yellow'
