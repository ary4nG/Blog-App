<#
.SYNOPSIS
    Checks whether a hotfix branch is needed or if a production bug can be fixed directly on main.

.DESCRIPTION
    Compares the latest production tag (prod/*) with the current state of origin/main.
    If main has new commits beyond the production tag, a hotfix branch is required.
    If main has NOT moved, the fix can be applied directly on main.

.EXAMPLE
    .\scripts\check-hotfix-needed.ps1

.NOTES
    Requires: git CLI, network access to fetch from remote
#>

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Hotfix Decision Helper (FastAPI)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Fetch latest tags and branches
Write-Host "[1/3] Fetching latest from remote..." -ForegroundColor Yellow
git fetch --all --tags --force --quiet 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: git fetch failed. Check your network/credentials." -ForegroundColor Red
    exit 1
}
Write-Host "  Done." -ForegroundColor Green

# Step 2: Find the latest production tag
Write-Host "[2/3] Finding latest production tag..." -ForegroundColor Yellow
$prodTags = git tag -l "prod/*" --sort=-v:refname
if (-not $prodTags) {
    Write-Host "  WARNING: No production tags (prod/*) found." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  This could mean:" -ForegroundColor White
    Write-Host "    - The repo has never deployed to production via the CI pipeline" -ForegroundColor Gray
    Write-Host "    - Environment tagging is not yet enabled in github_cd.yml" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  To handle hotfixes without tags:" -ForegroundColor Yellow
    Write-Host "    1. Find the Prod commit SHA from the last successful Prod deployment in GitHub Actions" -ForegroundColor Gray
    Write-Host "    2. Compare with main HEAD" -ForegroundColor Gray
    Write-Host "    3. If different, create hotfix branch: git checkout -b hotfix/<name> <prod-sha>" -ForegroundColor Gray
    exit 1
}
$prodTag = ($prodTags | Select-Object -First 1).Trim()
Write-Host "  Latest production tag: $prodTag" -ForegroundColor Green

# Step 3: Compare main with production tag
Write-Host "[3/3] Checking if main has moved beyond production..." -ForegroundColor Yellow
$commits = git log "$prodTag..origin/main" --oneline 2>$null
$commitCount = if ($commits) { ($commits | Measure-Object).Count } else { 0 }

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RESULT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($commitCount -eq 0) {
    Write-Host "  Main has NOT moved beyond $prodTag" -ForegroundColor Green
    Write-Host ""
    Write-Host "  RECOMMENDATION: Fix on main directly" -ForegroundColor Green
    Write-Host "  Deploy normally: Dev -> Test -> ACC -> Prod" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Next steps:" -ForegroundColor White
    Write-Host "    git checkout main" -ForegroundColor Gray
    Write-Host "    git pull" -ForegroundColor Gray
    Write-Host "    # Apply your fix, commit, and push" -ForegroundColor Gray
    Write-Host "    # CI pipeline will build and deploy through all environments" -ForegroundColor Gray
} else {
    Write-Host "  Main has $commitCount new commit(s) beyond $prodTag" -ForegroundColor Yellow
    Write-Host ""
    if ($commits) {
        Write-Host "  Commits on main not in production:" -ForegroundColor Yellow
        $commits | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
        Write-Host ""
    }
    Write-Host "  RECOMMENDATION: Create a hotfix branch" -ForegroundColor Yellow
    Write-Host "  Deploy via hotfix: Test -> ACC -> Prod (skip Dev)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Option A - Use the GitHub Actions UI:" -ForegroundColor White
    Write-Host "    Go to Actions -> 'Create Hotfix Branch' -> Run workflow" -ForegroundColor Gray
    Write-Host "    The workflow auto-detects the latest release tag" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Option B - Create manually:" -ForegroundColor White
    Write-Host "    git checkout -b hotfix/<descriptive-name> $prodTag" -ForegroundColor Gray
    Write-Host "    git push -u origin hotfix/<descriptive-name>" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Then:" -ForegroundColor White
    Write-Host "    # Apply your fix, commit, and push to the hotfix branch" -ForegroundColor Gray
    Write-Host "    # CI pipeline will build and deploy: Test -> ACC -> Prod (skips Dev)" -ForegroundColor Gray
    Write-Host "    # Auto PR will be created to merge fix back to main" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Hotfix Decision Helper (FastAPI)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
