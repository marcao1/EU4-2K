param(
    [string]$Eu4UserDirectory = "$env:USERPROFILE\OneDrive\Dokumente\Paradox Interactive\Europa Universalis IV"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$source = Join-Path $root "MillenniumDawnEU4"
$modDirectory = Join-Path $Eu4UserDirectory "mod"
$destination = Join-Path $modDirectory "MillenniumDawnEU4"

if (-not (Test-Path -LiteralPath (Join-Path $source "descriptor.mod"))) {
    throw "Generate the mod before installing it."
}

New-Item -ItemType Directory -Force -Path $modDirectory | Out-Null
if (Test-Path -LiteralPath $destination) {
    $resolved = [System.IO.Path]::GetFullPath($destination)
    if (-not $resolved.StartsWith([System.IO.Path]::GetFullPath($modDirectory))) {
        throw "Refusing to replace a destination outside the EU4 mod directory."
    }
    Remove-Item -LiteralPath $destination -Recurse -Force
}
Copy-Item -LiteralPath $source -Destination $destination -Recurse
Copy-Item -LiteralPath (Join-Path $root "MillenniumDawnEU4.mod") -Destination (Join-Path $modDirectory "MillenniumDawnEU4.mod") -Force
Write-Host "Installed Millennium Dawn EU4 to $destination"
