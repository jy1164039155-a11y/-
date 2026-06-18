param(
    [string]$PythonExe = "python",
    [int]$Port = 8000,
    [switch]$Lan
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$HostArg = "127.0.0.1"
if ($Lan) {
    $HostArg = "0.0.0.0"
}

Write-Host "Starting valuation report demo server..."
Write-Host "Project root: $Root"
Write-Host "Bind address: $HostArg"
Write-Host "Port: $Port"
Write-Host ""

if ($Lan) {
    $ip = (Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object { $_.IPAddress -notlike "169.254*" -and $_.IPAddress -ne "127.0.0.1" } |
        Select-Object -First 1 -ExpandProperty IPAddress)
    if ($ip) {
        Write-Host "LAN demo URL: http://$ip`:$Port"
    }
} else {
    Write-Host "Local demo URL: http://127.0.0.1:$Port"
}

Write-Host ""
Write-Host "Keep this window open during the QA demo. Press Ctrl+C to stop."
& $PythonExe -m uvicorn src.api:app --host $HostArg --port $Port
