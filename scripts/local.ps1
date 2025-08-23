# CodeLens - Local Development Script
# Runs CodeLens on local Kubernetes (Docker Desktop) with full automation

param(
    [switch]$Stop,
    [switch]$Status,
    [switch]$Auto,
    [switch]$ForceStop
)

Write-Host "CodeLens - Local Development" -ForegroundColor Blue
Write-Host "============================" -ForegroundColor Blue
Write-Host ""

# Ensure we're using the correct kubectl context for local development
Write-Host "Setting kubectl context for local development..." -ForegroundColor Yellow
$currentContext = kubectl config current-context 2>$null
if ($currentContext) {
    Write-Host "Current context: $currentContext" -ForegroundColor Gray
    
    # Check if we're using Docker Desktop context
    if ($currentContext -match "docker-desktop|docker-for-desktop") {
        Write-Host "[OK] Already using Docker Desktop context" -ForegroundColor Green
    } else {
        Write-Host "Switching from GKE context to Docker Desktop..." -ForegroundColor Yellow
        
        # Try to switch to docker-desktop context
        kubectl config use-context docker-desktop 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] Switched to docker-desktop context" -ForegroundColor Green
        } else {
            # Try alternative context name
            kubectl config use-context docker-for-desktop 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "[OK] Switched to docker-for-desktop context" -ForegroundColor Green
            } else {
                Write-Host "[WARNING] Could not switch to Docker Desktop context automatically" -ForegroundColor Yellow
                Write-Host "Available contexts:" -ForegroundColor Gray
                kubectl config get-contexts --no-headers | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
                Write-Host ""
                Write-Host "Please manually switch with: kubectl config use-context docker-desktop" -ForegroundColor Yellow
            }
        }
    }
} else {
    Write-Host "[WARNING] No current kubectl context found" -ForegroundColor Yellow
}
Write-Host ""

# Function to check if port is available
function Test-Port {
    param([int]$Port)
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any, $Port)
        $listener.Start()
        $listener.Stop()
        return $true
    } catch {
        return $false
    }
}

# Function to check Kubernetes cluster connectivity
function Test-KubernetesConnectivity {
    try {
        $null = kubectl cluster-info --request-timeout=5s 2>$null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

# Function to check Docker Desktop health
function Test-DockerHealth {
    try {
        # Quick docker info check
        $dockerInfo = docker info --format "{{.ServerVersion}}" 2>$null
        if ($dockerInfo) {
            return $true
        }
        return $false
    } catch {
        return $false
    }
}

# Function to wait for pods to be ready
function Wait-ForPods {
    param([int]$TimeoutSeconds = 120)
    
    Write-Host "Waiting for pods to be ready..." -ForegroundColor Yellow
    $timeout = (Get-Date).AddSeconds($TimeoutSeconds)
    
    do {
        $pods = kubectl get pods -l app=codelens -o jsonpath='{.items[*].status.phase}' 2>$null
        if ($pods -and ($pods -split ' ' | Where-Object { $_ -ne 'Running' }).Count -eq 0) {
            Write-Host "All pods are running!" -ForegroundColor Green
            return $true
        }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $timeout)
    
    Write-Host "Timeout waiting for pods to be ready" -ForegroundColor Red
    return $false
}

# Function to kill existing port forwards
function Stop-PortForwards {
    Write-Host "Stopping existing port forwards..." -ForegroundColor Yellow
    
    # Only target kubectl port-forward processes, not all processes using the ports
    $kubectlProcesses = Get-Process | Where-Object { 
        $_.ProcessName -eq "kubectl" -and 
        $_.CommandLine -like "*port-forward*" -and
        ($_.CommandLine -like "*3000:3000*" -or $_.CommandLine -like "*8000:8000*")
    }
    
    if ($kubectlProcesses) {
        Write-Host "Found $($kubectlProcesses.Count) kubectl port-forward process(es), stopping gracefully..." -ForegroundColor Yellow
        
        foreach ($process in $kubectlProcesses) {
            try {
                Write-Host "  Stopping kubectl port-forward (PID: $($process.Id))..." -ForegroundColor Gray
                
                # Try graceful termination first with timeout
                if (-not $process.HasExited) {
                    $process.CloseMainWindow()
                    
                    # Wait up to 3 seconds for graceful exit
                    $timeout = 30 # 3 seconds in 100ms increments
                    while (-not $process.HasExited -and $timeout -gt 0) {
                        Start-Sleep -Milliseconds 100
                        $timeout--
                    }
                    
                    # If still running after graceful attempt, force stop
                    if (-not $process.HasExited) {
                        Write-Host "    Graceful stop failed, forcing termination..." -ForegroundColor Gray
                        $process | Stop-Process -Force -ErrorAction SilentlyContinue
                    } else {
                        Write-Host "    Stopped gracefully" -ForegroundColor Green
                    }
                }
            } catch {
                Write-Host "    Warning: Could not stop process $($process.Id): $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
        
        # Brief wait for cleanup
        Start-Sleep -Seconds 1
    } else {
        Write-Host "  No kubectl port-forward processes found" -ForegroundColor Gray
    }
    
    # Check if there are any other kubectl processes that might be using our ports
    $otherKubectl = Get-Process | Where-Object { 
        $_.ProcessName -eq "kubectl" -and 
        $_.CommandLine -notlike "*port-forward*"
    }
    
    if ($otherKubectl) {
        Write-Host "  Found other kubectl processes, leaving them running" -ForegroundColor Gray
    }
}

# Handle command line parameters first
if ($Status) {
    Write-Host "CodeLens Status:" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "Pods:" -ForegroundColor Yellow
    kubectl get pods -l app=codelens 2>$null
    
    Write-Host ""
    Write-Host "Services:" -ForegroundColor Yellow
    kubectl get services -l app=codelens 2>$null
    
    Write-Host ""
    Write-Host "Port forwards:" -ForegroundColor Yellow
    $portForwards = Get-Process | Where-Object { $_.ProcessName -eq "kubectl" -and $_.CommandLine -like "*port-forward*" }
    if ($portForwards) {
        $portForwards | ForEach-Object { Write-Host "  $($_.CommandLine)" -ForegroundColor White }
    } else {
        Write-Host "  No active port forwards" -ForegroundColor Gray
    }
    
    exit 0
}

if ($ForceStop) {
    Write-Host "Force Stopping CodeLens..." -ForegroundColor Red
    Write-Host "This will aggressively terminate all processes and may cause Docker Desktop to restart." -ForegroundColor Yellow
    Write-Host ""
    
    # Force stop all kubectl processes
    Write-Host "Force stopping all kubectl processes..." -ForegroundColor Yellow
    Get-Process | Where-Object { $_.ProcessName -eq "kubectl" } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    # Force stop processes using our ports
    Write-Host "Force stopping processes using ports 3000 and 8000..." -ForegroundColor Yellow
    try {
        $frontendPort = netstat -ano | Select-String ":3000 " | ForEach-Object { ($_ -split '\s+')[-1] } | Select-Object -First 1
        $backendPort = netstat -ano | Select-String ":8000 " | ForEach-Object { ($_ -split '\s+')[-1] } | Select-Object -First 1
        
        if ($frontendPort -and $frontendPort -ne "0") {
            Stop-Process -Id $frontendPort -Force -ErrorAction SilentlyContinue
        }
        if ($backendPort -and $backendPort -ne "0") {
            Stop-Process -Id $backendPort -Force -ErrorAction SilentlyContinue
        }
    } catch {
        Write-Host "  Could not force stop port processes" -ForegroundColor Yellow
    }
    
    # Try to delete Kubernetes resources if possible
    Write-Host "Attempting to remove Kubernetes resources..." -ForegroundColor Yellow
    kubectl delete -f k8s/local/frontend.yaml --ignore-not-found=true --timeout=10s 2>$null
    kubectl delete -f k8s/local/backend.yaml --ignore-not-found=true --timeout=10s 2>$null
    kubectl delete -f k8s/local/test-runner.yaml --ignore-not-found=true --timeout=10s 2>$null
    kubectl delete -f k8s/local/rbac.yaml --ignore-not-found=true --timeout=10s 2>$null
    
    Write-Host ""
    Write-Host "Force stop completed. If Docker Desktop became unresponsive, restart it." -ForegroundColor Red
    exit 0
}

if ($Stop) {
    Write-Host "Stopping CodeLens..." -ForegroundColor Yellow
    
    # Check Docker and Kubernetes health first, before any cleanup attempts
    $dockerHealthy = Test-DockerHealth
    $k8sHealthy = Test-KubernetesConnectivity
    
    if (-not $dockerHealthy) {
        Write-Host "Docker Desktop appears to be unhealthy or stopped." -ForegroundColor Yellow
        Write-Host "If Docker is completely stopped, the containers are already removed." -ForegroundColor Green
        Write-Host "If Docker is running but unresponsive, try restarting Docker Desktop." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "CodeLens stop completed (Docker not accessible)." -ForegroundColor Green
        exit 0
    }
    
    if (-not $k8sHealthy) {
        Write-Host "Cannot connect to Kubernetes cluster." -ForegroundColor Yellow
        Write-Host "This usually means Docker Desktop's Kubernetes is stopping or stopped." -ForegroundColor Yellow
        Write-Host "The pods will be automatically removed when Docker Desktop restarts." -ForegroundColor Green
        Write-Host ""
        
        # Only try to stop port forwards if Kubernetes is down but Docker is up
        Write-Host "Attempting to stop any remaining port forwards..." -ForegroundColor Yellow
        Stop-PortForwards
        
        Write-Host ""
        Write-Host "CodeLens stop completed (Kubernetes not accessible)." -ForegroundColor Green
        exit 0
    }
    
    # Both Docker and Kubernetes are healthy, proceed with normal cleanup
    Write-Host "Docker and Kubernetes are accessible, proceeding with graceful shutdown..." -ForegroundColor Green
    
    # Stop port forwards first, but only if we're sure the system is stable
    Stop-PortForwards
    
    # Delete resources with proper waiting and error handling
    Write-Host "Removing Kubernetes resources..." -ForegroundColor Yellow
    
    # Delete in reverse order with delays and better error handling
    Write-Host "  Removing frontend..." -ForegroundColor Gray
    kubectl delete -f k8s/local/frontend.yaml --ignore-not-found=true --wait=true --timeout=20s 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "    Warning: Failed to remove frontend (this is usually harmless)" -ForegroundColor Yellow
    } else {
        Write-Host "    Frontend removed successfully" -ForegroundColor Green
    }
    Start-Sleep -Seconds 1
    
    Write-Host "  Removing backend..." -ForegroundColor Gray
    kubectl delete -f k8s/local/backend.yaml --ignore-not-found=true --wait=true --timeout=20s 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "    Warning: Failed to remove backend (this is usually harmless)" -ForegroundColor Yellow
    } else {
        Write-Host "    Backend removed successfully" -ForegroundColor Green
    }
    Start-Sleep -Seconds 1
    
    Write-Host "  Removing test runner..." -ForegroundColor Gray
    kubectl delete -f k8s/local/test-runner.yaml --ignore-not-found=true --wait=true --timeout=20s 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "    Warning: Failed to remove test runner (this is usually harmless)" -ForegroundColor Yellow
    } else {
        Write-Host "    Test runner removed successfully" -ForegroundColor Green
    }
    Start-Sleep -Seconds 1
    
    Write-Host "  Removing RBAC..." -ForegroundColor Gray
    kubectl delete -f k8s/local/rbac.yaml --ignore-not-found=true --wait=true --timeout=20s 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "    Warning: Failed to remove RBAC (this is usually harmless)" -ForegroundColor Yellow
    } else {
        Write-Host "    RBAC removed successfully" -ForegroundColor Green
    }
    
    # Wait for cleanup to complete
    Write-Host "Waiting for cleanup to complete..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
    
    # Verify cleanup if Kubernetes is still accessible
    if (Test-KubernetesConnectivity) {
        $remainingPods = kubectl get pods -l app=codelens --no-headers 2>$null
        if ($remainingPods) {
            Write-Host "Some pods may still be terminating:" -ForegroundColor Yellow
            Write-Host $remainingPods -ForegroundColor Gray
            Write-Host "This is normal and they should terminate shortly." -ForegroundColor Yellow
        } else {
            Write-Host "All CodeLens resources have been removed successfully." -ForegroundColor Green
        }
    } else {
        Write-Host "Cannot verify cleanup - Kubernetes cluster became unavailable during cleanup." -ForegroundColor Yellow
        Write-Host "This can happen if Docker Desktop is shutting down, but cleanup likely succeeded." -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "CodeLens stopped successfully!" -ForegroundColor Green
    exit 0
}

# Check prerequisites
Write-Host "Checking requirements..." -ForegroundColor Yellow

# Check Docker
try {
    docker info | Out-Null
    Write-Host "[OK] Docker is running" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check kubectl
try {
    kubectl version --client | Out-Null
    Write-Host "[OK] kubectl is available" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] kubectl not found. Please enable Kubernetes in Docker Desktop." -ForegroundColor Red
    Write-Host "  Go to Docker Desktop → Settings → Kubernetes → Enable Kubernetes" -ForegroundColor Yellow
    exit 1
}

# Check cluster
try {
    kubectl cluster-info | Out-Null
    Write-Host "[OK] Kubernetes cluster is running" -ForegroundColor Green
    
    # Verify we're still using the correct context
    $currentContext = kubectl config current-context 2>$null
    if ($currentContext -and $currentContext -match "docker-desktop|docker-for-desktop") {
        Write-Host "[OK] Using Docker Desktop Kubernetes context: $currentContext" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Context changed unexpectedly. Current context: '$currentContext'" -ForegroundColor Red
        Write-Host "This shouldn't happen after context was set at startup." -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "[ERROR] Cannot connect to Kubernetes cluster." -ForegroundColor Red
    Write-Host "  Make sure Docker Desktop is running with Kubernetes enabled." -ForegroundColor Yellow
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
        Write-Host "[OK] $image found" -ForegroundColor Green
    }
}

if ($missingImages.Count -gt 0) {
    Write-Host ""
    Write-Host "Missing Docker images:" -ForegroundColor Red
    foreach ($image in $missingImages) {
        Write-Host "  - $image" -ForegroundColor Red
    }
    Write-Host ""
    
    if ($Auto) {
        Write-Host "Building missing images..." -ForegroundColor Yellow
        & ".\scripts\build.ps1"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Failed to build images. Exiting." -ForegroundColor Red
            exit 1
        }
        
        # Verify images are now available
        Write-Host "Verifying built images..." -ForegroundColor Yellow
        foreach ($image in $images) {
            if (!(docker images -q $image 2>$null)) {
                Write-Host "[ERROR] Image $image still not found after build" -ForegroundColor Red
                exit 1
            } else {
                Write-Host "[OK] $image verified" -ForegroundColor Green
            }
        }
    } else {
        Write-Host "Run .\scripts\build.ps1 first to build the images." -ForegroundColor Yellow
        exit 1
    }
}

# Show menu if no Auto parameter
if (-not $Auto) {
    Write-Host ""
    Write-Host "What would you like to do?" -ForegroundColor Cyan
    Write-Host "1. Start CodeLens" -ForegroundColor White
    Write-Host "2. Stop CodeLens (graceful)" -ForegroundColor White
    Write-Host "3. Restart CodeLens" -ForegroundColor White
    Write-Host "4. View Status" -ForegroundColor White
    Write-Host "5. Force Stop (if graceful stop fails)" -ForegroundColor Red
    Write-Host ""
    $choice = Read-Host "Enter your choice (1-5)"
} else {
    # Auto mode defaults to start
    $choice = "1"
}

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Starting CodeLens..." -ForegroundColor Green
        
        # Check for existing deployments
        Write-Host "Checking for existing deployments..." -ForegroundColor Yellow
        $existingPods = kubectl get pods -l app=codelens --no-headers 2>$null
        if ($existingPods) {
            Write-Host ""
            Write-Host "ERROR: CodeLens is already running!" -ForegroundColor Red
            Write-Host "Found existing pods:" -ForegroundColor Yellow
            Write-Host $existingPods -ForegroundColor Gray
            Write-Host ""
            Write-Host "Please stop the existing deployment first:" -ForegroundColor Cyan
            Write-Host "  .\scripts\local.ps1 -Stop" -ForegroundColor White
            Write-Host "  OR" -ForegroundColor White
            Write-Host "  .\scripts\local.ps1 and choose option 2 (Stop)" -ForegroundColor White
            Write-Host ""
            Write-Host "Alternatively, you can restart (which stops and starts):" -ForegroundColor Cyan
            Write-Host "  .\scripts\local.ps1 and choose option 3 (Restart)" -ForegroundColor White
            Write-Host ""
            exit 1
        }
        
        # Check for port conflicts
        Write-Host "Checking port availability..." -ForegroundColor Yellow
        
        if (-not (Test-Port 3000)) {
            Write-Host ""
            Write-Host "ERROR: Port 3000 is already in use!" -ForegroundColor Red
            Write-Host "Please stop the process using port 3000 or use:" -ForegroundColor Cyan
            Write-Host "  .\scripts\local.ps1 -Stop" -ForegroundColor White
            Write-Host ""
            exit 1
        }
        
        if (-not (Test-Port 8000)) {
            Write-Host ""
            Write-Host "ERROR: Port 8000 is already in use!" -ForegroundColor Red
            Write-Host "Please stop the process using port 8000 or use:" -ForegroundColor Cyan
            Write-Host "  .\scripts\local.ps1 -Stop" -ForegroundColor White
            Write-Host ""
            exit 1
        }
        
        Write-Host "[OK] No conflicts found, proceeding with deployment..." -ForegroundColor Green
        
        # Deploy services
        Write-Host "Deploying services..." -ForegroundColor Yellow
        kubectl apply -f k8s/local/rbac.yaml
        kubectl apply -f k8s/local/test-runner.yaml
        kubectl apply -f k8s/local/backend.yaml
        kubectl apply -f k8s/local/frontend.yaml
        
        # Wait for pods to be ready
        if (-not (Wait-ForPods)) {
            Write-Host "Failed to start pods. Check 'kubectl get pods -l app=codelens' for details." -ForegroundColor Red
            exit 1
        }
        
        # Start port forwarding in background
        Write-Host ""
        Write-Host "Setting up port forwarding..." -ForegroundColor Yellow
        
        $frontendJob = Start-Job -ScriptBlock {
            kubectl port-forward service/codelens-frontend 3000:3000
        }
        
        $backendJob = Start-Job -ScriptBlock {
            kubectl port-forward service/codelens-backend 8000:8000
        }
        
        # Wait a moment for port forwards to establish
        Start-Sleep -Seconds 3
        
        # Verify port forwards are working
        $frontendReady = $false
        $backendReady = $false
        $maxAttempts = 10
        
        for ($i = 1; $i -le $maxAttempts; $i++) {
            Write-Host "Checking port forward status (attempt $i/$maxAttempts)..." -ForegroundColor Yellow
            
            if (-not $frontendReady) {
                try {
                    $response = Invoke-WebRequest -Uri "http://localhost:3000" -Method Head -TimeoutSec 5 -ErrorAction Stop
                    $frontendReady = $true
                    Write-Host "[OK] Frontend port forward is ready" -ForegroundColor Green
                } catch {
                    Write-Host "  Frontend not ready yet..." -ForegroundColor Gray
                }
            }
            
            if (-not $backendReady) {
                try {
                    $response = Invoke-WebRequest -Uri "http://localhost:8000" -Method Head -TimeoutSec 5 -ErrorAction Stop
                    $backendReady = $true
                    Write-Host "[OK] Backend port forward is ready" -ForegroundColor Green
                } catch {
                    Write-Host "  Backend not ready yet..." -ForegroundColor Gray
                }
            }
            
            if ($frontendReady -and $backendReady) {
                break
            }
            
            Start-Sleep -Seconds 3
        }
        
        if (-not $frontendReady -or -not $backendReady) {
            Write-Host "Warning: Some services may not be fully ready yet." -ForegroundColor Yellow
        }
        
        # Show final status
        Write-Host ""
        Write-Host "=================================" -ForegroundColor Green
        Write-Host "CodeLens is now running!" -ForegroundColor Green
        Write-Host "=================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
        Write-Host "Backend:  http://localhost:8000" -ForegroundColor Cyan
        Write-Host ""
        
        if ($Auto) {
            Write-Host "Port forwards are running in background jobs." -ForegroundColor Gray
            Write-Host "Press Ctrl+C to stop this script (port forwards will continue)." -ForegroundColor Gray
            
            # Keep script running to maintain port forwards in foreground in Auto mode
            try {
                while ($true) {
                    Start-Sleep -Seconds 30
                    
                    # Check if jobs are still running
                    if ($frontendJob.State -ne "Running" -or $backendJob.State -ne "Running") {
                        Write-Host ""
                        Write-Host "Port forward jobs have stopped. Restarting..." -ForegroundColor Yellow
                        
                        if ($frontendJob.State -ne "Running") {
                            $frontendJob = Start-Job -ScriptBlock {
                                kubectl port-forward service/codelens-frontend 3000:3000
                            }
                        }
                        
                        if ($backendJob.State -ne "Running") {
                            $backendJob = Start-Job -ScriptBlock {
                                kubectl port-forward service/codelens-backend 8000:8000
                            }
                        }
                    }
                }
            } finally {
                # Cleanup jobs when script exits
                Remove-Job $frontendJob -Force -ErrorAction SilentlyContinue
                Remove-Job $backendJob -Force -ErrorAction SilentlyContinue
            }
        }
    }
    
    "2" {
        Write-Host ""
        Write-Host "Stopping CodeLens..." -ForegroundColor Yellow
        
        # Check Docker health first
        if (-not (Test-DockerHealth)) {
            Write-Host "Warning: Docker Desktop appears to be unhealthy or stopped." -ForegroundColor Yellow
            Write-Host "If Docker is completely stopped, the containers are already removed." -ForegroundColor Green
            Write-Host "If Docker is running but unresponsive, try restarting Docker Desktop." -ForegroundColor Yellow
            Write-Host ""
            Write-Host "CodeLens stop completed (Docker not accessible)." -ForegroundColor Green
            return
        }
        
        # Check Kubernetes connectivity
        if (-not (Test-KubernetesConnectivity)) {
            Write-Host "Warning: Cannot connect to Kubernetes cluster." -ForegroundColor Yellow
            Write-Host "This usually means Docker Desktop's Kubernetes is stopping or stopped." -ForegroundColor Yellow
            Write-Host "The pods will be automatically removed when Docker Desktop restarts." -ForegroundColor Green
            Write-Host ""
            
            # Try to stop port forwards anyway
            Write-Host "Attempting to stop any remaining port forwards..." -ForegroundColor Yellow
            Stop-PortForwards
            
            Write-Host ""
            Write-Host "CodeLens stop completed (Kubernetes not accessible)." -ForegroundColor Green
            return
        }
        
        # Stop port forwards first
        Stop-PortForwards
        
        # Delete resources with proper waiting and error handling
        Write-Host "Removing Kubernetes resources..." -ForegroundColor Yellow
        
        Write-Host "  Removing frontend..." -ForegroundColor Gray
        kubectl delete -f k8s/local/frontend.yaml --ignore-not-found=true --wait=true --timeout=30s 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "    Warning: Failed to remove frontend (this is usually harmless)" -ForegroundColor Yellow
        }
        Start-Sleep -Seconds 2
        
        Write-Host "  Removing backend..." -ForegroundColor Gray
        kubectl delete -f k8s/local/backend.yaml --ignore-not-found=true --wait=true --timeout=30s 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "    Warning: Failed to remove backend (this is usually harmless)" -ForegroundColor Yellow
        }
        Start-Sleep -Seconds 2
        
        Write-Host "  Removing test runner..." -ForegroundColor Gray
        kubectl delete -f k8s/local/test-runner.yaml --ignore-not-found=true --wait=true --timeout=30s 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "    Warning: Failed to remove test runner (this is usually harmless)" -ForegroundColor Yellow
        }
        Start-Sleep -Seconds 2
        
        Write-Host "  Removing RBAC..." -ForegroundColor Gray
        kubectl delete -f k8s/local/rbac.yaml --ignore-not-found=true --wait=true --timeout=30s 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "    Warning: Failed to remove RBAC (this is usually harmless)" -ForegroundColor Yellow
        }
        
        # Wait for cleanup to complete
        Write-Host "Waiting for cleanup to complete..." -ForegroundColor Yellow
        Start-Sleep -Seconds 3
        
        # Verify cleanup if Kubernetes is still accessible
        if (Test-KubernetesConnectivity) {
            $remainingPods = kubectl get pods -l app=codelens --no-headers 2>$null
            if ($remainingPods) {
                Write-Host "Warning: Some pods may still be terminating:" -ForegroundColor Yellow
                Write-Host $remainingPods -ForegroundColor Gray
            } else {
                Write-Host "All CodeLens resources have been removed." -ForegroundColor Green
            }
        } else {
            Write-Host "Cannot verify cleanup - Kubernetes cluster became unavailable during cleanup." -ForegroundColor Yellow
            Write-Host "This is normal if Docker Desktop is shutting down." -ForegroundColor Yellow
        }
        
        Write-Host ""
        Write-Host "CodeLens stopped successfully!" -ForegroundColor Green
    }
    
    "3" {
        Write-Host ""
        Write-Host "Restarting CodeLens..." -ForegroundColor Yellow
        
        # Stop first - gracefully
        Write-Host "Stopping existing deployment..." -ForegroundColor Yellow
        Stop-PortForwards
        
        kubectl delete -f k8s/local/frontend.yaml --ignore-not-found=true --wait=true --timeout=30s
        Start-Sleep -Seconds 2
        kubectl delete -f k8s/local/backend.yaml --ignore-not-found=true --wait=true --timeout=30s
        Start-Sleep -Seconds 2
        kubectl delete -f k8s/local/test-runner.yaml --ignore-not-found=true --wait=true --timeout=30s
        Start-Sleep -Seconds 2
        kubectl delete -f k8s/local/rbac.yaml --ignore-not-found=true --wait=true --timeout=30s
        
        Write-Host "Waiting for complete cleanup..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        
        # Start again
        Write-Host "Starting fresh deployment..." -ForegroundColor Yellow
        kubectl apply -f k8s/local/rbac.yaml
        Start-Sleep -Seconds 2
        kubectl apply -f k8s/local/test-runner.yaml
        Start-Sleep -Seconds 2
        kubectl apply -f k8s/local/backend.yaml
        Start-Sleep -Seconds 2
        kubectl apply -f k8s/local/frontend.yaml
        
        # Wait for pods to be ready
        if (Wait-ForPods) {
            Write-Host ""
            Write-Host "CodeLens restarted successfully!" -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "CodeLens restarted but some pods may still be starting." -ForegroundColor Yellow
        }
        
        Write-Host ""
        Write-Host "To access your application with port forwarding:" -ForegroundColor Cyan
        Write-Host "  Run: .\scripts\local.ps1 -Auto" -ForegroundColor White
        Write-Host "  Or manually run:" -ForegroundColor White
        Write-Host "    kubectl port-forward service/codelens-frontend 3000:3000" -ForegroundColor Gray
        Write-Host "    kubectl port-forward service/codelens-backend 8000:8000" -ForegroundColor Gray
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
        
        Write-Host ""
        Write-Host "Port forwards:" -ForegroundColor Yellow
        $portForwards = Get-Process | Where-Object { $_.ProcessName -eq "kubectl" -and $_.CommandLine -like "*port-forward*" }
        if ($portForwards) {
            $portForwards | ForEach-Object { Write-Host "  $($_.CommandLine)" -ForegroundColor White }
        } else {
            Write-Host "  No active port forwards" -ForegroundColor Gray
        }
    }
    
    "5" {
        Write-Host ""
        Write-Host "Force Stopping CodeLens..." -ForegroundColor Red
        Write-Host "WARNING: This will aggressively terminate processes and may cause Docker Desktop to restart!" -ForegroundColor Yellow
        Write-Host ""
        $confirm = Read-Host "Are you sure you want to force stop? (y/N)"
        
        if ($confirm -eq "y" -or $confirm -eq "Y") {
            # Force stop all kubectl processes
            Write-Host "Force stopping all kubectl processes..." -ForegroundColor Yellow
            Get-Process | Where-Object { $_.ProcessName -eq "kubectl" } | Stop-Process -Force -ErrorAction SilentlyContinue
            
            # Force stop processes using our ports
            Write-Host "Force stopping processes using ports 3000 and 8000..." -ForegroundColor Yellow
            try {
                $frontendPort = netstat -ano | Select-String ":3000 " | ForEach-Object { ($_ -split '\s+')[-1] } | Select-Object -First 1
                $backendPort = netstat -ano | Select-String ":8000 " | ForEach-Object { ($_ -split '\s+')[-1] } | Select-Object -First 1
                
                if ($frontendPort -and $frontendPort -ne "0") {
                    Stop-Process -Id $frontendPort -Force -ErrorAction SilentlyContinue
                }
                if ($backendPort -and $backendPort -ne "0") {
                    Stop-Process -Id $backendPort -Force -ErrorAction SilentlyContinue
                }
            } catch {
                Write-Host "  Could not force stop port processes" -ForegroundColor Yellow
            }
            
            # Try to delete Kubernetes resources if possible
            Write-Host "Attempting to remove Kubernetes resources..." -ForegroundColor Yellow
            kubectl delete -f k8s/local/frontend.yaml --ignore-not-found=true --timeout=10s 2>$null
            kubectl delete -f k8s/local/backend.yaml --ignore-not-found=true --timeout=10s 2>$null
            kubectl delete -f k8s/local/test-runner.yaml --ignore-not-found=true --timeout=10s 2>$null
            kubectl delete -f k8s/local/rbac.yaml --ignore-not-found=true --timeout=10s 2>$null
            
            Write-Host ""
            Write-Host "Force stop completed. If Docker Desktop became unresponsive, restart it." -ForegroundColor Red
        } else {
            Write-Host "Force stop cancelled." -ForegroundColor Green
        }
    }
    
    default {
        Write-Host "Invalid choice. Exiting." -ForegroundColor Red
    }
}
