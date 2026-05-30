<#
.SYNOPSIS
    Extracts PMDG .ptp livery files using CabLib.

.DESCRIPTION
    Pass one or more .ptp file paths as arguments from an existing PowerShell session.
    Each file is extracted into a subfolder named after the .ptp file, placed
    in the same directory as the source file.

    Requirements:
      - CabLib.dll must be in the same folder as this script.
      - .NET / PowerShell 5.1+ (or PowerShell 7+)
#>

param (
    [Parameter(Mandatory, ValueFromRemainingArguments)]
    [string[]] $PtpFiles
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ── Resolve and load CabLib ───────────────────────────────────────────────────

$scriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$cabLibPath = Join-Path $scriptDir 'CabLib.dll'

if (-not (Test-Path $cabLibPath)) {
    Write-Error "CabLib.dll not found at: $cabLibPath`nPlace this script in the same folder as CabLib.dll."
    exit 1
}

Unblock-File -Path $cabLibPath
Unblock-File -Path $MyInvocation.MyCommand.Path

Add-Type -Path $cabLibPath
Add-Type -AssemblyName System.Web

$shimSource = @'
using System;
using CabLib;

public static class PtpHelper
{
    public static void Subscribe(Extract extract)
    {
        extract.evBeforeCopyFile += AllowAll;
    }

    public static bool AllowAll(Extract.kCabinetFileInfo info)
    {
        Console.WriteLine("  Extracting: " + info.s_RelPath);
        return true;
    }
}
'@

Add-Type -TypeDefinition $shimSource -ReferencedAssemblies $cabLibPath

$decryptionKey = [System.Text.Encoding]::ASCII.GetBytes('PMDG_SecurityCode')

# ── Helpers ───────────────────────────────────────────────────────────────────

function Decode-PtpName ([string] $raw) {
    $decoded = [System.Web.HttpUtility]::UrlDecode($raw)
    return $decoded -replace '[<>:"/\\|?*]', '_'
}

# ── Process each dropped file ─────────────────────────────────────────────────

$results = [System.Collections.Generic.List[PSCustomObject]]::new()

foreach ($rawPath in $PtpFiles) {

    $ptpPath = $rawPath.Trim('"').Trim("'")

    if (-not (Test-Path $ptpPath)) {
        Write-Warning "File not found, skipping: $ptpPath"
        $results.Add([PSCustomObject]@{ File = $ptpPath; Status = 'Not found' })
        continue
    }

    $ptpPath   = (Resolve-Path $ptpPath).Path
    $sourceDir = Split-Path -Parent $ptpPath
    $rawStem   = [System.IO.Path]::GetFileNameWithoutExtension($ptpPath)
    $baseName  = Decode-PtpName $rawStem
    $outputDir = Join-Path $sourceDir $baseName

    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host "  Source : $ptpPath"     -ForegroundColor Cyan
    Write-Host "  Output : $outputDir"   -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray

    if (-not (Test-Path $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir | Out-Null
    }

    try {
        $extract = New-Object CabLib.Extract
        $extract.SetDecryptionKey($decryptionKey)

        [PtpHelper]::Subscribe($extract)

        $extract.ExtractFile($ptpPath, $outputDir)

        Write-Host "  Done." -ForegroundColor Green
        $results.Add([PSCustomObject]@{ File = $baseName; Status = 'OK'; Output = $outputDir })

    } catch {
        Write-Warning "  Extraction failed: $_"
        $results.Add([PSCustomObject]@{ File = $baseName; Status = "Failed: $_" })
    }
}

# ── Summary ───────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host "  Summary" -ForegroundColor White
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray

foreach ($r in $results) {
    $colour = if ($r.Status -eq 'OK') { 'Green' } else { 'Red' }
    Write-Host ("  [{0,-6}] {1}" -f $r.Status, $r.File) -ForegroundColor $colour
}
