param(
    [string]$PythonExecutable = "python",
    [string]$OutputPath = "docs/test-reports/windows-python314.json"
)
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $ProjectRoot
try {
    # Requires an already-installed interpreter. No install, network or key prompts.
    if (-not (Get-Command $PythonExecutable -ErrorAction SilentlyContinue)) {
        $ReportDir = Split-Path -Parent $OutputPath
        if ($ReportDir) { New-Item -ItemType Directory -Force $ReportDir | Out-Null }
        @{status="NOT TESTED"; reason="Existing Python interpreter not found; no installation attempted"} |
            ConvertTo-Json | Set-Content -Encoding UTF8 $OutputPath
        $TestExit = 2
    } else {
        & $PythonExecutable "$PSScriptRoot/check_compatibility.py" --require-windows --require-python314 --output $OutputPath
        $TestExit = $LASTEXITCODE
    }
} finally {
    Pop-Location
}
exit $TestExit
