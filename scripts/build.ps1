# Build Script - Builds all CodeLens container images
# Run this first to build your application

Write-Host "Building CodeLens Application..." -ForegroundColor Blue
Write-Host "===============================" -ForegroundColor Blue

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "[SUCCESS] Docker is running" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Building containers..." -ForegroundColor Yellow

# Build Frontend
Write-Host "Building frontend..." -ForegroundColor Blue
docker build -t codelens-frontend:latest ./frontend
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Frontend build failed" -ForegroundColor Red
    exit 1
}
Write-Host "[SUCCESS] Frontend built successfully" -ForegroundColor Green

# Build Backend  
Write-Host "Building backend..." -ForegroundColor Blue
docker build -t codelens-backend:latest ./backend
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Backend build failed" -ForegroundColor Red
    exit 1
}
Write-Host "[SUCCESS] Backend built successfully" -ForegroundColor Green

# Build Test Runner
Write-Host "Building test runner..." -ForegroundColor Blue
docker build -t codelens-test-runner:latest ./test-runner
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Test runner build failed" -ForegroundColor Red
    exit 1
}
Write-Host "[SUCCESS] Test runner built successfully" -ForegroundColor Green

Write-Host ""
Write-Host "All containers built successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Run: .\start.ps1    # Start the application" -ForegroundColor White
Write-Host "  2. Run: .\stop.ps1     # Stop the application" -ForegroundColor White
