# launch-inspector.ps1
# Generic MCP Inspector launcher for uv-based MCP servers
# Auto-detects project entry point from pyproject.toml

[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSAvoidUsingWriteHost', '')]
param(
    [string]$ServerPath = $null
)

Write-Host "=== MCP Inspector Launcher ===" -ForegroundColor Cyan
Write-Host ""

# Determine server directory
if ($ServerPath) {
    $repoRoot = Resolve-Path $ServerPath
} else {
    $repoRoot = Get-Location
}

Write-Host "Project: $repoRoot" -ForegroundColor Yellow
Write-Host ""

# Verify we're in the right directory
$pyprojectToml = Join-Path $repoRoot "pyproject.toml"
if (-not (Test-Path $pyprojectToml)) {
    Write-Host "✗ Not a valid MCP project directory!" -ForegroundColor Red
    Write-Host "   Missing: pyproject.toml" -ForegroundColor Red
    exit 1
}

# Parse pyproject.toml to find the entry point
Write-Host "Detecting project entry point..." -ForegroundColor Yellow
$content = Get-Content $pyprojectToml -Raw

# Extract project name and scripts section
if ($content -match '(?ms)\[project\.scripts\]\s*\n([^\[]+)') {
    $scriptsSection = $matches[1]
    # Get first entry point (format: name = "module:function")
    if ($scriptsSection -match '^(\S+)\s*=') {
        $entryPoint = $matches[1].Trim()
        Write-Host "✓ Detected entry point: $entryPoint" -ForegroundColor Green
    } else {
        Write-Host "✗ Could not parse [project.scripts] section!" -ForegroundColor Red
        Write-Host "   Expected format: entry-point = 'module:function'" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✗ No [project.scripts] section found in pyproject.toml!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting MCP Inspector..." -ForegroundColor Cyan
Write-Host "Inspector will open in your browser" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Change to project directory and launch
Push-Location $repoRoot
try {
    # Launch inspector with detected entry point
    & npx @modelcontextprotocol/inspector uv run $entryPoint
} finally {
    Pop-Location
}
