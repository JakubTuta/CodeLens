# CodeLens - Local Development Script
# Runs CodeLens on local Kubernetes (Docker Desktop)

Write-Host "CodeLens - Local Development" -ForegroundColor Blue
Write-Host "============================" -ForegroundColor Blue
Write-Host ""

# Check prerequisites
Write-Host "Checking requirements..." -ForegroundColor Yellow

# Check Docker
try {
    docker info | Out-Null
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check kubectl
try {
    kubectl version --client --short | Out-Null
    Write-Host "✓ kubectl is available" -ForegroundColor Green
} catch {
    Write-Host "✗ kubectl not found. Please enable Kubernetes in Docker Desktop." -ForegroundColor Red
    Write-Host "  Go to Docker Desktop → Settings → Kubernetes → Enable Kubernetes" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check cluster
try {
    kubectl cluster-info | Out-Null
    Write-Host "✓ Kubernetes cluster is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Cannot connect to Kubernetes cluster." -ForegroundColor Red
    Write-Host "  Make sure Docker Desktop is running with Kubernetes enabled." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if images exist
Write-Host ""
Write-Host "Checking Docker images..." -ForegroundColor Yellow
$missingImages = @()

$images = @("codelens-frontend:latest", "codelens-backend:latest", "codelens-test-runner:latest")
foreach ($image in $images) {
    if (!(docker images -q $image 2>$null)) {
        $missingImages += $image
    } else {
        Write-Host "✓ $image found" -ForegroundColor Green
    }
}

if ($missingImages.Count -gt 0) {
    Write-Host ""
    Write-Host "✗ Missing Docker images:" -ForegroundColor Red
    foreach ($image in $missingImages) {
        Write-Host "  - $image" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Run .\scripts\build.ps1 first to build the images." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "What would you like to do?" -ForegroundColor Cyan
Write-Host "1. Start CodeLens" -ForegroundColor White
Write-Host "2. Stop CodeLens" -ForegroundColor White
Write-Host "3. Restart CodeLens" -ForegroundColor White
Write-Host "4. View Status" -ForegroundColor White
Write-Host ""
$choice = Read-Host "Enter your choice (1-4)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Starting CodeLens..." -ForegroundColor Green
        
        # Deploy services
        kubectl apply -f k8s/local/rbac.yaml
        kubectl apply -f k8s/local/test-runner.yaml
        kubectl apply -f k8s/local/backend.yaml
        kubectl apply -f k8s/local/frontend.yaml
        
        Write-Host ""
        Write-Host "Waiting for services to start..." -ForegroundColor Yellow
        Start-Sleep -Seconds 15
        
        # Show status
        Write-Host ""
        Write-Host "Current Status:" -ForegroundColor Cyan
        kubectl get pods -l app=codelens
        
        Write-Host ""
        Write-Host "✓ CodeLens started successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "To access your application, run these commands in separate terminals:" -ForegroundColor Cyan
        Write-Host "  kubectl port-forward service/codelens-frontend 3000:3000" -ForegroundColor White
        Write-Host "  kubectl port-forward service/codelens-backend 8000:8000" -ForegroundColor White
        Write-Host ""
        Write-Host "Then open: http://localhost:3000" -ForegroundColor Yellow
    }
    
    "2" {
        Write-Host ""
        Write-Host "Stopping CodeLens..." -ForegroundColor Yellow
        
        kubectl delete -f k8s/local/frontend.yaml --ignore-not-found=true
        kubectl delete -f k8s/local/backend.yaml --ignore-not-found=true
        kubectl delete -f k8s/local/test-runner.yaml --ignore-not-found=true
        kubectl delete -f k8s/local/rbac.yaml --ignore-not-found=true
        
        Write-Host ""
        Write-Host "✓ CodeLens stopped successfully!" -ForegroundColor Green
    }
    
    "3" {
        Write-Host ""
        Write-Host "Restarting CodeLens..." -ForegroundColor Yellow
        
        # Stop first
        kubectl delete -f k8s/local/frontend.yaml --ignore-not-found=true
        kubectl delete -f k8s/local/backend.yaml --ignore-not-found=true
        kubectl delete -f k8s/local/test-runner.yaml --ignore-not-found=true
        kubectl delete -f k8s/local/rbac.yaml --ignore-not-found=true
        
        Start-Sleep -Seconds 5
        
        # Start again
        kubectl apply -f k8s/local/rbac.yaml
        kubectl apply -f k8s/local/test-runner.yaml
        kubectl apply -f k8s/local/backend.yaml
        kubectl apply -f k8s/local/frontend.yaml
        
        Write-Host ""
        Write-Host "✓ CodeLens restarted successfully!" -ForegroundColor Green
    }
    
    "4" {
        Write-Host ""
        Write-Host "CodeLens Status:" -ForegroundColor Cyan
        Write-Host ""
        
        Write-Host "Pods:" -ForegroundColor Yellow
        kubectl get pods -l app=codelens
        
        Write-Host ""
        Write-Host "Services:" -ForegroundColor Yellow
        kubectl get services -l app=codelens
    }
    
    default {
        Write-Host "Invalid choice. Exiting." -ForegroundColor Red
    }
}

Write-Host ""
Read-Host "Press Enter to continue"
