# CodeLens - GCP Deployment Script
# Deploys CodeLens to Google Cloud Platform

Write-Host "CodeLens - GCP Deployment" -ForegroundColor Blue
Write-Host "=========================" -ForegroundColor Blue
Write-Host ""

# Get configuration from user
Write-Host "Please provide your GCP configuration:" -ForegroundColor Cyan
Write-Host ""

$PROJECT_ID = Read-Host "Enter your GCP Project ID"
if ([string]::IsNullOrWhiteSpace($PROJECT_ID)) {
    Write-Host "✗ Project ID is required" -ForegroundColor Red
    Read-Host "Press Enter to exit"
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
    Write-Host "✗ Domain is required" -ForegroundColor Red
    Read-Host "Press Enter to exit"
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
    Write-Host "✗ Backend build failed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Building frontend..." -ForegroundColor Yellow
docker build -t codelens-frontend:latest ./frontend
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Frontend build failed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Building test runner..." -ForegroundColor Yellow
docker build -t codelens-test-runner:latest ./test-runner
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Test runner build failed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Tagging and pushing images..." -ForegroundColor Green

# Tag and push images
$images = @(
    @{Local="codelens-frontend:latest"; Remote="$REGISTRY/codelens-frontend:latest"},
    @{Local="codelens-backend:latest"; Remote="$REGISTRY/codelens-backend:latest"},
    @{Local="codelens-test-runner:latest"; Remote="$REGISTRY/codelens-test-runner:latest"}
)

foreach ($image in $images) {
    Write-Host "Processing $($image.Local)..." -ForegroundColor Yellow
    docker tag $image.Local $image.Remote
    docker push $image.Remote
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Failed to push $($image.Remote)" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host ""
Write-Host "Deploying to Kubernetes..." -ForegroundColor Green

# Function to process template files
function Process-Template {
    param($templatePath, $outputPath, $replacements)
    
    # Check if output file already exists and ask user
    if (Test-Path $outputPath) {
        Write-Host "  Configuration file already exists: $outputPath" -ForegroundColor Yellow
        $overwrite = Read-Host "  Overwrite existing file? (y/n)"
        if ($overwrite -ne "y" -and $overwrite -ne "Y") {
            Write-Host "  Skipping $outputPath" -ForegroundColor Gray
            return
        }
    }
    
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

# Deploy to Kubernetes
kubectl apply -f k8s/gcp/rbac.yaml
kubectl apply -f k8s/gcp/backend.yaml
kubectl apply -f k8s/gcp/frontend.yaml
kubectl apply -f k8s/gcp/test-runner.yaml
kubectl apply -f k8s/gcp/ingress.yaml

Write-Host ""
Write-Host "Waiting for deployments..." -ForegroundColor Yellow
kubectl wait --for=condition=available --timeout=600s deployment/codelens-backend 2>$null
kubectl wait --for=condition=available --timeout=600s deployment/codelens-frontend 2>$null

Write-Host ""
Write-Host "✓ Deployment completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Getting service information..." -ForegroundColor Cyan

Write-Host ""
Write-Host "LoadBalancer Services:" -ForegroundColor Yellow
kubectl get service codelens-frontend -o wide 2>$null
kubectl get service codelens-backend-external -o wide 2>$null

Write-Host ""
Write-Host "Important next steps:" -ForegroundColor Cyan
Write-Host "1. Configure DNS to point your domain to the LoadBalancer IPs above" -ForegroundColor White
Write-Host "2. Wait for SSL certificates to be provisioned (10-60 minutes)" -ForegroundColor White
Write-Host "3. Monitor with: kubectl get pods -l app=codelens" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to continue"
