# CodeLens All-in-One Script
# This script does everything: build, stop old app, start new app, and set up connections

param(
    [switch]$Help
)

if ($Help) {
    Write-Host "CodeLens All-in-One Script" -ForegroundColor Blue
    Write-Host "=========================" -ForegroundColor Blue
    Write-Host ""
    Write-Host "This script will:" -ForegroundColor Yellow
    Write-Host "  1. Build all container images" -ForegroundColor White
    Write-Host "  2. Stop any running application" -ForegroundColor White
    Write-Host "  3. Start the new application" -ForegroundColor White
    Write-Host "  4. Set up port forwarding for all services" -ForegroundColor White
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\run-app.ps1           # Run the complete workflow" -ForegroundColor White
    Write-Host "  .\run-app.ps1 -Help     # Show this help" -ForegroundColor White
    Write-Host ""
    Write-Host "After running, your application will be available at:" -ForegroundColor Yellow
    Write-Host "  Frontend:    http://localhost:3000" -ForegroundColor White
    Write-Host "  Backend:     http://localhost:8000" -ForegroundColor White
    Write-Host "  Test Runner: http://localhost:8001" -ForegroundColor White
    exit 0
}

Write-Host ""
Write-Host "CodeLens All-in-One Deployment" -ForegroundColor Blue
Write-Host "==================================" -ForegroundColor Blue
Write-Host ""

# Function to check prerequisites
function Check-Prerequisites {
    Write-Host "Checking prerequisites..." -ForegroundColor Yellow
    
    # Check Docker
    try {
        docker info | Out-Null
        Write-Host "[SUCCESS] Docker is running" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
        exit 1
    }
    
    # Check kubectl
    try {
        kubectl version --client --short | Out-Null
        Write-Host "[SUCCESS] kubectl is available" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] kubectl not found. Please enable Kubernetes in Docker Desktop." -ForegroundColor Red
        exit 1
    }
    
    # Check Kubernetes cluster
    try {
        kubectl cluster-info | Out-Null
        Write-Host "[SUCCESS] Kubernetes cluster is running" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Cannot connect to Kubernetes. Make sure it's enabled in Docker Desktop." -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
}

# Function to build all containers
function Build-All {
    Write-Host "STEP 1: Building all containers..." -ForegroundColor Blue
    Write-Host "====================================" -ForegroundColor Blue
    
    # Build Frontend
    Write-Host "Building frontend..." -ForegroundColor Yellow
    docker build -t codelens-frontend:latest ./frontend
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Frontend build failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "[SUCCESS] Frontend built successfully" -ForegroundColor Green
    
    # Build Backend
    Write-Host "Building backend..." -ForegroundColor Yellow
    docker build -t codelens-backend:latest ./backend
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Backend build failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "[SUCCESS] Backend built successfully" -ForegroundColor Green
    
    # Build Test Runner
    Write-Host "Building test runner..." -ForegroundColor Yellow
    docker build -t codelens-test-runner:latest ./test-runner
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Test runner build failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "[SUCCESS] Test runner built successfully" -ForegroundColor Green
    
    Write-Host ""
}

# Function to stop existing application
function Stop-Existing {
    Write-Host "STEP 2: Stopping existing application..." -ForegroundColor Blue
    Write-Host "===========================================" -ForegroundColor Blue
    
    kubectl delete -f k8s/frontend.yaml --ignore-not-found=true 2>$null
    kubectl delete -f k8s/backend.yaml --ignore-not-found=true 2>$null
    kubectl delete -f k8s/test-runner.yaml --ignore-not-found=true 2>$null
    
    Write-Host "[SUCCESS] Previous application stopped" -ForegroundColor Green
    Write-Host ""
}

# Function to start new application
function Start-New {
    Write-Host "STEP 3: Starting new application..." -ForegroundColor Blue
    Write-Host "======================================" -ForegroundColor Blue
    
    # Deploy services
    Write-Host "Starting test runner..." -ForegroundColor Yellow
    kubectl apply -f k8s/test-runner.yaml
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to start test runner" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Starting backend..." -ForegroundColor Yellow
    kubectl apply -f k8s/backend.yaml
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to start backend" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Starting frontend..." -ForegroundColor Yellow
    kubectl apply -f k8s/frontend.yaml
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to start frontend" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "[SUCCESS] Application started successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
    Write-Host ""
}

# Function to setup port forwarding
function Setup-Connections {
    Write-Host "STEP 4: Setting up connections..." -ForegroundColor Blue
    Write-Host "====================================" -ForegroundColor Blue
    
    # Check if pods are running
    $pods = kubectl get pods -l app=codelens -o jsonpath='{.items[*].status.phase}' 2>$null
    if (-not $pods -or $pods -notmatch "Running") {
        Write-Host "[WARNING] Pods are still starting up..." -ForegroundColor Yellow
        Write-Host "   Waiting a bit more..." -ForegroundColor White
        Start-Sleep -Seconds 10
    }
    
    Write-Host "Current pod status:" -ForegroundColor Yellow
    kubectl get pods -l app=codelens
    Write-Host ""
    
    Write-Host "Setting up port forwarding..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Starting port forwarding in background..." -ForegroundColor Blue
    
    # Start port forwarding in background jobs
    Start-Job -ScriptBlock { kubectl port-forward service/codelens-frontend 3000:3000 } -Name "frontend-port-forward" | Out-Null
    Start-Job -ScriptBlock { kubectl port-forward service/codelens-backend 8000:8000 } -Name "backend-port-forward" | Out-Null
    Start-Job -ScriptBlock { kubectl port-forward service/codelens-test-runner 8001:8001 } -Name "test-runner-port-forward" | Out-Null
    
    # Wait a moment for port forwarding to establish
    Start-Sleep -Seconds 3
    
    Write-Host "[SUCCESS] Port forwarding active!" -ForegroundColor Green
    Write-Host ""
}

# Function to show final status
function Show-Completion {
    Write-Host "DEPLOYMENT COMPLETE!" -ForegroundColor Green
    Write-Host "========================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your CodeLens application is now running!" -ForegroundColor Blue
    Write-Host ""
    Write-Host "Access your application:" -ForegroundColor Yellow
    Write-Host "  Frontend:    http://localhost:3000" -ForegroundColor White
    Write-Host "  Backend:     http://localhost:8000" -ForegroundColor White
    Write-Host "  Test Runner: http://localhost:8001" -ForegroundColor White
    Write-Host ""
    Write-Host "Useful commands:" -ForegroundColor Yellow
    Write-Host "  Get-Job                     # See port forwarding status" -ForegroundColor White
    Write-Host "  Stop-Job *port-forward*     # Stop port forwarding" -ForegroundColor White
    Write-Host "  kubectl get pods            # Check pod status" -ForegroundColor White
    Write-Host "  .\scripts\stop.ps1          # Stop the application" -ForegroundColor White
    Write-Host ""
    Write-Host "To stop everything:" -ForegroundColor Red
    Write-Host "  1. Press Ctrl+C to stop this script" -ForegroundColor White
    Write-Host "  2. Run: Stop-Job *port-forward*; Remove-Job *port-forward*" -ForegroundColor White
    Write-Host "  3. Run: .\scripts\stop.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "Press Ctrl+C to stop port forwarding and exit..." -ForegroundColor Yellow
    
    # Keep script running to maintain port forwarding
    try {
        while ($true) {
            Start-Sleep -Seconds 5
            # Check if any jobs failed and restart them
            $allJobs = Get-Job 2>$null | Where-Object { $_.Name -like "*port-forward*" -and $_.State -eq "Failed" }
            if ($allJobs) {
                Write-Host "[WARNING] Restarting failed port forwarding..." -ForegroundColor Yellow
                $allJobs | Remove-Job -Force
                Start-Job -ScriptBlock { kubectl port-forward service/codelens-frontend 3000:3000 } -Name "frontend-port-forward" | Out-Null
                Start-Job -ScriptBlock { kubectl port-forward service/codelens-backend 8000:8000 } -Name "backend-port-forward" | Out-Null
                Start-Job -ScriptBlock { kubectl port-forward service/codelens-test-runner 8001:8001 } -Name "test-runner-port-forward" | Out-Null
            }
        }
    } finally {
        Write-Host ""
        Write-Host "Cleaning up port forwarding..." -ForegroundColor Yellow
        Get-Job -Name "*port-forward*" 2>$null | Stop-Job 2>$null
        Get-Job -Name "*port-forward*" 2>$null | Remove-Job 2>$null
        Write-Host "[SUCCESS] Cleanup complete" -ForegroundColor Green
    }
}

# Main execution flow
Check-Prerequisites
Build-All
Stop-Existing  
Start-New
Setup-Connections
Show-Completion
