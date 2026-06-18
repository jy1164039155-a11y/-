<#
Lightweight LandChina API relay for Windows Server.

Example:
  powershell -ExecutionPolicy Bypass -File .\landchina_proxy_server.ps1 -Port 8787 -Token "replace-with-a-long-token"

Local app config:
  LANDCHINA_PROXY_URL=http://SERVER_PUBLIC_IP:8787/landchina/
  LANDCHINA_PROXY_TOKEN=replace-with-a-long-token
#>

[CmdletBinding()]
param(
    [int]$Port = 8787,
    [Parameter(Mandatory = $true)]
    [string]$Token,
    [int]$TimeoutSec = 25,
    [int]$MinIntervalMs = 900,
    [int]$DetailIntervalMs = 1800
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
[System.Net.WebRequest]::DefaultWebProxy = $null

$UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
$ApiBase = "https://api.landchina.com"
$AllowedPaths = @(
    "/tGdxm/result/list",
    "/tGdxm/result/detail",
    "/bptFieldEnum/xzq",
    "/bptFieldEnum/tdytTreeList"
)
$script:NextRequestAt = Get-Date
$script:BlockedUntil = Get-Date

function Get-Sha256Hex {
    param([string]$Text)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
        return -join ($sha.ComputeHash($bytes) | ForEach-Object { $_.ToString("x2") })
    } finally {
        $sha.Dispose()
    }
}

function Get-LandChinaHash {
    param([string]$Path)
    $action = ($Path.TrimEnd("/") -split "/")[-1]
    return Get-Sha256Hex ("{0}{1}{2}" -f $UserAgent, (Get-Date).Day, $action)
}

function Read-Body {
    param($Request)
    $reader = New-Object System.IO.StreamReader($Request.InputStream, $Request.ContentEncoding)
    try {
        return $reader.ReadToEnd()
    } finally {
        $reader.Dispose()
    }
}

function Write-Json {
    param(
        $Context,
        [int]$StatusCode,
        $Data
    )
    $json = $Data | ConvertTo-Json -Depth 20 -Compress
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
    try {
        $Context.Response.StatusCode = $StatusCode
        $Context.Response.ContentType = "application/json; charset=utf-8"
        $Context.Response.ContentLength64 = $bytes.Length
        $Context.Response.OutputStream.Write($bytes, 0, $bytes.Length)
        $Context.Response.OutputStream.Close()
    } catch {
        Write-Host ("{0:s} RESPONSE_WRITE_FAILED status={1} message={2}" -f (Get-Date), $StatusCode, $_.Exception.Message) -ForegroundColor Yellow
    }
}

function Read-WebExceptionBody {
    param($Response)
    if (-not $Response) {
        return ""
    }
    try {
        $stream = $Response.GetResponseStream()
        if (-not $stream) {
            return ""
        }
        $reader = New-Object System.IO.StreamReader($stream, [System.Text.Encoding]::UTF8)
        try {
            return $reader.ReadToEnd()
        } finally {
            $reader.Dispose()
            $stream.Dispose()
        }
    } catch {
        return ""
    }
}

function Wait-RelaySlot {
    param([string]$Path)
    $interval = if ($Path -eq "/tGdxm/result/detail") { $DetailIntervalMs } else { $MinIntervalMs }
    $now = Get-Date
    if ($script:NextRequestAt -gt $now) {
        $delay = [int][Math]::Ceiling(($script:NextRequestAt - $now).TotalMilliseconds)
        if ($delay -gt 0) {
            Start-Sleep -Milliseconds $delay
        }
    }
    $script:NextRequestAt = (Get-Date).AddMilliseconds([Math]::Max($interval, 0))
}

function Invoke-LandChina {
    param(
        [string]$Path,
        $Payload
    )
    Wait-RelaySlot -Path $Path
    $json = $Payload | ConvertTo-Json -Depth 20 -Compress
    $headers = @{
        "Accept" = "application/json, text/plain, */*"
        "Accept-Language" = "zh-CN,zh;q=0.9"
        "Cache-Control" = "no-cache"
        "Origin" = "https://www.landchina.com"
        "Referer" = "https://www.landchina.com/"
        "Hash" = Get-LandChinaHash -Path $Path
    }
    $response = Invoke-WebRequest `
        -Uri ($ApiBase + $Path) `
        -Method Post `
        -Body ([System.Text.Encoding]::UTF8.GetBytes($json)) `
        -ContentType "application/json;charset=UTF-8" `
        -Headers $headers `
        -UserAgent $UserAgent `
        -UseBasicParsing `
        -TimeoutSec $TimeoutSec `
        -MaximumRedirection 0
    return $response.Content | ConvertFrom-Json
}

$prefix = "http://+:$Port/landchina/"
$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add($prefix)
$listener.Start()

Write-Host "LandChina relay listening on $prefix" -ForegroundColor Green
Write-Host "Allowed paths: $($AllowedPaths -join ', ')" -ForegroundColor DarkCyan
Write-Host "Press Ctrl+C to stop." -ForegroundColor DarkCyan

try {
    while ($listener.IsListening) {
        $context = $listener.GetContext()
        try {
            if ($context.Request.HttpMethod -eq "GET") {
                Write-Json $context 200 @{
                    status = "ok"
                    blocked_until = if ($script:BlockedUntil -gt (Get-Date)) { $script:BlockedUntil.ToString("s") } else { "" }
                    allowed_paths = $AllowedPaths
                }
                continue
            }
            if ($context.Request.HttpMethod -ne "POST") {
                Write-Json $context 405 @{ error = "method_not_allowed" }
                continue
            }
            $providedToken = $context.Request.Headers["X-LandChina-Proxy-Token"]
            if ([string]::IsNullOrWhiteSpace($providedToken)) {
                $auth = [string]$context.Request.Headers["Authorization"]
                if ($auth.StartsWith("Bearer ")) {
                    $providedToken = $auth.Substring(7)
                }
            }
            if ($providedToken -ne $Token) {
                Write-Json $context 401 @{ error = "unauthorized" }
                continue
            }

            $raw = Read-Body $context.Request
            $inputData = $raw | ConvertFrom-Json
            $path = [string]$inputData.path
            if ($AllowedPaths -notcontains $path) {
                Write-Json $context 400 @{ error = "path_not_allowed"; path = $path }
                continue
            }
            if ($script:BlockedUntil -gt (Get-Date)) {
                Write-Json $context 503 @{
                    error = "relay_cooling_down"
                    blocked_until = $script:BlockedUntil.ToString("s")
                    message = "relay is cooling down after an upstream failure"
                }
                Write-Host ("{0:s} COOLING_DOWN {1} until={2}" -f (Get-Date), $path, $script:BlockedUntil.ToString("s")) -ForegroundColor Yellow
                continue
            }
            $payload = $inputData.payload
            if ($null -eq $payload) {
                $payload = @{}
            }

            Write-Host ("{0:s} START {1}" -f (Get-Date), $path) -ForegroundColor DarkCyan
            $official = Invoke-LandChina -Path $path -Payload $payload
            Write-Json $context 200 $official
            Write-Host ("{0:s} OK {1}" -f (Get-Date), $path)
        } catch {
            $response = $_.Exception.Response
            $statusCode = 502
            $officialStatus = ""
            $location = ""
            $body = ""
            if ($response) {
                $officialStatus = [int]$response.StatusCode
                $location = [string]$response.Headers["Location"]
                $body = Read-WebExceptionBody $response
            }
            if ($officialStatus -in @(500, 502, 503, 504) -or -not $response) {
                $script:BlockedUntil = (Get-Date).AddMinutes(5)
            }
            Write-Json $context 502 @{
                error = "relay_failed"
                official_status = $officialStatus
                location = $location
                message = $_.Exception.Message
                body_preview = $body.Substring(0, [Math]::Min(600, $body.Length))
                blocked_until = if ($script:BlockedUntil -gt (Get-Date)) { $script:BlockedUntil.ToString("s") } else { "" }
            }
            Write-Host ("{0:s} FAIL official_status={1} location={2} blocked_until={3} message={4}" -f (Get-Date), $officialStatus, $location, $(if ($script:BlockedUntil -gt (Get-Date)) { $script:BlockedUntil.ToString("s") } else { "" }), $_.Exception.Message) -ForegroundColor Yellow
        }
    }
} finally {
    if ($listener.IsListening) {
        $listener.Stop()
    }
    $listener.Close()
}
