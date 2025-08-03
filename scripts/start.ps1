# Start Script - Starts CodeLens application in Kubernetes
# Make sure you run build.ps1 first!

Write-Host "Starting CodeLens Application..." -ForegroundColor Blue
Write-Host "================================" -ForegroundColor Blue

# Check if kubectl is available
try {
    kubectl version --client --short | Out-Null
    Write-Host "[SUCCESS] kubectl is available" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] kubectl not found. Please enable Kubernetes in Docker Desktop." -ForegroundColor Red
    Write-Host "   Go to Docker Desktop -> Settings -> Kubernetes -> Enable Kubernetes" -ForegroundColor Yellow
    exit 1
}

# Check if cluster is accessible
try {
    kubectl cluster-info | Out-Null
    Write-Host "[SUCCESS] Kubernetes cluster is running" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Cannot connect to Kubernetes cluster." -ForegroundColor Red
    Write-Host "   Make sure Docker Desktop is running with Kubernetes enabled." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Starting application..." -ForegroundColor Yellow

# Deploy services
Write-Host "Starting test runner..." -ForegroundColor Blue
kubectl apply -f k8s/test-runner.yaml
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to start test runner" -ForegroundColor Red
    exit 1
}

Write-Host "Starting backend..." -ForegroundColor Blue
kubectl apply -f k8s/backend.yaml
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to start backend" -ForegroundColor Red
    exit 1
}

Write-Host "Starting frontend..." -ForegroundColor Blue
kubectl apply -f k8s/frontend.yaml
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to start frontend" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[SUCCESS] Application started successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check status
Write-Host ""
Write-Host "[STATUS] Current Status:" -ForegroundColor Blue
kubectl get pods -l app=codelens

Write-Host ""
Write-Host "[INFO] To access your application:" -ForegroundColor Green
Write-Host ""
Write-Host "  Open 3 separate PowerShell windows and run these commands:" -ForegroundColor Yellow
Write-Host "    kubectl port-forward service/codelens-frontend 3000:3000" -ForegroundColor White
Write-Host "    kubectl port-forward service/codelens-backend 8000:8000" -ForegroundColor White  
Write-Host "    kubectl port-forward service/codelens-test-runner 8001:8001" -ForegroundColor White
Write-Host ""
Write-Host "  Then open your browser:" -ForegroundColor Yellow
Write-Host "    Frontend:    http://localhost:3000" -ForegroundColor White
Write-Host "    Backend:     http://localhost:8000" -ForegroundColor White
Write-Host "    Test Runner: http://localhost:8001" -ForegroundColor White
Write-Host ""
Write-Host "[INFO] Useful commands:" -ForegroundColor Blue
Write-Host "  .\stop.ps1              # Stop the application" -ForegroundColor White
Write-Host "  kubectl get pods        # Check if pods are running" -ForegroundColor White
Write-Host "  kubectl logs -f <pod>   # View logs from a specific pod" -ForegroundColor White
