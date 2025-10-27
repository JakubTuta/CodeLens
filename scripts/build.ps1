# CodeLens - Build Script
# Builds all Docker images for CodeLens application

Write-Host "CodeLens - Build Script" -ForegroundColor Blue
Write-Host "======================" -ForegroundColor Blue
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker..." -ForegroundColor Yellow
try {
    docker info | Out-Null
    Write-Host "Docker is running" -ForegroundColor Green
} catch {
    Write-Host "Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Building Docker images..." -ForegroundColor Yellow

# Function to remove existing image if it exists
function Remove-ExistingImage {
    param($imageName)
    
    $imageExists = docker images -q $imageName 2>$null
    if ($imageExists) {
        Write-Host "  Removing existing image: $imageName" -ForegroundColor Yellow
        docker rmi $imageName -f | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Existing image removed" -ForegroundColor Green
        } else {
            Write-Host "  Warning: Could not remove existing image" -ForegroundColor Yellow
        }
    }
}

# Build Frontend
Write-Host "Building frontend..." -ForegroundColor Cyan
Remove-ExistingImage "codelens-frontend:latest"
docker build -t codelens-frontend:latest ./frontend
if ($LASTEXITCODE -ne 0) {
    Write-Host "Frontend build failed" -ForegroundColor Red
    exit 1
}
Write-Host "Frontend built successfully" -ForegroundColor Green

# Build Backend  
Write-Host "Building backend..." -ForegroundColor Cyan
Remove-ExistingImage "codelens-backend:latest"
docker build -t codelens-backend:latest ./backend
if ($LASTEXITCODE -ne 0) {
    Write-Host "Backend build failed" -ForegroundColor Red
    exit 1
}
Write-Host "Backend built successfully" -ForegroundColor Green

# Build Test Runner
Write-Host "Building test runner..." -ForegroundColor Cyan
Remove-ExistingImage "codelens-test-runner:kubernetes"
docker build -t codelens-test-runner:kubernetes ./test-runner
if ($LASTEXITCODE -ne 0) {
    Write-Host "Test runner build failed" -ForegroundColor Red
    exit 1
}
Write-Host "Test runner built successfully" -ForegroundColor Green

# Build Kubernetes Test Executor (optimized base image)
Write-Host "Building Kubernetes test executor..." -ForegroundColor Cyan
Remove-ExistingImage "codelens-k8s-test-executor:latest"
docker build -f ./test-runner/test-executor.Dockerfile -t codelens-k8s-test-executor:latest ./test-runner
if ($LASTEXITCODE -ne 0) {
    Write-Host "Kubernetes test executor build failed" -ForegroundColor Red
    exit 1
}
Write-Host "Kubernetes test executor built successfully" -ForegroundColor Green

Write-Host ""
Write-Host "All images built successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  Local development: .\scripts\local.ps1" -ForegroundColor White
Write-Host "  Deploy to GCP:     .\scripts\deploy.ps1" -ForegroundColor White
Write-Host ""
