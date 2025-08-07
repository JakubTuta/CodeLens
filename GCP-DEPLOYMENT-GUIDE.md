# CodeLens GCP Deployment Guide

This guide provides step-by-step instructions to deploy CodeLens to Google Cloud Platform using Google Kubernetes Engine (GKE).

## Prerequisites

Before starting the deployment, ensure you have the following:

### Required Tools
1. **Google Cloud SDK (gcloud)** - [Install guide](https://cloud.google.com/sdk/docs/install)
2. **kubectl** - Kubernetes command-line tool (installed with gcloud)
3. **Docker Desktop** - For building images locally
4. **PowerShell** - For running deployment scripts (Windows)

### Google Cloud Account Setup
1. **Google Cloud Account** with billing enabled
2. **Project created** in Google Cloud Console
3. **Required APIs enabled** (see API setup section below)

## Step 1: Google Cloud Project Setup

### 1.1 Create or Select a Project
```bash
# Create a new project (optional)
gcloud projects create codelens-467015 --name="CodeLens"

# Set the project as default
gcloud config set project codelens-467015
```

### 1.2 Enable Required APIs
```bash
# Enable required Google Cloud APIs
gcloud services enable container.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable dns.googleapis.com
gcloud services enable certificatemanager.googleapis.com
```

### 1.3 Create Artifact Registry Repository
```bash
# Create Docker repository in Artifact Registry
gcloud artifacts repositories create codelens-repo \
    --repository-format=docker \
    --location=europe-central2 \
    --description="CodeLens application images"
```

## Step 2: GKE Cluster Setup

### 2.1 Create GKE Cluster
```bash
# Create a GKE cluster with autopilot (recommended for simplicity)
gcloud container clusters create-auto codelens-cluster \
    --region=europe-central2 \
    --project=codelens-467015

# Or create a standard cluster with more control
gcloud container clusters create codelens-cluster \
    --zone=europe-central2-a \
    --num-nodes=3 \
    --machine-type=e2-medium \
    --enable-autorepair \
    --enable-autoupgrade \
    --enable-autoscaling \
    --min-nodes=1 \
    --max-nodes=10
```

### 2.2 Get Cluster Credentials
```bash
# Configure kubectl to use the new cluster
gcloud container clusters get-credentials codelens-cluster \
    --region=europe-central2 \
    --project=codelens-467015
```

## Step 3: IAM and Service Account Setup

### 3.1 Create Service Account for Test Runner
```bash
# Create a service account for the test runner component
gcloud iam service-accounts create codelens-test-runner \
    --display-name="CodeLens Test Runner" \
    --description="Service account for CodeLens test runner component"

# Grant necessary permissions
gcloud projects add-iam-policy-binding codelens-467015 \
    --member="serviceAccount:codelens-test-runner@codelens-467015.iam.gserviceaccount.com" \
    --role="roles/container.developer"

# Enable Workload Identity (if using GKE Autopilot or standard cluster with Workload Identity)
gcloud iam service-accounts add-iam-policy-binding \
    codelens-test-runner@codelens-467015.iam.gserviceaccount.com \
    --role="roles/iam.workloadIdentityUser" \
    --member="serviceAccount:codelens-467015.svc.id.goog[default/test-runner-sa]"
```

## Step 4: Network and DNS Setup (Optional but Recommended)

### 4.1 Reserve Static IP Address
```bash
# Reserve a global static IP for the ingress
gcloud compute addresses create codelens-ip --global
```

### 4.2 Configure DNS (if using custom domain)
1. Purchase or use an existing domain
2. Point your domain's DNS records to the reserved IP:
   - Create an A record for `codelens.online` → Static IP
   - Create an A record for `api.codelens.online` → Static IP

### 4.3 Update Configuration Files
If using a custom domain, update the following files:
- `k8s/gcp/frontend.yaml` - Update environment variables
- `k8s/gcp/backend.yaml` - Update CORS origins
- `k8s/gcp/ingress.yaml` - Update domain names

## Step 5: Deploy the Application

### 5.1 Authentication Setup
```powershell
# Authenticate with Google Cloud
gcloud auth login

# Configure Docker to use Artifact Registry
gcloud auth configure-docker europe-central2-docker.pkg.dev
```

### 5.2 Run Deployment Script
```powershell
# Navigate to the project directory
cd "d:\Projekty\web\CodeLens"

# Run the deployment script
.\scripts\deploy.ps1
```

The deployment script will:
1. Authenticate with Google Cloud
2. Get GKE cluster credentials
3. Build Docker images locally
4. Tag images for Artifact Registry
5. Push images to Artifact Registry
6. Deploy all Kubernetes manifests
7. Wait for deployments to be ready
8. Display service information

## Step 6: Verify Deployment

### 6.1 Check Pod Status
```bash
# Check if all pods are running
kubectl get pods -l app=codelens

# Check detailed pod information
kubectl describe pods -l app=codelens
```

### 6.2 Check Services
```bash
# Check service status
kubectl get services

# Get LoadBalancer external IPs
kubectl get services -o wide
```

### 6.3 Check Ingress (if using custom domain)
```bash
# Check ingress status
kubectl get ingress codelens-ingress

# Check managed certificate status
kubectl get managedcertificate codelens-ssl-cert
```

## Step 7: Access the Application

### 7.1 Using LoadBalancer IPs (immediate access)
1. Get the external IPs from the services:
   ```bash
   kubectl get service codelens-frontend
   kubectl get service codelens-backend-external
   ```
2. Access the frontend using the frontend service external IP
3. The application will communicate with the backend using its external IP

### 7.2 Using Custom Domain (after DNS propagation)
1. Wait for DNS propagation (can take up to 48 hours)
2. Wait for SSL certificate provisioning (10-60 minutes)
3. Access your application at:
   - Frontend: `https://codelens.online`
   - Backend API: `https://api.codelens.online`

## Step 8: Monitoring and Troubleshooting

### 8.1 View Application Logs
```bash
# Backend logs
kubectl logs -f deployment/codelens-backend

# Frontend logs
kubectl logs -f deployment/codelens-frontend

# Test runner logs
kubectl logs -f deployment/codelens-test-runner
```

### 8.2 Scale the Application
```bash
# Scale frontend
kubectl scale deployment codelens-frontend --replicas=3

# Scale backend
kubectl scale deployment codelens-backend --replicas=3
```

### 8.3 Update the Application
```bash
# After making code changes, rebuild and redeploy
.\scripts\deploy.ps1
```

## Step 9: Cost Optimization

### 9.1 Cluster Management
- Use GKE Autopilot for automatic resource optimization
- Enable cluster autoscaling
- Use preemptible nodes for non-production workloads

### 9.2 Resource Limits
The deployment configurations include resource requests and limits:
- Backend: 256Mi-512Mi memory, 250m-500m CPU
- Frontend: 128Mi-256Mi memory, 100m-200m CPU
- Test Runner: 256Mi-512Mi memory, 250m-500m CPU

### 9.3 Monitoring Costs
```bash
# Monitor cluster costs
gcloud billing budgets list

# Check resource usage
kubectl top nodes
kubectl top pods
```

## Security Considerations

1. **Network Policies**: Consider implementing Kubernetes Network Policies
2. **Pod Security**: Use Pod Security Standards
3. **Secrets Management**: Use Google Secret Manager for sensitive data
4. **RBAC**: Review and minimize permissions
5. **Image Security**: Scan images for vulnerabilities

## Backup and Disaster Recovery

1. **Persistent Volume Backups**: If using persistent storage
2. **Configuration Backups**: Keep Kubernetes manifests in version control
3. **Database Backups**: If using a database, implement regular backups
4. **Multi-region Deployment**: Consider deploying across multiple regions

## Support and Maintenance

### Regular Maintenance Tasks
1. **GKE Cluster Updates**: Keep cluster and node pools updated
2. **Image Updates**: Regularly update base images
3. **Dependency Updates**: Keep application dependencies current
4. **Security Patches**: Apply security updates promptly

### Getting Help
- **Google Cloud Support**: For infrastructure issues
- **Kubernetes Documentation**: For Kubernetes-specific questions
- **Application Logs**: For debugging application issues

## Cleanup (when needed)

To remove all resources and stop incurring costs:

```bash
# Delete the application
kubectl delete -f k8s/gcp/

# Delete the cluster
gcloud container clusters delete codelens-cluster --region=europe-central2

# Delete the Artifact Registry repository
gcloud artifacts repositories delete codelens-repo --location=europe-central2

# Release the static IP
gcloud compute addresses delete codelens-ip --global
```

---

This guide provides a complete setup for deploying CodeLens to Google Cloud Platform. Follow each step carefully and refer to the troubleshooting section if you encounter any issues.
