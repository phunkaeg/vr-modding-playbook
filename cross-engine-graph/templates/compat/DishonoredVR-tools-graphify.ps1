[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('stage', 'extract', 'query')]
    [string] $Command = 'stage',

    [switch] $IncludeSharedCorpus,

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

    [string] $Question
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$docsRoot = Join-Path $repositoryRoot 'docs'
$corpusRoot = Join-Path $repositoryRoot 'graphify\corpus'
$localCorpus = Join-Path $corpusRoot 'dishonoredvr'
$sharedCorpusSource = 'D:\Dev Debug\VR Modding\cross-engine-graph\corpus'
$sharedCorpus = Join-Path $corpusRoot 'cross-engine'

function Copy-MarkdownTree {
    param(
        [Parameter(Mandatory)] [string] $Source,
        [Parameter(Mandatory)] [string] $Destination
    )

    if (-not (Test-Path -LiteralPath $Source)) {
        throw "Source folder does not exist: $Source"
    }

    Remove-Item -LiteralPath $Destination -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -LiteralPath $Source -Recurse -File -Filter '*.md' | ForEach-Object {
        $relativePath = $_.FullName.Substring($Source.Length).TrimStart('\')
        $target = Join-Path $Destination $relativePath
        New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
        Copy-Item -LiteralPath $_.FullName -Destination $target -Force
    }
}

function Stage-Corpus {
    Copy-MarkdownTree -Source $docsRoot -Destination $localCorpus
    if ($IncludeSharedCorpus) {
        Copy-MarkdownTree -Source $sharedCorpusSource -Destination $sharedCorpus
    }
    Write-Host "Staged local documentation at $localCorpus"
    if ($IncludeSharedCorpus) {
        Write-Host "Staged shared cross-engine documentation at $sharedCorpus"
    }
}

switch ($Command) {
    'stage' {
        Stage-Corpus
    }
    'extract' {
        $runner = Join-Path $repositoryRoot 'Graphify-Update-All.ps1'
        if (-not (Test-Path -LiteralPath $runner -PathType Leaf)) {
            throw "Safe Graphify project runner not found: $runner"
        }
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
    }
    'query' {
        if ([string]::IsNullOrWhiteSpace($Question)) {
            throw 'Provide -Question when querying the graph.'
        }
        $graphPath = Join-Path $repositoryRoot 'graphify-out\graph.json'
        if (-not (Test-Path -LiteralPath $graphPath)) {
            throw "No graph exists at $graphPath. Run an extract first."
        }
        & graphify query $Question --graph $graphPath
    }
}
