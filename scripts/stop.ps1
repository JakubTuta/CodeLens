# Stop Script - Stops CodeLens application in Kubernetes

Write-Host "Stopping CodeLens Application..." -ForegroundColor Blue
Write-Host "================================" -ForegroundColor Blue

# Check if kubectl is available
try {
    kubectl version --client --short | Out-Null
} catch {
    Write-Host "[ERROR] kubectl not found." -ForegroundColor Red
    exit 1
}

Write-Host "Stopping application..." -ForegroundColor Yellow

# Stop services
kubectl delete -f k8s/frontend.yaml --ignore-not-found=true
kubectl delete -f k8s/backend.yaml --ignore-not-found=true  
kubectl delete -f k8s/test-runner.yaml --ignore-not-found=true

Write-Host ""
Write-Host "[SUCCESS] Application stopped successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "[STATUS] Remaining pods (should be empty):" -ForegroundColor Blue
kubectl get pods -l app=codelens

Write-Host ""
Write-Host "To start again, run: .\start.ps1" -ForegroundColor Yellow
