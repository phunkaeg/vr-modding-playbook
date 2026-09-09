[CmdletBinding()]
param(
    [ValidateSet('Prepare','Install','Check')][string]$Mode = 'Prepare',
    [Parameter(Mandatory)][string]$Stage
)
$ErrorActionPreference = 'Stop'
$playbookRoot = Split-Path $PSScriptRoot -Parent
$stageRoot = [IO.Path]::GetFullPath($Stage)
$allowedStage = Join-Path $playbookRoot '.guidance-staging'
if (-not $stageRoot.StartsWith($allowedStage + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Stage must be a child of the playbook .guidance-staging directory'
}
$utf8 = [Text.UTF8Encoding]::new($false, $true)
$markerStart = '<!-- vr-research-integration:start -->'
$markerEnd = '<!-- vr-research-integration:end -->'
$entry = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'agent-guidance/entry-block.md'))
$skillBlock = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'agent-guidance/skill-block.md'))
$newSkill = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'agent-guidance/vr-research-receipts/SKILL.md'))
$fleetSection = ([IO.File]::ReadAllText((Join-Path $playbookRoot 'sources.yml')) -split '(?m)^external:')[0]
$fleetRoots = @([regex]::Matches($fleetSection, '(?m)^    root: "([^"]+)"') | ForEach-Object { [IO.Path]::GetFullPath($_.Groups[1].Value) })
if ($fleetRoots.Count -ne 10) { throw 'Fleet changed: review installer scope before extending it' }
$targets = @()
foreach ($projectRoot in $fleetRoots) {
    foreach ($name in @('AGENTS.md','CLAUDE.md')) {
        $path = Join-Path $projectRoot $name
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing pair: $path" }
        $targets += @{ Path=$path; Block=$entry; Replace=$false }
    }
    $codexGuide = Join-Path $projectRoot 'CODEX.md'
    if (Test-Path -LiteralPath $codexGuide -PathType Leaf) { $targets += @{ Path=$codexGuide; Block=$entry; Replace=$false } }
}
foreach ($profile in @(@{Dir='C:\Users\meise\.codex'; Guide='AGENTS.md'}, @{Dir='C:\Users\meise\.claude'; Guide='CLAUDE.md'})) {
    $targets += @{ Path=(Join-Path $profile.Dir $profile.Guide); Block=$entry; Replace=$false }
    $targets += @{ Path=(Join-Path $profile.Dir 'skills/vr-re-workflow/SKILL.md'); Block=$skillBlock; Replace=$false }
    $targets += @{ Path=(Join-Path $profile.Dir 'skills/vr-research-receipts/SKILL.md'); Block=$newSkill; Replace=$true }
}
function FileHash($path) {
    if (Test-Path -LiteralPath $path -PathType Leaf) { return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash }
    return $null
}
$manifestPath = Join-Path $stageRoot 'manifest.json'
if ($Mode -eq 'Prepare') {
    if (Test-Path -LiteralPath $stageRoot) { throw 'Choose a new stage; previous backups are immutable' }
    New-Item -ItemType Directory -Path $stageRoot | Out-Null
    $records = @()
    foreach ($target in $targets) {
        $path = $target.Path
        $before = FileHash $path
        if (-not $before -and -not $target.Replace) { throw "Missing existing guide: $path" }
        $old = if ($before) { [IO.File]::ReadAllText($path, $utf8) } else { '' }
        $newline = if ($old.Contains("`r`n")) { "`r`n" } else { "`n" }
        $block = ($target.Block -replace "`r?`n", $newline).TrimEnd()
        if ($target.Replace) { $updated = $block + $newline }
        elseif ($old.Contains($markerStart)) {
            if ([regex]::Matches($old, [regex]::Escape($markerStart)).Count -ne 1 -or [regex]::Matches($old, [regex]::Escape($markerEnd)).Count -ne 1) { throw "Ambiguous managed markers: $path" }
            $pattern = '(?s)' + [regex]::Escape($markerStart) + '.*?' + [regex]::Escape($markerEnd)
            $updated = [regex]::Replace($old, $pattern, [Text.RegularExpressions.MatchEvaluator]{ param($match) $block })
        }
        else { $updated = $old + $newline + $newline + $block + $newline }
        $index = $records.Count.ToString('D2')
        $draft = Join-Path $stageRoot "$index.draft"
        $backup = Join-Path $stageRoot "$index.original"
        if ($before) { Copy-Item -LiteralPath $path -Destination $backup }
        $hadBom = $false
        if ($before) {
            $originalBytes = [IO.File]::ReadAllBytes($path)
            $hadBom = $originalBytes.Length -ge 3 -and $originalBytes[0] -eq 239 -and $originalBytes[1] -eq 187 -and $originalBytes[2] -eq 191
        }
        [IO.File]::WriteAllText($draft, $updated, [Text.UTF8Encoding]::new([bool]$hadBom))
        if ((FileHash $path) -ne $before) { throw "Concurrent edit during preparation: $path" }
        $records += [ordered]@{path=$path; before=$before; after=(FileHash $draft); draft=$draft; backup=$backup}
    }
    [IO.File]::WriteAllText($manifestPath, (ConvertTo-Json -InputObject $records -Depth 5), $utf8)
    Write-Output "PREPARED $($records.Count) files: $manifestPath"
    exit 0
}
$records = @(Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json)
$allowed = @($targets | ForEach-Object { $_.Path })
if ($records.Count -ne $allowed.Count -or @($records.path | Select-Object -Unique).Count -ne $allowed.Count) { throw 'Manifest target count mismatch' }
foreach ($record in $records) {
    if ($record.path -notin $allowed) { throw "Out-of-scope destination: $($record.path)" }
    if (-not [IO.Path]::GetFullPath($record.draft).StartsWith($stageRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Draft escapes staging' }
    if ((FileHash $record.draft) -ne $record.after) { throw "Changed draft: $($record.draft)" }
    $expected = if ($Mode -eq 'Check') { $record.after } else { $record.before }
    if ((FileHash $record.path) -ne $expected) { throw "Concurrent or unexpected edit: $($record.path)" }
}
if ($Mode -eq 'Install') {
    foreach ($record in $records) {
        if ((FileHash $record.path) -ne $record.before) { throw "Concurrent edit: $($record.path)" }
        $parent = Split-Path $record.path -Parent
        if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent | Out-Null }
        Copy-Item -LiteralPath $record.draft -Destination $record.path
        if ((FileHash $record.path) -ne $record.after) { throw "Installation mismatch: $($record.path)" }
    }
}
Write-Output "$Mode verified $($records.Count) files; backups and hashes: $manifestPath"
