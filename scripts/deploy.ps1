# CodeLens - GCP Deployment Script
# Deploys CodeLens to Google Cloud Platform

Write-Host "CodeLens - GCP Deployment" -ForegroundColor Blue
Write-Host "============================" -ForegroundColor Blue
Write-Host ""

# Ensure we're using the correct kubectl context for GCP deployment
Write-Host "Setting kubectl context for GCP deployment..." -ForegroundColor Yellow
$currentContext = kubectl config current-context 2>$null
if ($currentContext) {
    Write-Host "Current context: $currentContext" -ForegroundColor Gray
    
    # Check if we're already using a GKE context
    if ($currentContext -match "gke_") {
        Write-Host "[OK] Already using GKE context" -ForegroundColor Green
    } else {
        Write-Host "Switching from local context to GKE context..." -ForegroundColor Yellow
        # We'll set the GKE context later when we get the cluster credentials
    }
} else {
    Write-Host "No current kubectl context found" -ForegroundColor Yellow
}
Write-Host ""

# Check if configuration files already exist
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

if ($existingFiles.Count -eq $configFiles.Count) {
    Write-Host "[OK] Found existing configuration files:" -ForegroundColor Green
    foreach ($file in $existingFiles) {
        Write-Host "  - $file" -ForegroundColor White
    }
    Write-Host ""
    
    $useExisting = Read-Host "Use existing configuration files? (y/n)"
    if ($useExisting -eq "y" -or $useExisting -eq "Y") {
        Write-Host "Using existing configuration files..." -ForegroundColor Green
        $skipConfiguration = $true
    } else {
        Write-Host "Will regenerate configuration files from templates..." -ForegroundColor Yellow
        $skipConfiguration = $false
    }
} elseif ($existingFiles.Count -gt 0) {
    Write-Host "[WARNING] Found partial configuration:" -ForegroundColor Yellow
    foreach ($file in $existingFiles) {
        Write-Host "  [OK] $file" -ForegroundColor Green
    }
    foreach ($file in $configFiles) {
        if ($file -notin $existingFiles) {
            Write-Host "  [MISSING] $file (missing)" -ForegroundColor Red
        }
    }
    Write-Host ""
    Write-Host "Will regenerate all configuration files from templates..." -ForegroundColor Yellow
    $skipConfiguration = $false
} else {
    Write-Host "No existing configuration files found." -ForegroundColor Yellow
    Write-Host "Will generate configuration files from templates..." -ForegroundColor Yellow
    $skipConfiguration = $false
}

Write-Host ""

# Only get configuration from user if we need to generate files
if (-not $skipConfiguration) {
    # Get configuration from user
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
        Write-Host "[ERROR] Domain is required" -ForegroundColor Red
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

    $confirm = Read-Host "Continue with deployment? (y/n)"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Write-Host "Deployment cancelled." -ForegroundColor Yellow
        exit 0
    }
} else {
    Write-Host "Skipping configuration prompts (using existing files)..." -ForegroundColor Green
    
    # Extract configuration from existing files for display and Docker operations
    try {
        $backendContent = Get-Content "k8s/gcp/backend.yaml" -Raw
        $PROJECT_ID = ($backendContent | Select-String "image: ([^/]+)-docker\.pkg\.dev/([^/]+)/").Matches[0].Groups[2].Value
        $REGION = ($backendContent | Select-String "image: ([^/]+)-docker\.pkg\.dev/").Matches[0].Groups[1].Value
        $REGISTRY = "$REGION-docker.pkg.dev/$PROJECT_ID/codelens-repo"
        
        $ingressContent = Get-Content "k8s/gcp/ingress.yaml" -Raw
        # Extract the first host that doesn't start with 'www.' or 'api.'
        $hostMatches = $ingressContent | Select-String "host: ([^\s]+)" -AllMatches
        $DOMAIN = ($hostMatches.Matches | Where-Object { $_.Groups[1].Value -notmatch '^(www\.|api\.)' } | Select-Object -First 1).Groups[1].Value
        
        # Validate extracted domain
        if ([string]::IsNullOrWhiteSpace($DOMAIN) -or $DOMAIN -match '\s') {
            throw "Invalid domain extracted: '$DOMAIN'"
        }
        
        $CLUSTER_NAME = "codelens-cluster"  # Default, as it's not stored in YAML files
        
        Write-Host "Extracted configuration from existing files:" -ForegroundColor Cyan
        Write-Host "  Project ID: $PROJECT_ID" -ForegroundColor White
        Write-Host "  Region: $REGION" -ForegroundColor White
        Write-Host "  Domain: $DOMAIN" -ForegroundColor White
        Write-Host "  Registry: $REGISTRY" -ForegroundColor White
        Write-Host "  Cluster: $CLUSTER_NAME (assumed)" -ForegroundColor Gray
    } catch {
        Write-Host "[WARNING] Could not extract all configuration from existing files." -ForegroundColor Yellow
        Write-Host "  Using defaults where possible..." -ForegroundColor Yellow
        $PROJECT_ID = "unknown"
        $REGION = "europe-central2"
        $DOMAIN = "unknown.com"
        $CLUSTER_NAME = "codelens-cluster"
        $REGISTRY = "$REGION-docker.pkg.dev/$PROJECT_ID/codelens-repo"
    }
}

Write-Host ""
Write-Host "Authenticating with Google Cloud..." -ForegroundColor Green
gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet

Write-Host "Getting GKE cluster credentials..." -ForegroundColor Green
gcloud container clusters get-credentials $CLUSTER_NAME --region $REGION --project $PROJECT_ID

Write-Host ""
Write-Host "Building Docker images..." -ForegroundColor Green

# Build images
Write-Host "Building backend..." -ForegroundColor Yellow
docker build -t codelens-backend:latest ./backend
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Backend build failed" -ForegroundColor Red
    exit 1
}

Write-Host "Building frontend..." -ForegroundColor Yellow
docker build -t codelens-frontend:latest ./frontend
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Frontend build failed" -ForegroundColor Red
    exit 1
}

Write-Host "Building test runner..." -ForegroundColor Yellow
docker build -t codelens-test-runner:kubernetes ./test-runner
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Test runner build failed" -ForegroundColor Red
    exit 1
}

Write-Host "Building Kubernetes test executor..." -ForegroundColor Yellow
docker build -f ./test-runner/test-executor.Dockerfile -t codelens-k8s-test-executor:latest ./test-runner
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Kubernetes test executor build failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Tagging and pushing images..." -ForegroundColor Green

# Tag and push images
$images = @(
    @{Local="codelens-frontend:latest"; Remote="$REGISTRY/codelens-frontend:latest"},
    @{Local="codelens-backend:latest"; Remote="$REGISTRY/codelens-backend:latest"},
    @{Local="codelens-test-runner:kubernetes"; Remote="$REGISTRY/codelens-test-runner:kubernetes"},
    @{Local="codelens-k8s-test-executor:latest"; Remote="$REGISTRY/codelens-k8s-test-executor:latest"}
)

foreach ($image in $images) {
    Write-Host "Processing $($image.Local)..." -ForegroundColor Yellow
    docker tag $image.Local $image.Remote
    docker push $image.Remote
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to push $($image.Remote)" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Deploying to Kubernetes..." -ForegroundColor Green

# Only process templates if we don't have existing configuration files
if (-not $skipConfiguration) {
    # Function to process template files
    function Process-Template {
        param($templatePath, $outputPath, $replacements)
        
        Write-Host "  Processing: $templatePath → $outputPath" -ForegroundColor Green
        $content = Get-Content $templatePath -Raw
        foreach ($replacement in $replacements.GetEnumerator()) {
            $content = $content -replace [regex]::Escape("{{$($replacement.Key)}}"), $replacement.Value
        }
        $content | Out-File -FilePath $outputPath -Encoding UTF8
    }

    # Prepare template replacements
    $replacements = @{
        "PROJECT_ID" = $PROJECT_ID
        "REGISTRY" = $REGISTRY
        "DOMAIN" = $DOMAIN
    }

    Write-Host "Processing configuration templates..." -ForegroundColor Yellow

    # Process template files
    Process-Template -templatePath "k8s/gcp/rbac.template.yaml" -outputPath "k8s/gcp/rbac.yaml" -replacements $replacements
    Process-Template -templatePath "k8s/gcp/backend.template.yaml" -outputPath "k8s/gcp/backend.yaml" -replacements $replacements
    Process-Template -templatePath "k8s/gcp/frontend.template.yaml" -outputPath "k8s/gcp/frontend.yaml" -replacements $replacements
    Process-Template -templatePath "k8s/gcp/test-runner.template.yaml" -outputPath "k8s/gcp/test-runner.yaml" -replacements $replacements
    Process-Template -templatePath "k8s/gcp/ingress.template.yaml" -outputPath "k8s/gcp/ingress.yaml" -replacements $replacements
} else {
    Write-Host "Skipping template processing (using existing configuration files)..." -ForegroundColor Green
}

# Deploy to Kubernetes
kubectl apply -f k8s/gcp/rbac.yaml
kubectl apply -f k8s/gcp/backend.yaml
kubectl apply -f k8s/gcp/frontend.yaml
kubectl apply -f k8s/gcp/test-runner.yaml
kubectl apply -f k8s/gcp/ingress.yaml

Write-Host ""
Write-Host "Waiting for deployments..." -ForegroundColor Yellow
kubectl wait --for=condition=available --timeout=300s deployment/codelens-backend 2>$null
kubectl wait --for=condition=available --timeout=300s deployment/codelens-frontend 2>$null

Write-Host ""
Write-Host "[SUCCESS] Deployment completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Getting service information..." -ForegroundColor Cyan

Write-Host ""
Write-Host "LoadBalancer Services:" -ForegroundColor Yellow
kubectl get service codelens-frontend -o wide 2>$null
kubectl get service codelens-backend-external -o wide 2>$null

Write-Host ""
Write-Host "Ingress Information:" -ForegroundColor Yellow
$ingressIP = kubectl get ingress codelens-ingress -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>$null
if ($ingressIP) {
    Write-Host "Ingress IP: $ingressIP" -ForegroundColor Green
} else {
    Write-Host "Ingress IP: Still provisioning..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "DNS CONFIGURATION REQUIRED:" -ForegroundColor Cyan
Write-Host "===============================" -ForegroundColor Cyan
if ($ingressIP) {
    Write-Host "Configure these A records in your domain DNS settings:" -ForegroundColor White
    Write-Host ""
    Write-Host "Record Type: A" -ForegroundColor Yellow
    Write-Host "Name: @           Points to: $ingressIP   (for $DOMAIN)" -ForegroundColor White
    Write-Host "Name: www         Points to: $ingressIP   (for www.$DOMAIN)" -ForegroundColor White
    Write-Host "Name: api         Points to: $ingressIP   (for api.$DOMAIN)" -ForegroundColor White
    Write-Host ""
    Write-Host "IMPORTANT: Use the INGRESS IP ($ingressIP), NOT the service IPs above!" -ForegroundColor Red
} else {
    Write-Host "Waiting for ingress IP to be assigned..." -ForegroundColor Yellow
    Write-Host "   Run 'kubectl get ingress' in a few minutes to get the IP address" -ForegroundColor White
}

Write-Host ""
Write-Host "Important next steps:" -ForegroundColor Cyan
Write-Host "1. Configure DNS A records to point to the INGRESS IP (shown above)" -ForegroundColor White
Write-Host "2. Wait for SSL certificates to be provisioned (10-60 minutes)" -ForegroundColor White
Write-Host "3. Monitor with: kubectl get pods -l app=codelens" -ForegroundColor White
Write-Host "4. Check certificate status: kubectl get managedcertificate" -ForegroundColor White
Write-Host ""
Write-Host "Once DNS propagates, your app will be available at:" -ForegroundColor Green
Write-Host "  https://$DOMAIN" -ForegroundColor White
Write-Host "  https://www.$DOMAIN" -ForegroundColor White
Write-Host "  Backend API: https://api.$DOMAIN" -ForegroundColor White
Write-Host ""
