# CodeLens - GCP Resume Script
# Restores CodeLens deployments from paused state (scales back to 1 replica)

Write-Host "CodeLens - GCP Resume" -ForegroundColor Green
Write-Host "====================" -ForegroundColor Green
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

Write-Host "RESUMING CodeLens Application" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Green
Write-Host ""

# Check if already running
$runningDeployments = 0
foreach ($deployment in $deployments) {
    if ($currentStatus.ContainsKey($deployment) -and $currentStatus[$deployment] -gt 0) {
        $runningDeployments++
    }
}

if ($runningDeployments -eq $deployments.Count) {
    Write-Host "All deployments are already running!" -ForegroundColor Yellow
    Write-Host ""
    foreach ($deployment in $deployments) {
        Write-Host "  $deployment`: $($currentStatus[$deployment]) replicas" -ForegroundColor White
    }
    Write-Host ""
    Write-Host "No action needed." -ForegroundColor Green
    exit 0
}

# Check if deployments exist but are paused
$pausedDeployments = 0
foreach ($deployment in $deployments) {
    if ($currentStatus.ContainsKey($deployment) -and $currentStatus[$deployment] -eq 0) {
        $pausedDeployments++
    }
}

if ($pausedDeployments -eq 0) {
    Write-Host "ERROR: No paused deployments found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Current status:" -ForegroundColor Yellow
    foreach ($deployment in $deployments) {
        if ($currentStatus.ContainsKey($deployment)) {
            Write-Host "  $deployment`: $($currentStatus[$deployment]) replicas" -ForegroundColor White
        } else {
            Write-Host "  $deployment`: Not found" -ForegroundColor Red
        }
    }
    Write-Host ""
    Write-Host "This script is only for resuming paused applications." -ForegroundColor Yellow
    Write-Host "If your app was never deployed, use: .\scripts\deploy.ps1" -ForegroundColor Cyan
    Write-Host "If your app was removed, use: .\scripts\deploy.ps1" -ForegroundColor Cyan
    exit 1
}

Write-Host "Found $pausedDeployments paused deployment(s) to resume." -ForegroundColor Yellow
Write-Host ""
Write-Host "This will scale your deployments back to 1 replica each." -ForegroundColor Yellow
Write-Host "Your application will start consuming resources and incurring costs again." -ForegroundColor Yellow
Write-Host ""

$confirm = Read-Host "Continue with resume? (y/n)"
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "Resume cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Scaling deployments to 1 replica..." -ForegroundColor Yellow

foreach ($deployment in $deployments) {
    if ($currentStatus.ContainsKey($deployment)) {
        Write-Host "  Scaling $deployment to 1..." -ForegroundColor Gray
        kubectl scale deployment $deployment --replicas=1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    $deployment scaled successfully" -ForegroundColor Green
        } else {
            Write-Host "    Warning: Failed to scale $deployment" -ForegroundColor Yellow
        }
    } else {
        Write-Host "    $deployment not found, skipping" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Waiting for pods to be ready..." -ForegroundColor Yellow
kubectl wait --for=condition=available --timeout=300s deployment/codelens-backend 2>$null
kubectl wait --for=condition=available --timeout=300s deployment/codelens-frontend 2>$null
kubectl wait --for=condition=available --timeout=300s deployment/codelens-test-runner 2>$null

Write-Host ""
Write-Host "Checking final status..." -ForegroundColor Yellow
kubectl get deployments -l app=codelens

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "CodeLens Application RESUMED!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your application is now running and accessible." -ForegroundColor White
Write-Host "Note: It may take a few minutes for the ingress to route traffic properly." -ForegroundColor Yellow
Write-Host ""
Write-Host "To pause your application again:" -ForegroundColor Cyan
Write-Host "  .\scripts\pause.ps1" -ForegroundColor White
Write-Host ""
