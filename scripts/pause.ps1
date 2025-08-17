# CodeLens - GCP Pause Script
# Scales CodeLens deployments to zero to save costs

Write-Host "CodeLens - GCP Pause" -ForegroundColor Yellow
Write-Host "===================" -ForegroundColor Yellow
Write-Host ""

# Check if configuration files exist to extract values
$configFiles = @(
    "k8s/gcp/backend.yaml",
    "k8s/gcp/frontend.yaml",
    "k8s/gcp/test-runner.yaml"
)

$existingFiles = @()
foreach ($file in $configFiles) {
    if (Test-Path $file) {
        $existingFiles += $file
    }
}

$skipConfiguration = $false
$PROJECT_ID = ""
$CLUSTER_NAME = ""
$REGION = ""

if ($existingFiles.Count -gt 0) {
    Write-Host "[INFO] Found existing configuration files:" -ForegroundColor Green
    foreach ($file in $existingFiles) {
        Write-Host "  - $file" -ForegroundColor White
    }
    Write-Host ""
    
    $useExisting = Read-Host "Extract configuration from existing files? (y/n)"
    if ($useExisting -eq "y" -or $useExisting -eq "Y") {
        Write-Host "Extracting configuration from existing files..." -ForegroundColor Green
        
        try {
            # Extract configuration from existing files
            if (Test-Path "k8s/gcp/backend.yaml") {
                $backendContent = Get-Content "k8s/gcp/backend.yaml" -Raw
                $registryMatch = $backendContent | Select-String "image: ([^/]+)-docker\.pkg\.dev/([^/]+)/([^/]+)/"
                if ($registryMatch) {
                    $REGION = $registryMatch.Matches[0].Groups[1].Value
                    $PROJECT_ID = $registryMatch.Matches[0].Groups[2].Value
                }
            }
            
            # Default cluster name since it's not stored in YAML files
            $CLUSTER_NAME = "codelens-cluster"
            
            Write-Host "Extracted configuration:" -ForegroundColor Cyan
            Write-Host "  Project ID: $PROJECT_ID" -ForegroundColor White
            Write-Host "  Region: $REGION" -ForegroundColor White
            Write-Host "  Cluster: $CLUSTER_NAME (default assumption)" -ForegroundColor Gray
            Write-Host ""
            
            if ([string]::IsNullOrWhiteSpace($PROJECT_ID)) {
                throw "Could not extract required configuration"
            }
            
            $skipConfiguration = $true
        } catch {
            Write-Host "[WARNING] Could not extract configuration from existing files." -ForegroundColor Yellow
            Write-Host "  Will prompt for configuration manually..." -ForegroundColor Yellow
            $skipConfiguration = $false
        }
    } else {
        Write-Host "Will prompt for configuration manually..." -ForegroundColor Yellow
        $skipConfiguration = $false
    }
}

# Get configuration from user if we couldn't extract it
if (-not $skipConfiguration) {
    Write-Host "Please provide your GCP configuration:" -ForegroundColor Cyan
    Write-Host ""

    $PROJECT_ID = Read-Host "Enter your GCP Project ID"
    if ([string]::IsNullOrWhiteSpace($PROJECT_ID)) {
        Write-Host "[ERROR] Project ID is required" -ForegroundColor Red
        exit 1
    }

    $CLUSTER_NAME = Read-Host "Enter GKE Cluster Name (default: codelens-cluster)" 
    if ([string]::IsNullOrWhiteSpace($CLUSTER_NAME)) {
        $CLUSTER_NAME = "codelens-cluster"
    }

    $REGION = Read-Host "Enter GCP Region (default: europe-central2)"
    if ([string]::IsNullOrWhiteSpace($REGION)) {
        $REGION = "europe-central2"
    }

    Write-Host ""
    Write-Host "Configuration:" -ForegroundColor Yellow
    Write-Host "  Project ID: $PROJECT_ID" -ForegroundColor White
    Write-Host "  Cluster: $CLUSTER_NAME" -ForegroundColor White
    Write-Host "  Region: $REGION" -ForegroundColor White
    Write-Host ""
}

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

# Check kubectl
try {
    kubectl version --client | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "kubectl not working"
    }
    Write-Host "[OK] kubectl is available" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] kubectl not found or not working." -ForegroundColor Red
    Write-Host "  Please ensure kubectl is installed and in your PATH." -ForegroundColor Yellow
    exit 1
}

# Check gcloud CLI
try {
    gcloud version | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "gcloud not working"
    }
    Write-Host "[OK] gcloud CLI is available" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] gcloud CLI not found or not working." -ForegroundColor Red
    Write-Host "  Please ensure Google Cloud CLI is installed and authenticated." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Connecting to GKE cluster..." -ForegroundColor Yellow
gcloud container clusters get-credentials $CLUSTER_NAME --region $REGION --project $PROJECT_ID
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to get cluster credentials." -ForegroundColor Red
    Write-Host "  Please check that the cluster exists and you have access." -ForegroundColor Yellow
    exit 1
}

try {
    kubectl cluster-info | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Cannot connect to cluster"
    }
    Write-Host "[OK] Connected to GKE cluster" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Cannot connect to Kubernetes cluster." -ForegroundColor Red
    Write-Host "  Please check your cluster configuration and network connectivity." -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Get current deployment status
$deployments = @("codelens-frontend", "codelens-backend", "codelens-test-runner")
$currentStatus = @{}

Write-Host "Checking current deployment status..." -ForegroundColor Yellow
foreach ($deployment in $deployments) {
    $replicas = kubectl get deployment $deployment -o jsonpath='{.spec.replicas}' 2>$null
    if ($LASTEXITCODE -eq 0) {
        $currentStatus[$deployment] = [int]$replicas
        $readyReplicas = kubectl get deployment $deployment -o jsonpath='{.status.readyReplicas}' 2>$null
        if (-not $readyReplicas) { $readyReplicas = 0 }
        Write-Host "  $deployment`: $replicas replicas (ready: $readyReplicas)" -ForegroundColor White
    } else {
        Write-Host "  $deployment`: Not found" -ForegroundColor Gray
    }
}

Write-Host ""

Write-Host "PAUSING CodeLens Application" -ForegroundColor Yellow
Write-Host "============================" -ForegroundColor Yellow
Write-Host ""

# Check if already paused
$pausedDeployments = 0
$hasNetworkingResources = $false

foreach ($deployment in $deployments) {
    if ($currentStatus.ContainsKey($deployment) -and $currentStatus[$deployment] -eq 0) {
        $pausedDeployments++
    }
}

# Check for active networking resources
$ingressExists = kubectl get ingress codelens-ingress 2>$null
if ($LASTEXITCODE -eq 0) {
    $hasNetworkingResources = $true
}

$loadBalancerExists = kubectl get service codelens-frontend -o jsonpath='{.spec.type}' 2>$null
if ($LASTEXITCODE -eq 0 -and $loadBalancerExists -eq "LoadBalancer") {
    $hasNetworkingResources = $true
}

if ($pausedDeployments -eq $deployments.Count -and -not $hasNetworkingResources) {
    Write-Host "All deployments and networking resources are already paused!" -ForegroundColor Yellow
    Write-Host ""
    foreach ($deployment in $deployments) {
        Write-Host "  $deployment`: 0 replicas" -ForegroundColor White
    }
    Write-Host "  Ingress: Removed" -ForegroundColor White
    Write-Host "  LoadBalancer: Removed" -ForegroundColor White
    Write-Host "  SSL Certificate: Removed" -ForegroundColor White
    Write-Host ""
    Write-Host "Your application is already saving maximum costs." -ForegroundColor Green
    exit 0
}

Write-Host "This will scale your deployments to 0 replicas and remove networking resources." -ForegroundColor Yellow
Write-Host "Benefits:" -ForegroundColor Green
Write-Host "  - Stops all running pods (saves compute costs)" -ForegroundColor White
Write-Host "  - Removes ingress/load balancer (saves networking costs)" -ForegroundColor White
Write-Host "  - Removes SSL certificates (saves certificate costs)" -ForegroundColor White
Write-Host "  - Keeps static IP reserved (minimal cost)" -ForegroundColor White
Write-Host "  - Keeps all configuration backed up for easy restoration" -ForegroundColor White
Write-Host ""
Write-Host "Your application will be completely inaccessible until resumed." -ForegroundColor Red
Write-Host "The domain will not resolve and SSL certificates will be removed." -ForegroundColor Red
Write-Host ""

$confirm = Read-Host "Continue with pause? (y/n)"
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "Pause cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Scaling deployments to 0 replicas..." -ForegroundColor Yellow

foreach ($deployment in $deployments) {
    if ($currentStatus.ContainsKey($deployment)) {
        Write-Host "  Scaling $deployment to 0..." -ForegroundColor Gray
        kubectl scale deployment $deployment --replicas=0
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    $deployment scaled down successfully" -ForegroundColor Green
        } else {
            Write-Host "    Warning: Failed to scale down $deployment" -ForegroundColor Yellow
        }
    } else {
        Write-Host "    $deployment not found, skipping" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Waiting for pods to terminate..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

$remainingPods = kubectl get pods -l app=codelens --no-headers 2>$null
if ($remainingPods) {
    Write-Host "Some pods are still terminating:" -ForegroundColor Yellow
    Write-Host $remainingPods -ForegroundColor Gray
    Write-Host "This is normal and they should terminate shortly." -ForegroundColor White
} else {
    Write-Host "All pods have been terminated." -ForegroundColor Green
}

Write-Host ""
Write-Host "Removing networking resources to save costs..." -ForegroundColor Yellow

# Store original ingress configuration before deleting
Write-Host "  Backing up ingress configuration..." -ForegroundColor Gray
$ingressExists = kubectl get ingress codelens-ingress -o yaml 2>$null
if ($LASTEXITCODE -eq 0) {
    # Create backup directory if it doesn't exist
    if (-not (Test-Path "k8s/gcp/backups")) {
        New-Item -ItemType Directory -Path "k8s/gcp/backups" -Force | Out-Null
    }
    
    kubectl get ingress codelens-ingress -o yaml > "k8s/gcp/backups/ingress-backup.yaml" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    Ingress configuration backed up" -ForegroundColor Green
    }
}

# Delete ingress (this removes the load balancer and saves networking costs)
Write-Host "  Deleting ingress..." -ForegroundColor Gray
kubectl delete ingress codelens-ingress 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "    Ingress deleted successfully" -ForegroundColor Green
} else {
    Write-Host "    Ingress not found or already deleted" -ForegroundColor Gray
}

# Delete managed certificate (saves SSL certificate costs)
Write-Host "  Deleting managed certificate..." -ForegroundColor Gray
kubectl delete managedcertificate codelens-ssl-cert 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "    Managed certificate deleted successfully" -ForegroundColor Green
} else {
    Write-Host "    Managed certificate not found or already deleted" -ForegroundColor Gray
}

# Change frontend service from LoadBalancer to ClusterIP to remove external IP costs
Write-Host "  Converting frontend service to ClusterIP..." -ForegroundColor Gray
$frontendServiceExists = kubectl get service codelens-frontend 2>$null
if ($LASTEXITCODE -eq 0) {
    # Patch the service to remove LoadBalancer type
    kubectl patch service codelens-frontend -p '{"spec":{"type":"ClusterIP"}}' 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    Frontend service converted to ClusterIP" -ForegroundColor Green
    } else {
        Write-Host "    Warning: Failed to convert frontend service" -ForegroundColor Yellow
    }
} else {
    Write-Host "    Frontend service not found" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Waiting for networking resources to be cleaned up..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

Write-Host ""
Write-Host "Checking final status..." -ForegroundColor Yellow
kubectl get deployments -l app=codelens

Write-Host ""
Write-Host "===============================" -ForegroundColor Green
Write-Host "CodeLens Application PAUSED!" -ForegroundColor Green
Write-Host "===============================" -ForegroundColor Green
Write-Host ""
Write-Host "Cost savings:" -ForegroundColor Cyan
Write-Host "- No compute costs for pods" -ForegroundColor White
Write-Host "- No networking costs (ingress/load balancer removed)" -ForegroundColor White
Write-Host "- No SSL certificate costs" -ForegroundColor White
Write-Host "- Static IP reserved but not in use (minimal cost)" -ForegroundColor White
Write-Host "- All configuration preserved for easy restoration" -ForegroundColor White
Write-Host ""
Write-Host "To resume your application later:" -ForegroundColor Yellow
Write-Host "  .\scripts\resume.ps1" -ForegroundColor White
Write-Host ""
