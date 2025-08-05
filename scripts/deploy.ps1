# Deploy CodeLens to Google Cloud Platform and Kubernetes

Write-Host "Building Docker images..." -ForegroundColor Green

# Build backend image
Write-Host "Building backend image..." -ForegroundColor Yellow
Set-Location backend
docker build -t codelens-backend:latest .
Set-Location ..

# Build frontend image  
Write-Host "Building frontend image..." -ForegroundColor Yellow
Set-Location frontend
docker build -t codelens-frontend:latest .
Set-Location ..

# Build test runner image
Write-Host "Building test runner image..." -ForegroundColor Yellow
Set-Location test-runner
docker build -t codelens-test-runner:latest .
Set-Location ..

Write-Host "Tagging images for Google Cloud Platform..." -ForegroundColor Green

# Tag images for GCP Artifact Registry
docker tag codelens-frontend:latest europe-central2-docker.pkg.dev/codelens-467015/codelens-repo/codelens-frontend:latest
docker tag codelens-backend:latest europe-central2-docker.pkg.dev/codelens-467015/codelens-repo/codelens-backend:latest
docker tag codelens-test-runner:latest europe-central2-docker.pkg.dev/codelens-467015/codelens-repo/codelens-test-runner:latest

Write-Host "Pushing images to Google Cloud Platform..." -ForegroundColor Green

# Push images to GCP Artifact Registry
Write-Host "Pushing frontend image..." -ForegroundColor Yellow
docker push europe-central2-docker.pkg.dev/codelens-467015/codelens-repo/codelens-frontend:latest

Write-Host "Pushing backend image..." -ForegroundColor Yellow
docker push europe-central2-docker.pkg.dev/codelens-467015/codelens-repo/codelens-backend:latest

Write-Host "Pushing test runner image..." -ForegroundColor Yellow
docker push europe-central2-docker.pkg.dev/codelens-467015/codelens-repo/codelens-test-runner:latest

Write-Host "Applying Kubernetes manifests..." -ForegroundColor Green

# Apply RBAC first
kubectl apply -f k8s/rbac.yaml

# Apply backend
kubectl apply -f k8s/backend.yaml

# Apply frontend 
kubectl apply -f k8s/frontend.yaml

# Apply test runner
kubectl apply -f k8s/test-runner.yaml

Write-Host "Waiting for deployments to be ready..." -ForegroundColor Green
kubectl wait --for=condition=available --timeout=300s deployment/codelens-backend
kubectl wait --for=condition=available --timeout=300s deployment/codelens-frontend

Write-Host "Getting service URLs..." -ForegroundColor Green
Write-Host "Backend service:" -ForegroundColor Yellow
kubectl get service codelens-backend-external

Write-Host "Frontend service:" -ForegroundColor Yellow  
kubectl get service codelens-frontend

Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host "To check WebSocket connectivity, run:" -ForegroundColor Cyan
Write-Host "kubectl logs -f deployment/codelens-backend" -ForegroundColor White
Write-Host "kubectl logs -f deployment/codelens-frontend" -ForegroundColor White
