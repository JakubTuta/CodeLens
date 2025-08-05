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

# Function to remove existing Docker image if it exists
function Remove-DockerImage {
    param (
        [string]$ImageName
    )
    
    Write-Host "Checking for existing image: $ImageName..." -ForegroundColor Cyan
    $imageExists = docker images -q $ImageName 2>$null
    
    if ($imageExists) {
        Write-Host "Removing existing image: $ImageName" -ForegroundColor Yellow
        docker rmi $ImageName --force 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[SUCCESS] Removed existing image: $ImageName" -ForegroundColor Green
        } else {
            Write-Host "[WARNING] Could not remove image: $ImageName (may be in use)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "No existing image found for: $ImageName" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Cleaning up existing images..." -ForegroundColor Yellow
Remove-DockerImage "codelens-frontend:latest"
Remove-DockerImage "codelens-backend:latest"
Remove-DockerImage "codelens-test-runner:latest"

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
Write-Host "Cleaning up dangling images..." -ForegroundColor Yellow
$danglingImages = docker images -f "dangling=true" -q 2>$null
if ($danglingImages) {
    docker rmi $danglingImages --force 2>$null | Out-Null
    Write-Host "[SUCCESS] Cleaned up dangling images" -ForegroundColor Green
} else {
    Write-Host "No dangling images to clean up" -ForegroundColor Gray
}

Write-Host ""
Write-Host "All containers built successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Run: .\start.ps1    # Start the application" -ForegroundColor White
Write-Host "  2. Run: .\stop.ps1     # Stop the application" -ForegroundColor White
