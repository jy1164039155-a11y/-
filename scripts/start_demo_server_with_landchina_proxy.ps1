param(
    [string]$PythonExe = "python",
    [int]$Port = 8000,
    [switch]$Lan,
    [string]$ProxyUrl = "",
    [string]$ProxyToken = ""
)

$ErrorActionPreference = "Stop"

if (-not $ProxyUrl) {
    $ProxyUrl = Read-Host "LandChina proxy URL, for example http://117.72.179.235:8787/landchina/"
}
if (-not $ProxyToken) {
    $ProxyToken = Read-Host "LandChina proxy token"
}

$env:LANDCHINA_PROXY_URL = $ProxyUrl
$env:LANDCHINA_PROXY_TOKEN = $ProxyToken

Write-Host "LandChina proxy enabled: $ProxyUrl"
& "$PSScriptRoot\start_demo_server.ps1" -PythonExe $PythonExe -Port $Port -Lan:$Lan
