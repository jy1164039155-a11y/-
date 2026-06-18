<# 
LandChina server access probe.

Run on the cloud server with Windows PowerShell:
  Set-ExecutionPolicy -Scope Process Bypass -Force
  .\landchina_server_probe.ps1 -XzqDm 431124 -StartDate 2023-04-23 -EndDate 2026-04-23

This script sends only a small number of requests:
  1. open the official page
  2. call one list API page
  3. if the list succeeds, call one detail API record
#>

[CmdletBinding()]
param(
    [string]$XzqDm = "431124",
    [string]$StartDate = "2023-04-23",
    [string]$EndDate = "2026-04-23",
    [int]$PageSize = 5,
    [int]$TimeoutSec = 25,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
} catch {
}
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
} catch {
}

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
    param(
        [string]$UserAgent,
        [string]$Path
    )
    $action = ($Path.TrimEnd("/") -split "/")[-1]
    return Get-Sha256Hex ("{0}{1}{2}" -f $UserAgent, (Get-Date).Day, $action)
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

function Convert-JsonSafely {
    param([string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) {
        return $null
    }
    try {
        return $Text | ConvertFrom-Json
    } catch {
        return $null
    }
}

function Invoke-OfficialHome {
    param($Profile)
    $result = [ordered]@{
        ok = $false
        status = $null
        url = $Profile.Home
        error = ""
        preview = ""
    }
    try {
        $response = Invoke-WebRequest `
            -Uri $Profile.Home `
            -UseBasicParsing `
            -TimeoutSec $TimeoutSec `
            -UserAgent $Profile.UserAgent `
            -ErrorAction Stop
        $result.ok = ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300)
        $result.status = [int]$response.StatusCode
        $result.preview = ($response.Content | Select-Object -First 1)
    } catch {
        $response = $_.Exception.Response
        if ($response) {
            $result.status = [int]$response.StatusCode
            $result.preview = Read-WebExceptionBody $response
        }
        $result.error = $_.Exception.Message
    }
    return [pscustomobject]$result
}

function Invoke-LandChinaApi {
    param(
        $Profile,
        [string]$Path,
        [hashtable]$Payload
    )
    $json = $Payload | ConvertTo-Json -Compress -Depth 12
    $headers = @{
        "Accept" = "application/json, text/plain, */*"
        "Accept-Language" = "zh-CN,zh;q=0.9"
        "Cache-Control" = "no-cache"
        "Origin" = $Profile.Origin
        "Referer" = $Profile.Referer
        "Hash" = Get-LandChinaHash -UserAgent $Profile.UserAgent -Path $Path
    }
    $url = "https://api.landchina.com$Path"
    if ($DryRun) {
        return [pscustomobject][ordered]@{
            ok = $true
            dry_run = $true
            status = 0
            redirected = $false
            location = ""
            url = $url
            payload = $json
            parsed = $null
            preview = ""
            error = ""
        }
    }

    $result = [ordered]@{
        ok = $false
        dry_run = $false
        status = $null
        redirected = $false
        location = ""
        url = $url
        payload = $json
        parsed = $null
        preview = ""
        error = ""
    }
    try {
        $response = Invoke-WebRequest `
            -Uri $url `
            -Method Post `
            -Body ([System.Text.Encoding]::UTF8.GetBytes($json)) `
            -ContentType "application/json;charset=UTF-8" `
            -Headers $headers `
            -UserAgent $Profile.UserAgent `
            -UseBasicParsing `
            -TimeoutSec $TimeoutSec `
            -MaximumRedirection 0 `
            -ErrorAction Stop
        $result.status = [int]$response.StatusCode
        $result.ok = ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300)
        $result.preview = $response.Content.Substring(0, [Math]::Min(600, $response.Content.Length))
        $result.parsed = Convert-JsonSafely $response.Content
    } catch {
        $response = $_.Exception.Response
        if ($response) {
            $result.status = [int]$response.StatusCode
            $result.redirected = $result.status -in @(301, 302, 307, 308)
            $result.location = [string]$response.Headers["Location"]
            $body = Read-WebExceptionBody $response
            $result.preview = $body.Substring(0, [Math]::Min(600, $body.Length))
            $result.parsed = Convert-JsonSafely $body
        }
        $result.error = $_.Exception.Message
    }
    return [pscustomobject]$result
}

$profiles = @(
    [pscustomobject]@{
        Name = "pc-www"
        Home = "https://www.landchina.com/"
        Origin = "https://www.landchina.com"
        Referer = "https://www.landchina.com/"
        UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
    },
    [pscustomobject]@{
        Name = "mobile-m"
        Home = "https://m.landchina.com/"
        Origin = "https://m.landchina.com"
        Referer = "https://m.landchina.com/"
        UserAgent = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    }
)

$listPayload = [ordered]@{
    pageNum = 1
    pageSize = $PageSize
    xzqDm = $XzqDm
    gyFs = $null
    tdYt = $null
    startDate = "$StartDate 00:00:00"
    endDate = "$EndDate 23:59:59"
    dzBaBh = $null
    tdZl = $null
}

$probe = [ordered]@{
    machine = $env:COMPUTERNAME
    public_ip_hint = ""
    started_at = (Get-Date).ToString("s")
    xzq_dm = $XzqDm
    start_date = $StartDate
    end_date = $EndDate
    page_size = $PageSize
    profiles = @()
    conclusion = "unknown"
}

Write-Host "LandChina server probe started: XzqDm=$XzqDm Date=$StartDate..$EndDate" -ForegroundColor Cyan
Write-Host "This probe uses at most one list request and one detail request per profile." -ForegroundColor DarkCyan

foreach ($profile in $profiles) {
    Write-Host ""
    Write-Host "=== Profile: $($profile.Name) ===" -ForegroundColor Cyan
    $profileResult = [ordered]@{
        name = $profile.Name
        home = $null
        list = $null
        detail = $null
        first_gd_guid = ""
        total = $null
        pages = $null
    }

    $homeResult = Invoke-OfficialHome -Profile $profile
    $profileResult.home = $homeResult
    Write-Host ("Home: status={0} ok={1}" -f $homeResult.status, $homeResult.ok)

    Start-Sleep -Seconds 2
    $list = Invoke-LandChinaApi -Profile $profile -Path "/tGdxm/result/list" -Payload $listPayload
    $profileResult.list = $list
    $listCode = $null
    if ($list.parsed) {
        $listCode = $list.parsed.code
    }
    Write-Host ("List: status={0} redirected={1} code={2} location={3}" -f $list.status, $list.redirected, $listCode, $list.location)

    if ($list.parsed -and $list.parsed.code -eq 200 -and $list.parsed.data) {
        $profileResult.total = $list.parsed.data.total
        $profileResult.pages = $list.parsed.data.pages
        $first = @($list.parsed.data.list | Where-Object { $_.gdGuid } | Select-Object -First 1)
        if ($first.Count -gt 0) {
            $gdGuid = [string]$first[0].gdGuid
            $profileResult.first_gd_guid = $gdGuid
            Write-Host ("First gdGuid: {0}; total={1}; pages={2}" -f $gdGuid, $profileResult.total, $profileResult.pages)
            Start-Sleep -Seconds 3
            $detailPayload = @{ gdGuid = $gdGuid }
            $detail = Invoke-LandChinaApi -Profile $profile -Path "/tGdxm/result/detail" -Payload $detailPayload
            $profileResult.detail = $detail
            $detailCode = $null
            if ($detail.parsed) {
                $detailCode = $detail.parsed.code
            }
            Write-Host ("Detail: status={0} redirected={1} code={2} location={3}" -f $detail.status, $detail.redirected, $detailCode, $detail.location)
            if ($detail.parsed -and $detail.parsed.code -eq 200 -and $detail.parsed.data) {
                Write-Host "Detail data returned: YES" -ForegroundColor Green
            }
        } else {
            Write-Host "List returned code=200 but no gdGuid in the first page." -ForegroundColor Yellow
        }
    }

    $probe.profiles += [pscustomobject]$profileResult
    Start-Sleep -Seconds 3
}

$anyDetail = $false
$anyList = $false
$anyRedirect = $false
foreach ($item in $probe.profiles) {
    if ($item.list -and $item.list.parsed -and $item.list.parsed.code -eq 200) {
        $anyList = $true
    }
    if ($item.detail -and $item.detail.parsed -and $item.detail.parsed.code -eq 200 -and $item.detail.parsed.data) {
        $anyDetail = $true
    }
    if (($item.list -and $item.list.redirected) -or ($item.detail -and $item.detail.redirected)) {
        $anyRedirect = $true
    }
}

if ($anyDetail) {
    $probe.conclusion = "detail_ok"
    Write-Host ""
    Write-Host "CONCLUSION: detail_ok - this server can reach list and detail APIs." -ForegroundColor Green
} elseif ($anyList) {
    $probe.conclusion = "list_only"
    Write-Host ""
    Write-Host "CONCLUSION: list_only - list API works, detail API did not return data." -ForegroundColor Yellow
} elseif ($anyRedirect) {
    $probe.conclusion = "redirect_blocked"
    Write-Host ""
    Write-Host "CONCLUSION: redirect_blocked - API was redirected, likely blocked by gateway/WAF." -ForegroundColor Red
} else {
    $probe.conclusion = "failed"
    Write-Host ""
    Write-Host "CONCLUSION: failed - API did not return usable JSON." -ForegroundColor Red
}

$probe.finished_at = (Get-Date).ToString("s")
$resultPath = Join-Path (Get-Location) ("landchina_probe_result_{0}.json" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
$probe | ConvertTo-Json -Depth 20 | Set-Content -Path $resultPath -Encoding UTF8
Write-Host "Result saved: $resultPath" -ForegroundColor Cyan
