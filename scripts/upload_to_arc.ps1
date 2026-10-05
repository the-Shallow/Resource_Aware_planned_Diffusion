[CmdletBinding()]
param(
    [string]$ArcUser = "kpatel53",
    [string]$ArcHost = "arc.csc.ncsu.edu",
    [string]$IdentityFile = "C:\Users\khush\.ssh\arc_v3",
    [string]$RemoteDirectory = "Resource_Aware_planned_Diffusion"
)

$ErrorActionPreference = "Stop"

if ($RemoteDirectory.StartsWith("/") -or
    $RemoteDirectory.Contains("..") -or
    $RemoteDirectory -notmatch '^[A-Za-z0-9._/-]+$') {
    throw "RemoteDirectory must be a safe path relative to your ARC home directory."
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$requiredCommands = @("tar.exe", "ssh.exe", "scp.exe")

foreach ($command in $requiredCommands) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        throw "Required command '$command' was not found on PATH."
    }
}

if (-not (Test-Path -LiteralPath $IdentityFile -PathType Leaf)) {
    throw "ARC SSH key not found: $IdentityFile"
}

$remote = "$ArcUser@$ArcHost"
$archiveName = "resource-aware-planned-diffusion-upload.tar.gz"
$localArchive = Join-Path ([System.IO.Path]::GetTempPath()) $archiveName
$remoteArchive = "$archiveName"

Write-Host "Project:      $repoRoot"
Write-Host "ARC account:  $remote"
Write-Host "Destination:  ~/$RemoteDirectory"
Write-Host ""
Write-Host "The upload excludes local environments, caches, model weights, and outputs."

try {
    if (Test-Path -LiteralPath $localArchive) {
        Remove-Item -LiteralPath $localArchive -Force
    }

    Push-Location $repoRoot
    try {
        & tar.exe -czf $localArchive `
            --exclude=.venv `
            --exclude=venv `
            --exclude=__pycache__ `
            --exclude=.pytest_cache `
            --exclude=.mypy_cache `
            --exclude=.ruff_cache `
            --exclude=.cache `
            --exclude=checkpoints `
            --exclude=models `
            --exclude=outputs `
            --exclude=results `
            --exclude=logs `
            --exclude=wandb `
            --exclude=tmp `
            --exclude=scratch `
            --exclude='*.pyc' `
            --exclude='*.safetensors' `
            --exclude='*.bin' `
            --exclude='*.pt' `
            --exclude='*.pth' `
            .

        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create the project archive."
        }
    }
    finally {
        Pop-Location
    }

    Write-Host "Creating the ARC destination directory..."
    & ssh.exe -i $IdentityFile $remote "cd ~ && mkdir -p '$RemoteDirectory'"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create the destination directory on ARC."
    }

    Write-Host "Uploading the project archive..."
    & scp.exe -i $IdentityFile $localArchive "${remote}:$remoteArchive"
    if ($LASTEXITCODE -ne 0) {
        throw "Project upload failed."
    }

    Write-Host "Extracting the project on ARC..."
    & ssh.exe -i $IdentityFile $remote "cd ~ && tar -xzf '$remoteArchive' -C '$RemoteDirectory' && rm -f '$remoteArchive'"
    if ($LASTEXITCODE -ne 0) {
        throw "The archive uploaded, but ARC extraction failed."
    }

    Write-Host ""
    Write-Host "Upload complete: ${remote}:~/$RemoteDirectory"
    Write-Host "Connect with: ssh -i `"$IdentityFile`" $remote"
    Write-Host "Then run:     cd ~/$RemoteDirectory"
}
finally {
    if (Test-Path -LiteralPath $localArchive) {
        Remove-Item -LiteralPath $localArchive -Force
    }
}
