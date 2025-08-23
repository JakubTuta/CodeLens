# CodeLens - GCP Removal Script
# Removes CodeLens from Google Cloud Platform

Write-Host "CodeLens - GCP Removal" -ForegroundColor Red
Write-Host "======================" -ForegroundColor Red
Write-Host ""

Write-Host "WARNING: This script will permanently remove your CodeLens application from GCP!" -ForegroundColor Yellow
Write-Host "This includes:" -ForegroundColor Yellow
Write-Host "  - All Kubernetes resources (deployments, services, ingress, etc.)" -ForegroundColor White
Write-Host "  - SSL certificates and managed certificates" -ForegroundColor White
Write-Host "  - Load balancers and backend configurations" -ForegroundColor White
Write-Host "  - Optionally: Docker images from Container Registry" -ForegroundColor White
Write-Host ""

$confirmRemoval = Read-Host "Are you sure you want to proceed with removal? (type 'YES' to confirm)"
if ($confirmRemoval -ne "YES") {
    Write-Host "Removal cancelled. No changes have been made." -ForegroundColor Green
    exit 0
}

Write-Host ""

# Check if configuration files exist to extract values
$configFiles = @(
    "k8s/gcp/backend.yaml",
    "k8s/gcp/frontend.yaml",
    "k8s/gcp/test-runner.yaml",
    "k8s/gcp/rbac.yaml",
    "k8s/gcp/ingress.yaml"
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
$DOMAIN = ""
$REGISTRY = ""

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
                    $REGISTRY = "$REGION-docker.pkg.dev/$PROJECT_ID/codelens-repo"
                }
            }
            
            if (Test-Path "k8s/gcp/ingress.yaml") {
                $ingressContent = Get-Content "k8s/gcp/ingress.yaml" -Raw
                # Extract the first host that doesn't start with 'www.' or 'api.'
                $hostMatches = $ingressContent | Select-String "host: ([^\s]+)" -AllMatches
                $DOMAIN = ($hostMatches.Matches | Where-Object { $_.Groups[1].Value -notmatch '^(www\.|api\.)' } | Select-Object -First 1).Groups[1].Value
            }
            
            # Default cluster name since it's not stored in YAML files
            $CLUSTER_NAME = "codelens-cluster"
            
            Write-Host "Extracted configuration:" -ForegroundColor Cyan
            Write-Host "  Project ID: $PROJECT_ID" -ForegroundColor White
            Write-Host "  Region: $REGION" -ForegroundColor White
            Write-Host "  Domain: $DOMAIN" -ForegroundColor White
            Write-Host "  Registry: $REGISTRY" -ForegroundColor White
            Write-Host "  Cluster: $CLUSTER_NAME (default assumption)" -ForegroundColor Gray
            Write-Host ""
            
            if ([string]::IsNullOrWhiteSpace($PROJECT_ID) -or [string]::IsNullOrWhiteSpace($DOMAIN)) {
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

    $DOMAIN = Read-Host "Enter your domain (e.g., codelens.online)"
    if ([string]::IsNullOrWhiteSpace($DOMAIN)) {
        Write-Host "[ERROR] Domain is required for complete cleanup" -ForegroundColor Red
        exit 1
    }

    $REGISTRY = "$REGION-docker.pkg.dev/$PROJECT_ID/codelens-repo"

    Write-Host ""
    Write-Host "Configuration:" -ForegroundColor Yellow
    Write-Host "  Project ID: $PROJECT_ID" -ForegroundColor White
    Write-Host "  Cluster: $CLUSTER_NAME" -ForegroundColor White
    Write-Host "  Region: $REGION" -ForegroundColor White
    Write-Host "  Domain: $DOMAIN" -ForegroundColor White
    Write-Host "  Registry: $REGISTRY" -ForegroundColor White
    Write-Host ""
}

# Final confirmation with specific details
Write-Host "FINAL CONFIRMATION:" -ForegroundColor Red
Write-Host "===================" -ForegroundColor Red
Write-Host "You are about to remove CodeLens from:" -ForegroundColor Yellow
Write-Host "  GCP Project: $PROJECT_ID" -ForegroundColor White
Write-Host "  GKE Cluster: $CLUSTER_NAME" -ForegroundColor White
Write-Host "  Region: $REGION" -ForegroundColor White
Write-Host "  Domain: $DOMAIN" -ForegroundColor White
Write-Host ""

$finalConfirm = Read-Host "Type 'REMOVE' to proceed with the removal"
if ($finalConfirm -ne "REMOVE") {
    Write-Host "Removal cancelled. No changes have been made." -ForegroundColor Green
    exit 0
}

Write-Host ""
Write-Host "Starting removal process..." -ForegroundColor Red
Write-Host ""

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
Write-Host "Authenticating with Google Cloud..." -ForegroundColor Yellow
gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet

Write-Host "Getting GKE cluster credentials..." -ForegroundColor Yellow
gcloud container clusters get-credentials $CLUSTER_NAME --region $REGION --project $PROJECT_ID
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to get cluster credentials." -ForegroundColor Red
    Write-Host "  Please check that the cluster exists and you have access." -ForegroundColor Yellow
    exit 1
}

Write-Host "Verifying cluster connection..." -ForegroundColor Yellow
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
Write-Host "Checking for existing CodeLens resources..." -ForegroundColor Yellow

# Check what resources exist
$existingResources = @()

# Check for deployments
$deployments = kubectl get deployments -l app=codelens --no-headers 2>$null
if ($deployments) {
    $existingResources += "Deployments: $(($deployments -split "`n").Count) found"
    Write-Host "[FOUND] CodeLens deployments" -ForegroundColor Yellow
} else {
    Write-Host "[OK] No CodeLens deployments found" -ForegroundColor Gray
}

# Check for services
$services = kubectl get services -l app=codelens --no-headers 2>$null
if ($services) {
    $existingResources += "Services: $(($services -split "`n").Count) found"
    Write-Host "[FOUND] CodeLens services" -ForegroundColor Yellow
} else {
    Write-Host "[OK] No CodeLens services found" -ForegroundColor Gray
}

# Check for ingress
$ingress = kubectl get ingress codelens-ingress --no-headers 2>$null
if ($ingress) {
    $existingResources += "Ingress: codelens-ingress found"
    Write-Host "[FOUND] CodeLens ingress" -ForegroundColor Yellow
} else {
    Write-Host "[OK] No CodeLens ingress found" -ForegroundColor Gray
}

# Check for managed certificates
$managedCerts = kubectl get managedcertificate codelens-ssl-cert --no-headers 2>$null
if ($managedCerts) {
    $existingResources += "Managed Certificate: codelens-ssl-cert found"
    Write-Host "[FOUND] CodeLens managed certificate" -ForegroundColor Yellow
} else {
    Write-Host "[OK] No CodeLens managed certificate found" -ForegroundColor Gray
}

# Check for backend config
$backendConfig = kubectl get backendconfig websocket-backend-config --no-headers 2>$null
if ($backendConfig) {
    $existingResources += "Backend Config: websocket-backend-config found"
    Write-Host "[FOUND] CodeLens backend config" -ForegroundColor Yellow
} else {
    Write-Host "[OK] No CodeLens backend config found" -ForegroundColor Gray
}

# Check for RBAC resources
$serviceAccount = kubectl get serviceaccount test-runner-sa --no-headers 2>$null
$role = kubectl get role test-runner-role --no-headers 2>$null
$roleBinding = kubectl get rolebinding test-runner-rolebinding --no-headers 2>$null

if ($serviceAccount -or $role -or $roleBinding) {
    $existingResources += "RBAC resources found"
    Write-Host "[FOUND] CodeLens RBAC resources" -ForegroundColor Yellow
} else {
    Write-Host "[OK] No CodeLens RBAC resources found" -ForegroundColor Gray
}

Write-Host ""

if ($existingResources.Count -eq 0) {
    Write-Host "No CodeLens resources found in the cluster." -ForegroundColor Green
    Write-Host "The application appears to already be removed." -ForegroundColor Green
    Write-Host ""
    
    $cleanupImages = Read-Host "Do you want to clean up Docker images from Container Registry? (y/n)"
    if ($cleanupImages -eq "y" -or $cleanupImages -eq "Y") {
        Write-Host ""
        Write-Host "Cleaning up Container Registry images..." -ForegroundColor Yellow
        
        $images = @("codelens-frontend", "codelens-backend", "codelens-test-runner")
        foreach ($image in $images) {
            Write-Host "Removing $REGISTRY/$image..." -ForegroundColor Gray
            gcloud container images delete "$REGISTRY/$image:latest" --quiet --project=$PROJECT_ID 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  $image removed successfully" -ForegroundColor Green
            } else {
                Write-Host "  $image not found or already removed" -ForegroundColor Gray
            }
        }
    }
    
    Write-Host ""
    Write-Host "Cleanup completed!" -ForegroundColor Green
    exit 0
}

Write-Host "Found CodeLens resources to remove:" -ForegroundColor Yellow
foreach ($resource in $existingResources) {
    Write-Host "  - $resource" -ForegroundColor White
}
Write-Host ""

# Ask about configuration files
$removeConfigFiles = $false
if ($existingFiles.Count -gt 0) {
    Write-Host "Local configuration files were found:" -ForegroundColor Cyan
    foreach ($file in $existingFiles) {
        Write-Host "  - $file" -ForegroundColor White
    }
    Write-Host ""
    $removeLocalFiles = Read-Host "Remove local configuration files after successful removal? (y/n)"
    if ($removeLocalFiles -eq "y" -or $removeLocalFiles -eq "Y") {
        $removeConfigFiles = $true
    }
}

# Ask about Docker images
Write-Host ""
$cleanupImages = Read-Host "Remove Docker images from Container Registry after Kubernetes cleanup? (y/n)"

Write-Host ""
Write-Host "Starting Kubernetes resource removal..." -ForegroundColor Red

# Remove resources in the correct order (reverse of deployment)
# 1. Remove ingress first (to stop traffic)
Write-Host ""
Write-Host "Step 1: Removing ingress and certificates..." -ForegroundColor Yellow
if (Test-Path "k8s/gcp/ingress.yaml") {
    Write-Host "  Removing ingress using configuration file..." -ForegroundColor Gray
    kubectl delete -f k8s/gcp/ingress.yaml --ignore-not-found=true --timeout=120s
} else {
    Write-Host "  Removing ingress resources manually..." -ForegroundColor Gray
    kubectl delete ingress codelens-ingress --ignore-not-found=true --timeout=120s
    kubectl delete managedcertificate codelens-ssl-cert --ignore-not-found=true --timeout=120s
    kubectl delete backendconfig websocket-backend-config --ignore-not-found=true --timeout=120s
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "  Ingress and certificates removed successfully" -ForegroundColor Green
} else {
    Write-Host "  Warning: Some ingress resources may not have been removed" -ForegroundColor Yellow
}

# Wait for ingress cleanup
Write-Host "  Waiting for ingress cleanup to complete..." -ForegroundColor Gray
Start-Sleep -Seconds 15

# 2. Remove application deployments
Write-Host ""
Write-Host "Step 2: Removing application deployments..." -ForegroundColor Yellow

$deploymentFiles = @("frontend.yaml", "backend.yaml", "test-runner.yaml")
foreach ($file in $deploymentFiles) {
    $fullPath = "k8s/gcp/$file"
    if (Test-Path $fullPath) {
        Write-Host "  Removing $file..." -ForegroundColor Gray
        kubectl delete -f $fullPath --ignore-not-found=true --timeout=120s
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    $file removed successfully" -ForegroundColor Green
        } else {
            Write-Host "    Warning: $file may not have been removed completely" -ForegroundColor Yellow
        }
        Start-Sleep -Seconds 5
    }
}

# Manual cleanup if files don't exist
if (-not (Test-Path "k8s/gcp/frontend.yaml")) {
    Write-Host "  Manually removing deployments and services..." -ForegroundColor Gray
    kubectl delete deployment codelens-frontend --ignore-not-found=true --timeout=120s
    kubectl delete deployment codelens-backend --ignore-not-found=true --timeout=120s
    kubectl delete deployment codelens-test-runner --ignore-not-found=true --timeout=120s
    kubectl delete service codelens-frontend --ignore-not-found=true --timeout=60s
    kubectl delete service codelens-backend --ignore-not-found=true --timeout=60s
    kubectl delete service codelens-test-runner --ignore-not-found=true --timeout=60s
}

# 3. Remove RBAC resources
Write-Host ""
Write-Host "Step 3: Removing RBAC resources..." -ForegroundColor Yellow
if (Test-Path "k8s/gcp/rbac.yaml") {
    Write-Host "  Removing RBAC using configuration file..." -ForegroundColor Gray
    kubectl delete -f k8s/gcp/rbac.yaml --ignore-not-found=true --timeout=60s
} else {
    Write-Host "  Removing RBAC resources manually..." -ForegroundColor Gray
    kubectl delete rolebinding test-runner-rolebinding --ignore-not-found=true --timeout=60s
    kubectl delete role test-runner-role --ignore-not-found=true --timeout=60s
    kubectl delete serviceaccount test-runner-sa --ignore-not-found=true --timeout=60s
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "  RBAC resources removed successfully" -ForegroundColor Green
} else {
    Write-Host "  Warning: Some RBAC resources may not have been removed" -ForegroundColor Yellow
}

# 4. Wait for complete cleanup
Write-Host ""
Write-Host "Step 4: Waiting for complete resource cleanup..." -ForegroundColor Yellow
Write-Host "  This may take a few minutes..." -ForegroundColor Gray

$maxWaitTime = 180 # 3 minutes
$waitTime = 0
$cleanupComplete = $false

while ($waitTime -lt $maxWaitTime -and -not $cleanupComplete) {
    Start-Sleep -Seconds 10
    $waitTime += 10
    
    # Check if any CodeLens resources still exist
    $remainingPods = kubectl get pods -l app=codelens --no-headers 2>$null
    $remainingServices = kubectl get services -l app=codelens --no-headers 2>$null
    $remainingDeployments = kubectl get deployments -l app=codelens --no-headers 2>$null
    
    if (-not $remainingPods -and -not $remainingServices -and -not $remainingDeployments) {
        $cleanupComplete = $true
        Write-Host "  All Kubernetes resources have been removed!" -ForegroundColor Green
    } else {
        Write-Host "  Still waiting for cleanup... ($waitTime/$maxWaitTime seconds)" -ForegroundColor Gray
    }
}

if (-not $cleanupComplete) {
    Write-Host "  Warning: Some resources may still be terminating" -ForegroundColor Yellow
    Write-Host "  You can check status with: kubectl get all -l app=codelens" -ForegroundColor Gray
}

# 5. Clean up Docker images if requested
if ($cleanupImages -eq "y" -or $cleanupImages -eq "Y") {
    Write-Host ""
    Write-Host "Step 5: Cleaning up Container Registry images..." -ForegroundColor Yellow
    
    $images = @("codelens-frontend", "codelens-backend", "codelens-test-runner")
    foreach ($image in $images) {
        Write-Host "  Removing $REGISTRY/$image:latest..." -ForegroundColor Gray
        gcloud container images delete "$REGISTRY/$image:latest" --quiet --project=$PROJECT_ID 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    $image removed successfully" -ForegroundColor Green
        } else {
            Write-Host "    $image not found or already removed" -ForegroundColor Gray
        }
    }
    
    Write-Host "  Container Registry cleanup completed" -ForegroundColor Green
}

# 6. Remove local configuration files if requested
if ($removeConfigFiles) {
    Write-Host ""
    Write-Host "Step 6: Removing local configuration files..." -ForegroundColor Yellow
    
    foreach ($file in $existingFiles) {
        if (Test-Path $file) {
            Write-Host "  Removing $file..." -ForegroundColor Gray
            Remove-Item $file -Force
            if (Test-Path $file) {
                Write-Host "    Warning: Could not remove $file" -ForegroundColor Yellow
            } else {
                Write-Host "    $file removed successfully" -ForegroundColor Green
            }
        }
    }
    
    Write-Host "  Local configuration cleanup completed" -ForegroundColor Green
}

# Final verification
Write-Host ""
Write-Host "Final verification..." -ForegroundColor Yellow

$finalCheck = kubectl get all -l app=codelens --no-headers 2>$null
if ($finalCheck) {
    Write-Host ""
    Write-Host "WARNING: Some CodeLens resources may still exist:" -ForegroundColor Yellow
    Write-Host $finalCheck -ForegroundColor Gray
    Write-Host ""
    Write-Host "These resources should terminate automatically in a few minutes." -ForegroundColor Yellow
    Write-Host "If they persist, you can check their status with:" -ForegroundColor Cyan
    Write-Host "  kubectl get all -l app=codelens" -ForegroundColor White
    Write-Host "  kubectl describe <resource-type> <resource-name>" -ForegroundColor White
} else {
    Write-Host "[SUCCESS] No CodeLens resources found - removal completed!" -ForegroundColor Green
}

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "CodeLens Removal Completed!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "Summary of actions performed:" -ForegroundColor Cyan
Write-Host "- Removed Kubernetes ingress and SSL certificates" -ForegroundColor White
Write-Host "- Removed application deployments and services" -ForegroundColor White
Write-Host "- Removed RBAC resources (roles, bindings, service accounts)" -ForegroundColor White

if ($cleanupImages -eq "y" -or $cleanupImages -eq "Y") {
    Write-Host "- Removed Docker images from Container Registry" -ForegroundColor White
}

if ($removeConfigFiles) {
    Write-Host "- Removed local configuration files" -ForegroundColor White
}

Write-Host ""
Write-Host "Important notes:" -ForegroundColor Yellow
Write-Host "1. DNS records for $DOMAIN still point to the old IP" -ForegroundColor White
Write-Host "   You may want to update or remove these DNS records" -ForegroundColor White
Write-Host "2. The GKE cluster itself was not removed" -ForegroundColor White
Write-Host "   If you want to remove the entire cluster, use: gcloud container clusters delete $CLUSTER_NAME --region $REGION" -ForegroundColor Gray
Write-Host "3. Static IP reservations may still exist in GCP Console" -ForegroundColor White
Write-Host "   Check: GCP Console → VPC Network → External IP addresses" -ForegroundColor Gray
Write-Host ""
Write-Host "Your CodeLens application has been successfully removed from GCP!" -ForegroundColor Green
Write-Host ""
