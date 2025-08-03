# Connect Script - Sets up port forwarding to access your application
# Run this AFTER start.ps1 in a separate terminal window

Write-Host "Setting up connection to CodeLens..." -ForegroundColor Blue
Write-Host "====================================" -ForegroundColor Blue

# Check if application is running
$pods = kubectl get pods -l app=codelens -o jsonpath='{.items[*].status.phase}' 2>$null
if (-not $pods -or $pods -notmatch "Running") {
    Write-Host "[ERROR] Application is not running!" -ForegroundColor Red
    Write-Host "   Please run: .\start.ps1 first" -ForegroundColor Yellow
    exit 1
}

Write-Host "[SUCCESS] Application is running" -ForegroundColor Green
Write-Host ""
Write-Host "[INFO] Choose which service to connect to:" -ForegroundColor Yellow
Write-Host "  1. Frontend  (Main application interface)" -ForegroundColor White
Write-Host "  2. Backend   (API server)" -ForegroundColor White  
Write-Host "  3. Test Runner (Test execution service)" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter your choice (1, 2, or 3)"

switch ($choice) {
    "1" {
        Write-Host "Connecting to Frontend..." -ForegroundColor Blue
        Write-Host "   Open your browser to: http://localhost:3000" -ForegroundColor Green
        Write-Host "   Press Ctrl+C to stop port forwarding" -ForegroundColor Yellow
        kubectl port-forward service/codelens-frontend 3000:3000
    }
    "2" {
        Write-Host "Connecting to Backend..." -ForegroundColor Blue
        Write-Host "   Open your browser to: http://localhost:8000" -ForegroundColor Green
        Write-Host "   Press Ctrl+C to stop port forwarding" -ForegroundColor Yellow
        kubectl port-forward service/codelens-backend 8000:8000
    }
    "3" {
        Write-Host "Connecting to Test Runner..." -ForegroundColor Blue
        Write-Host "   Open your browser to: http://localhost:8001" -ForegroundColor Green
        Write-Host "   Press Ctrl+C to stop port forwarding" -ForegroundColor Yellow
        kubectl port-forward service/codelens-test-runner 8001:8001
    }
    default {
        Write-Host "[ERROR] Invalid choice. Please run the script again and choose 1, 2, or 3." -ForegroundColor Red
    }
}
