<#
.SYNOPSIS
  Stage and incrementally refresh semantic document graphs for the in-house VR fleet.

.DESCRIPTION
  This is the semantic companion to Graphify's deterministic code extraction.
  It builds one document corpus and one Graphify output per project so same-named
  entities cannot collide across projects. Gemini is the default semantics
  provider; the trusted LAN OpenAI-compatible endpoint is also supported.

  Credentials are loaded by run-graphify.ps1 from process scope or user-local
  configuration. Keys are never printed, persisted in the repository, or passed
  on a command line.

.EXAMPLE
  # Free audit: no staging, API calls, or writes.
  .\update-fleet-docs.ps1 -WhatIfCost

.EXAMPLE
  # Normalize every project code graph under the current Graphify version,
  # preserving semantic nodes, then refresh changed fleet documents.
  .\update-fleet-docs.ps1 -NormalizeCode

.EXAMPLE
  # Refresh just two projects.
  .\update-fleet-docs.ps1 -Project farcry2vr,swat4vr

.EXAMPLE
  # Rebuild every document for one project, bypassing the manifest cache.
  .\update-fleet-docs.ps1 -Project sims4vr -Force
#>

[CmdletBinding()]
param(
    [string[]] $Project,

    # Select the fleet entry whose configured root matches this path. This is
    # used by identical project-local shortcut scripts.
    [string] $ProjectRoot,

    # Report corpus sizes without staging or calling a semantic provider.
    [switch] $WhatIfCost,

    # Refresh corpus snapshots but do not call a semantic provider.
    [switch] $StageOnly,

    # Update each project's own mixed code+document graph instead of the
    # curated per-project documentation graphs under this directory.
    [switch] $ProjectGraph,

    # Bypass Graphify's incremental semantic cache.
    [switch] $Force,

    # Upgrade the Graphify CLI package, then reinstall matching Codex and Claude
    # skills before doing any graph work.
    [switch] $UpdateGraphify,

    [ValidateSet('codex', 'claude')]
    [string[]] $GraphifyPlatform = @('codex', 'claude'),

    # Before the semantic pass, fully rescan project code under the installed
    # Graphify version while carrying each graph's semantic tier forward.
    [switch] $NormalizeCode,

    # Refresh only deterministic code structure, preserving any existing
    # semantic/document tier, then stop without staging or invoking an LLM.
    [switch] $CodeOnly,

    [ValidateSet('gemini', 'local')]
    [string] $SemanticProvider = 'gemini',

    [string] $LocalModel = 'coder-next',

    [ValidatePattern('^https?://')]
    [string] $LocalBaseUrl = 'http://192.168.0.161:8080/v1',

    [string] $LocalKeyFile,

    [switch] $Deep,

    [switch] $Wiki,

    [ValidateRange(1000, 1000000)]
    [int] $TokenBudget = 20000,

    [ValidateRange(1, 32)]
    [int] $MaxConcurrency = 2,

    # An LLM can occasionally return an empty result for an otherwise valid file.
    # Graphify 0.9.53 re-queues those files, so two cheap incremental retries
    # normally close the gap without reprocessing successful documents.
    [ValidateRange(0, 5)]
    [int] $SemanticRetries = 2
)

$ErrorActionPreference = 'Stop'

if ($SemanticProvider -eq 'local' -and -not $PSBoundParameters.ContainsKey('MaxConcurrency')) {
    # A single LAN GPU is normally more reliable with one semantics request at
    # a time. Explicit -MaxConcurrency still wins.
    $MaxConcurrency = 1
}

$fleet = @(
    [pscustomobject]@{ Id = 'ss2vr';        Name = 'SS2VR';        Root = 'D:\Dev Debug\ss2vr-work';   IncludeCaptures = $false; GraphTarget = 'D:\Dev Debug\ss2vr-work';                         GraphOut = 'D:\Dev Debug\ss2vr-work';             PreStage = $null }
    [pscustomobject]@{ Id = 'bioshockvr';   Name = 'BioShockVR';   Root = 'D:\Dev Debug\BioshockVR';   IncludeCaptures = $false; GraphTarget = 'D:\Dev Debug\BioshockVR';                         GraphOut = 'D:\Dev Debug\BioshockVR';             PreStage = $null }
    [pscustomobject]@{ Id = 'somavr';       Name = 'SOMAVR';       Root = 'D:\Dev Debug\SOMAVR';       IncludeCaptures = $false; GraphTarget = 'D:\Dev Debug\SOMAVR';                             GraphOut = 'D:\Dev Debug\SOMAVR';                 PreStage = $null }
    [pscustomobject]@{ Id = 'preyvr';       Name = 'PreyVR';       Root = 'D:\Dev Debug\PreyVR';       IncludeCaptures = $true;  GraphTarget = 'D:\Dev Debug\PreyVR\graphify\corpus\preyvr'; GraphOut = 'D:\Dev Debug\PreyVR\graphify';        PreStage = 'D:\Dev Debug\PreyVR\graphify\stage-corpus.ps1' }
    [pscustomobject]@{ Id = 'dishonoredvr'; Name = 'DishonoredVR'; Root = 'D:\Dev Debug\DishonoredVR'; IncludeCaptures = $false; GraphTarget = 'D:\Dev Debug\DishonoredVR';                       GraphOut = 'D:\Dev Debug\DishonoredVR';           PreStage = $null }
    [pscustomobject]@{ Id = 'farcry2vr';    Name = 'FarCry2VR';    Root = 'D:\Dev Debug\FarCry2-vr';   IncludeCaptures = $false; GraphTarget = 'D:\Dev Debug\FarCry2-vr';                         GraphOut = 'D:\Dev Debug\FarCry2-vr';             PreStage = $null }
    [pscustomobject]@{ Id = 'swat4vr';      Name = 'SWAT4VR';      Root = 'D:\Dev Debug\Swat4-VR';     IncludeCaptures = $false; GraphTarget = 'D:\Dev Debug\Swat4-VR';                           GraphOut = 'D:\Dev Debug\Swat4-VR';               PreStage = $null }
    [pscustomobject]@{ Id = 'sims4vr';      Name = 'Sims4VR';      Root = 'D:\Dev Debug\Sims4VR';      IncludeCaptures = $false; GraphTarget = 'D:\Dev Debug\Sims4VR';                            GraphOut = 'D:\Dev Debug\Sims4VR';                PreStage = $null }
)

$knownIds = @($fleet.Id)
if ($Project -and $ProjectRoot) {
    throw '-Project and -ProjectRoot are mutually exclusive.'
}
if ($Project) {
    $unknown = @($Project | Where-Object { $_ -notin $knownIds })
    if ($unknown.Count -gt 0) {
        throw "Unknown project id(s): $($unknown -join ', '). Valid ids: $($knownIds -join ', ')"
    }
    $fleet = @($fleet | Where-Object { $_.Id -in $Project })
}
if ($ProjectRoot) {
    if (-not (Test-Path -LiteralPath $ProjectRoot -PathType Container)) {
        throw "Project root not found: $ProjectRoot"
    }
    $selectedRoot = [IO.Path]::GetFullPath($ProjectRoot).TrimEnd([char[]]'\/')
    $fleet = @($fleet | Where-Object {
        [IO.Path]::GetFullPath($_.Root).TrimEnd([char[]]'\/').Equals(
            $selectedRoot,
            [StringComparison]::OrdinalIgnoreCase
        )
    })
    if ($fleet.Count -ne 1) {
        throw "No fleet project is configured for root: $selectedRoot"
    }
}

$corpusRoot = Join-Path $PSScriptRoot 'corpus'
$outputRoot = Join-Path $PSScriptRoot 'per-project'
$runner = Join-Path $PSScriptRoot 'run-graphify.ps1'

function Update-GraphifyInstallation {
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if ($null -eq $uv) {
        throw 'uv was not found on PATH, so the Graphify CLI package cannot be upgraded.'
    }

    Write-Host 'Upgrading the Graphify CLI package...' -ForegroundColor Cyan
    & $uv.Source tool upgrade graphifyy
    if ($LASTEXITCODE -ne 0) {
        throw "uv tool upgrade graphifyy exited with code $LASTEXITCODE"
    }

    foreach ($platform in $GraphifyPlatform) {
        Write-Host "Installing the matching Graphify $platform skill..." -ForegroundColor Cyan
        & graphify install --platform $platform
        if ($LASTEXITCODE -ne 0) {
            throw "graphify install --platform $platform exited with code $LASTEXITCODE"
        }
    }

    Write-Host 'Installed Graphify version:' -ForegroundColor Green
    & graphify --version
    if ($LASTEXITCODE -ne 0) {
        throw "graphify --version exited with code $LASTEXITCODE"
    }
}

if ($UpdateGraphify) {
    Update-GraphifyInstallation
}

function Assert-GeneratedChildPath {
    param(
        [Parameter(Mandatory = $true)][string] $Parent,
        [Parameter(Mandatory = $true)][string] $Child
    )

    $parentFull = [IO.Path]::GetFullPath($Parent).TrimEnd([char[]]'\/') + [IO.Path]::DirectorySeparatorChar
    $childFull = [IO.Path]::GetFullPath($Child).TrimEnd([char[]]'\/')
    if (-not $childFull.StartsWith($parentFull, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to replace a path outside the generated corpus: $childFull"
    }
}

function Get-ProjectDocuments {
    param([Parameter(Mandatory = $true)] $Entry)

    if (-not (Test-Path -LiteralPath $Entry.Root)) {
        throw "Project root not found: $($Entry.Root)"
    }

    $files = @()
    $docsRoot = Join-Path $Entry.Root 'docs'
    if (Test-Path -LiteralPath $docsRoot) {
        $files += @(Get-ChildItem -LiteralPath $docsRoot -Recurse -File |
            Where-Object { $_.Extension -in @('.md', '.txt') })
    }

    foreach ($rootName in @('README.md', 'AGENTS.md', 'CLAUDE.md')) {
        $rootFile = Join-Path $Entry.Root $rootName
        if (Test-Path -LiteralPath $rootFile) {
            $files += Get-Item -LiteralPath $rootFile
        }
    }

    # Prey records high-value live observations as Markdown capture receipts.
    if ($Entry.IncludeCaptures) {
        $captureRoot = Join-Path $Entry.Root 'captures\traces'
        if (Test-Path -LiteralPath $captureRoot) {
            $files += @(Get-ChildItem -LiteralPath $captureRoot -Recurse -File -Filter '*.md')
        }
    }

    # Chronological user-test logs are very large and low-signal for retrieval.
    return @($files |
        Where-Object { $_.Name -notmatch '(?i)USER_TEST_LOG' } |
        Sort-Object FullName -Unique)
}

function Stage-ProjectDocuments {
    param(
        [Parameter(Mandatory = $true)] $Entry,
        [Parameter(Mandatory = $true)][IO.FileInfo[]] $Files
    )

    New-Item -ItemType Directory -Path $corpusRoot -Force | Out-Null
    $target = Join-Path $corpusRoot $Entry.Id
    $temp = Join-Path $corpusRoot ('.staging-{0}-{1}' -f $Entry.Id, [guid]::NewGuid().ToString('N'))
    Assert-GeneratedChildPath -Parent $corpusRoot -Child $target
    Assert-GeneratedChildPath -Parent $corpusRoot -Child $temp
    New-Item -ItemType Directory -Path $temp | Out-Null

    # Documents under docs/ retain their historical corpus-relative paths so
    # existing semantic cache entries remain reusable. If a root-level project
    # document has the same relative name, keep both by namespacing the root copy.
    $docsRoot = Join-Path $Entry.Root 'docs'
    $docsRootFull = [IO.Path]::GetFullPath($docsRoot).TrimEnd([char[]]'\/') + [IO.Path]::DirectorySeparatorChar
    $docsRelativePaths = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    foreach ($file in $Files) {
        if ($file.FullName.StartsWith($docsRootFull, [StringComparison]::OrdinalIgnoreCase)) {
            [void]$docsRelativePaths.Add([IO.Path]::GetRelativePath($docsRoot, $file.FullName))
        }
    }

    try {
        foreach ($file in $Files) {
            if ($file.FullName.StartsWith($docsRootFull, [StringComparison]::OrdinalIgnoreCase)) {
                # Keep the original three-project corpus' top-level filenames
                # stable so existing semantic cache entries remain reusable.
                $relative = [IO.Path]::GetRelativePath($docsRoot, $file.FullName)
            } else {
                $relative = [IO.Path]::GetRelativePath($Entry.Root, $file.FullName)
                if ($docsRelativePaths.Contains($relative)) {
                    $relative = Join-Path '_project' $relative
                }
            }
            if ($relative.StartsWith('..')) {
                throw "Document escaped project root: $($file.FullName)"
            }
            $destination = Join-Path $temp $relative
            New-Item -ItemType Directory -Path (Split-Path $destination -Parent) -Force | Out-Null
            Copy-Item -LiteralPath $file.FullName -Destination $destination
        }

        if (Test-Path -LiteralPath $target) {
            Remove-Item -LiteralPath $target -Recurse -Force
        }
        Move-Item -LiteralPath $temp -Destination $target
    }
    finally {
        if (Test-Path -LiteralPath $temp) {
            Remove-Item -LiteralPath $temp -Recurse -Force
        }
    }

    return $target
}

function Get-DocumentGraphStatus {
    param(
        [Parameter(Mandatory = $true)][string] $Stage,
        [Parameter(Mandatory = $true)][string] $GraphPath
    )

    $graph = Get-Content -LiteralPath $GraphPath -Raw | ConvertFrom-Json
    $sourceValues = @()
    $sourceValues += @($graph.nodes | ForEach-Object { $_.source_file })
    $sourceValues += @($graph.links | ForEach-Object { $_.source_file })
    $sourceValues += @($graph.hyperedges | ForEach-Object { $_.source_file })
    $sources = @(
        $sourceValues |
            Where-Object { $_ } |
            ForEach-Object { ($_ -replace '\\', '/').ToLowerInvariant() } |
            Sort-Object -Unique
    )
    $documents = @(
        Get-ChildItem -LiteralPath $Stage -Recurse -File |
            Where-Object { $_.Extension -in @('.md', '.txt') }
    )
    $missing = @()
    foreach ($file in $documents) {
        $relative = [IO.Path]::GetRelativePath($Stage, $file.FullName).Replace('\', '/').ToLowerInvariant()
        $represented = @(
            $sources | Where-Object { $_ -eq $relative -or $_.EndsWith('/' + $relative) }
        ).Count -gt 0
        if (-not $represented) { $missing += $relative }
    }

    return [pscustomobject]@{
        Graph = $graph
        Documents = $documents.Count
        Missing = $missing
    }
}

$preStaged = @{}

function Invoke-ProjectPreStage {
    param([Parameter(Mandatory = $true)] $Entry)

    if (-not $Entry.PreStage -or $preStaged.ContainsKey($Entry.Id)) { return }
    Write-Host "`nRefreshing $($Entry.Name)'s project-local corpus..." -ForegroundColor Cyan
    & $Entry.PreStage -SharedCorpus $corpusRoot
    $preStaged[$Entry.Id] = $true
}

function Invoke-CodeNormalization {
    param([Parameter(Mandatory = $true)] $Entry)

    Invoke-ProjectPreStage -Entry $Entry

    $graphPath = Join-Path $Entry.GraphOut 'graphify-out\graph.json'
    $beforeNodes = 0
    $beforeDocs = 0
    $beforeDocFiles = @()
    if (Test-Path -LiteralPath $graphPath) {
        $before = Get-Content -LiteralPath $graphPath -Raw | ConvertFrom-Json
        $beforeNodes = @($before.nodes).Count
        $beforeDocs = @($before.nodes | Where-Object { $_.source_file -match '\.(md|mdx|rst|adoc|txt)$' }).Count
        $beforeDocFiles = @(
            $before.nodes |
                Where-Object { $_.source_file -match '\.(md|mdx|rst|adoc|txt)$' } |
                ForEach-Object { $_.source_file } |
                Sort-Object -Unique
        )
    }

    Write-Host "`nNormalizing $($Entry.Name) code under the installed Graphify version..." -ForegroundColor Cyan
    & graphify extract $Entry.GraphTarget --force --code-only --out $Entry.GraphOut
    if ($LASTEXITCODE -ne 0) {
        throw "Graphify code normalization failed for $($Entry.Name) with code $LASTEXITCODE"
    }
    if (-not (Test-Path -LiteralPath $graphPath)) {
        throw "Graphify completed without producing $graphPath"
    }

    $after = Get-Content -LiteralPath $graphPath -Raw | ConvertFrom-Json
    $afterNodes = @($after.nodes).Count
    $afterDocs = @($after.nodes | Where-Object { $_.source_file -match '\.(md|mdx|rst|adoc|txt)$' }).Count
    $afterDocFiles = @(
        $after.nodes |
            Where-Object { $_.source_file -match '\.(md|mdx|rst|adoc|txt)$' } |
            ForEach-Object { $_.source_file } |
            Sort-Object -Unique
    )
    $lostDocFiles = @(
        Compare-Object -ReferenceObject $beforeDocFiles -DifferenceObject $afterDocFiles |
            Where-Object { $_.SideIndicator -eq '<=' } |
            ForEach-Object { $_.InputObject }
    )
    if ($lostDocFiles.Count -gt 0) {
        throw "$($Entry.Name) lost semantic/document source coverage during code-only normalization: $($lostDocFiles -join ', ')"
    }
    if ($beforeDocs -gt 0 -and $afterDocs -lt $beforeDocs) {
        Write-Host ("  note: Graphify consolidated {0:N0} duplicate document/concept node(s); all {1:N0} source documents remain represented" -f ($beforeDocs - $afterDocs), $afterDocFiles.Count) -ForegroundColor Yellow
    }

    Write-Host ("  verified: {0:N0} -> {1:N0} nodes; {2:N0} document/concept nodes across {3:N0} source documents" -f $beforeNodes, $afterNodes, $afterDocs, $afterDocFiles.Count) -ForegroundColor Green
}

$totalFiles = 0
$totalBytes = 0L
$plans = @()

foreach ($entry in $fleet) {
    $files = @(Get-ProjectDocuments -Entry $entry)
    $bytes = [long](($files | Measure-Object Length -Sum).Sum)
    $tokens = [math]::Round($bytes / 3.75)
    $totalFiles += $files.Count
    $totalBytes += $bytes
    $plans += [pscustomobject]@{ Entry = $entry; Files = $files; Bytes = $bytes; Tokens = $tokens }
    Write-Host ('{0,-14} {1,4} files  {2,10:N0} bytes  ~{3,9:N0} input tokens' -f $entry.Name, $files.Count, $bytes, $tokens)
}

Write-Host ('{0,-14} {1,4} files  {2,10:N0} bytes  ~{3,9:N0} input tokens' -f 'TOTAL', $totalFiles, $totalBytes, [math]::Round($totalBytes / 3.75))
if ($WhatIfCost) {
    Write-Host 'Dry run only: no corpus files changed and no semantic-provider calls made.' -ForegroundColor Yellow
    return
}

if ($ProjectGraph -and $StageOnly) {
    throw '-ProjectGraph and -StageOnly are mutually exclusive; project graphs do not use the shared staged-docs corpus.'
}
if ($CodeOnly -and ($ProjectGraph -or $StageOnly -or $Force)) {
    throw '-CodeOnly cannot be combined with -ProjectGraph, -StageOnly, or -Force.'
}

if ($CodeOnly) {
    foreach ($plan in $plans) {
        Invoke-CodeNormalization -Entry $plan.Entry
    }
    Write-Host "`nSelected project code graphs are current; existing semantic nodes were preserved." -ForegroundColor Green
    return
}

if ($NormalizeCode) {
    foreach ($plan in $plans) {
        Invoke-CodeNormalization -Entry $plan.Entry
    }
}

if ($ProjectGraph) {
    foreach ($plan in $plans) {
        $entry = $plan.Entry
        Invoke-ProjectPreStage -Entry $entry

        Write-Host "`nUpdating $($entry.Name)'s mixed project graph semantics via $SemanticProvider..." -ForegroundColor Cyan
        $runArgs = @{
            Target = $entry.GraphTarget
            Out = $entry.GraphOut
            TokenBudget = $TokenBudget
            MaxConcurrency = $MaxConcurrency
            SemanticProvider = $SemanticProvider
            LocalModel = $LocalModel
            LocalBaseUrl = $LocalBaseUrl
        }
        if ($LocalKeyFile) { $runArgs.LocalKeyFile = $LocalKeyFile }
        if ($Deep) { $runArgs.Deep = $true }
        if ($Wiki) { $runArgs.Wiki = $true }
        if ($Force) { $runArgs.Force = $true }
        & $runner @runArgs

        $graphPath = Join-Path $entry.GraphOut 'graphify-out\graph.json'
        if (-not (Test-Path -LiteralPath $graphPath)) {
            throw "Graphify completed without producing $graphPath"
        }
        $graph = Get-Content -LiteralPath $graphPath -Raw | ConvertFrom-Json
        Write-Host ("  verified: {0:N0} nodes, {1:N0} links" -f @($graph.nodes).Count, @($graph.links).Count) -ForegroundColor Green
    }
    Write-Host "`nSelected mixed project graphs are semantically current." -ForegroundColor Green
    return
}

foreach ($plan in $plans) {
    $entry = $plan.Entry
    Write-Host "`nStaging $($entry.Name)..." -ForegroundColor Cyan
    $stage = Stage-ProjectDocuments -Entry $entry -Files $plan.Files
    Write-Host "  $($plan.Files.Count) files -> $stage"

    if ($StageOnly) { continue }

    $out = Join-Path $outputRoot $entry.Id
    $runArgs = @{
        Target = $stage
        Out = $out
        TokenBudget = $TokenBudget
        MaxConcurrency = $MaxConcurrency
        SemanticProvider = $SemanticProvider
        LocalModel = $LocalModel
        LocalBaseUrl = $LocalBaseUrl
    }
    if ($LocalKeyFile) { $runArgs.LocalKeyFile = $LocalKeyFile }
    if ($Deep) { $runArgs.Deep = $true }
    if ($Wiki) { $runArgs.Wiki = $true }
    if ($Force) { $runArgs.Force = $true }

    $graphPath = Join-Path $out 'graphify-out\graph.json'
    $status = $null
    $lastFailure = $null
    $maxAttempts = 1 + $SemanticRetries
    for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
        try {
            & $runner @runArgs
            $lastFailure = $null
        }
        catch {
            $lastFailure = $_
        }

        if (Test-Path -LiteralPath $graphPath) {
            $status = Get-DocumentGraphStatus -Stage $stage -GraphPath $graphPath
        }

        if ($null -eq $lastFailure -and $null -ne $status -and $status.Missing.Count -eq 0) {
            break
        }
        if ($attempt -ge $maxAttempts) {
            if ($null -ne $lastFailure) {
                throw "Graphify remained incomplete for $($entry.Name) after $maxAttempts attempt(s): $($lastFailure.Exception.Message)"
            }
            break
        }

        $reason = if ($null -ne $lastFailure) {
            'the shrink guard preserved the previous graph'
        } elseif ($null -eq $status) {
            'no graph was produced'
        } else {
            "$($status.Missing.Count) staged document(s) have no surviving provenance"
        }
        Write-Host "  retrying incrementally ($attempt/$maxAttempts): $reason" -ForegroundColor Yellow

        # A forced first pass should still use cheap incremental retries.
        [void]$runArgs.Remove('Force')
    }

    if ($null -eq $status) {
        throw "Graphify completed without producing $graphPath"
    }
    if ($status.Missing.Count -gt 0) {
        Write-Host ("  warning: {0:N0} staged document(s) have no surviving node/edge provenance after {1} attempt(s): {2}" -f $status.Missing.Count, $maxAttempts, ($status.Missing -join ', ')) -ForegroundColor Yellow
    }
    $represented = $status.Documents - $status.Missing.Count
    Write-Host ("  verified: {0:N0} nodes, {1:N0} links, {2}/{3} staged files represented" -f @($status.Graph.nodes).Count, @($status.Graph.links).Count, $represented, $status.Documents) -ForegroundColor Green
}

if ($StageOnly) {
    Write-Host "`nCorpus staged; no semantic provider was called." -ForegroundColor Yellow
} else {
    Write-Host "`nPer-project semantic document graphs are current for the selected fleet entries." -ForegroundColor Green
    Write-Host 'The reconciled cross-project graph remains a separate, explicit step; unioning graphs does not create cross-project concept edges.'
}
