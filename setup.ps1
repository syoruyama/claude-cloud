# GA4 MCP Setup Script for Claude Desktop (Windows)
# Prerequisites: Python 3.10+, gcloud CLI installed and on PATH

param(
    [Parameter(Mandatory=$true)]
    [string]$PropertyId
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Check-Command($name) {
    return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}

# --- gcloud CLI check ---
if (-not (Check-Command "gcloud")) {
    Write-Error @"
gcloud CLI が見つかりません。先にインストールしてください:
  https://cloud.google.com/sdk/docs/install
インストール後、PowerShell を再起動してからこのスクリプトを再実行してください。
"@
    exit 1
}

# --- ADC (Application Default Credentials) ---
Write-Host "ADC 認証を開始します..." -ForegroundColor Cyan
gcloud auth application-default login
if ($LASTEXITCODE -ne 0) {
    Write-Error "ADC 認証に失敗しました。"
    exit 1
}
Write-Host "ADC 認証完了。" -ForegroundColor Green

# --- pipx ---
if (-not (Check-Command "pipx")) {
    Write-Host "pipx をインストールします..." -ForegroundColor Cyan
    pip install pipx
    pipx ensurepath
    Write-Warning "PATH を反映するため、PowerShell を再起動してからこのスクリプトを再実行してください。"
    exit 0
}

# --- google-analytics-mcp ---
Write-Host "google-analytics-mcp をインストールします..." -ForegroundColor Cyan
pipx install google-analytics-mcp
if ($LASTEXITCODE -ne 0) {
    Write-Error "google-analytics-mcp のインストールに失敗しました。"
    exit 1
}
Write-Host "google-analytics-mcp インストール完了。" -ForegroundColor Green

# --- Claude Desktop config ---
$configDir = "$env:APPDATA\Claude"
$configPath = "$configDir\claude_desktop_config.json"

if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir | Out-Null
}

$mcpEntry = @{
    mcpServers = @{
        "google-analytics" = @{
            command = "google-analytics-mcp"
            args    = @("--property-id", $PropertyId)
        }
    }
}

if (Test-Path $configPath) {
    $existing = Get-Content $configPath -Raw | ConvertFrom-Json
    if (-not $existing.mcpServers) {
        $existing | Add-Member -MemberType NoteProperty -Name mcpServers -Value ([PSCustomObject]@{})
    }
    $existing.mcpServers | Add-Member -MemberType NoteProperty -Name "google-analytics" -Value $mcpEntry.mcpServers."google-analytics" -Force
    $existing | ConvertTo-Json -Depth 10 | Set-Content $configPath -Encoding UTF8
} else {
    $mcpEntry | ConvertTo-Json -Depth 10 | Set-Content $configPath -Encoding UTF8
}

Write-Host ""
Write-Host "セットアップ完了！" -ForegroundColor Green
Write-Host "設定ファイル: $configPath" -ForegroundColor Yellow
Write-Host ""
Write-Host "次のステップ:" -ForegroundColor Cyan
Write-Host "  1. Google Cloud Console で以下の API を有効化してください:"
Write-Host "     - Google Analytics Data API"
Write-Host "       https://console.cloud.google.com/apis/library/analyticsdata.googleapis.com"
Write-Host "     - Google Analytics Admin API"
Write-Host "       https://console.cloud.google.com/apis/library/analyticsadmin.googleapis.com"
Write-Host "  2. Claude Desktop を再起動してください。"
Write-Host "  3. 設定 > Developer に 'google-analytics | Running' と表示されれば完了です。"
