# Kubernetes Configuration Structure

This document explains the organization of Kubernetes configuration files in the CodeLens project.

## Directory Structure

```
k8s/
├── local/          # Local development configurations
│   ├── backend.yaml
│   ├── frontend.yaml
│   ├── rbac.yaml
│   └── test-runner.yaml
└── gcp/            # Google Cloud Platform configurations
    ├── backend.yaml
    ├── frontend.yaml
    ├── rbac.yaml
    ├── test-runner.yaml
    └── ingress.yaml
```

## Configuration Types

### Local Development (`k8s/local/`)
- **Purpose**: Docker Desktop Kubernetes or local clusters
- **Image Policy**: `Never` (uses locally built images)
- **Networking**: ClusterIP and LoadBalancer for external access
- **Resources**: No resource limits (suitable for development)
- **Replicas**: Single replica per service

### Google Cloud Platform (`k8s/gcp/`)
- **Purpose**: Production deployment on GKE
- **Image Policy**: `Always` (pulls from Artifact Registry)
- **Networking**: LoadBalancer with Ingress for SSL termination
- **Resources**: Defined limits and requests for production
- **Replicas**: Multiple replicas for high availability

## Usage

### Local Development
```bash
# Start local development environment
kubectl apply -f k8s/local/

# Stop local development environment
kubectl delete -f k8s/local/
```

### GCP Production
```bash
# Deploy to GCP (use deploy script instead)
kubectl apply -f k8s/gcp/

# Clean up GCP deployment
kubectl delete -f k8s/gcp/
```

## Scripts Reference

### Local Development Scripts
- `scripts/build.ps1` - Build Docker images locally
- `scripts/local.ps1` - Manage local Kubernetes deployment

### GCP Deployment Scripts
- `scripts/deploy.ps1` - Deploy to GCP (interactive setup)

## Key Differences

| Feature | Local (`k8s/local/`) | GCP (`k8s/gcp/`) |
|---------|---------------------|------------------|
| **Images** | `codelens-*:latest` | `europe-central2-docker.pkg.dev/...` |
| **Pull Policy** | `Never` | `Always` |
| **Replicas** | 1 | 2+ |
| **Resources** | No limits | CPU/Memory limits |
| **SSL/TLS** | No | Google Managed SSL |
| **Ingress** | No | Yes (with SSL) |
| **Workload Identity** | No | Yes |

## Environment Variables

### Local Development
- Backend CORS: `http://codelens-frontend:3000,http://localhost:3000`
- Frontend API URL: `http://codelens-backend:8000`
- WebSocket URL: `ws://codelens-backend:8000`
- Test Runner URL: `ws://codelens-test-runner:8001/ws`

### GCP Production
- Backend CORS: `https://codelens.online,http://localhost:3000`
- Frontend API URL: `https://api.codelens.online`
- WebSocket URL: `wss://api.codelens.online`
- Test Runner URL: `ws://codelens-test-runner:8001/ws`

### Backend Environment Variables
- **TEST_RUNNER_URL**: WebSocket URL for the test runner service
  - Local: `ws://codelens-test-runner:8001/ws` (internal service name)
  - Production: `ws://codelens-test-runner:8001/ws` (internal service name)
  - External/Development: `ws://localhost:8001/ws` (when backend runs outside K8s)
- **WEBSOCKET_PING_INTERVAL**: WebSocket ping interval (GCP only)
- **WEBSOCKET_TIMEOUT**: WebSocket timeout (GCP only)

## Migration Notes

If you're updating from the old flat structure:
1. Local configs moved from `k8s/*.yaml` to `k8s/local/*.yaml`
2. All scripts updated to use new paths
3. GCP configs remain in `k8s/gcp/`
4. No changes needed to Docker images or source code
