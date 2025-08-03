# CodeLens - AI-Powered Code Testing Platform

CodeLens is a microservices-based platform that generates and executes Python tests using AI, with secure, isolated test execution in Kubernetes containers.

## 🏗️ Architecture Overview

The system consists of **4 distinct container types** with clear separation of responsibilities:

### Container Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │ Main Backend    │    │ Test Runner     │    │ Dynamic Test    │
│   Container     │    │ Server          │    │ Server          │    │ Containers      │
│                 │    │ Container       │    │ Container       │    │                 │
│ ✅ UI/UX        │◄──►│ ✅ AI Services  │◄──►│ ✅ K8s Jobs     │◄──►│ ✅ Isolated     │
│ ✅ WebSocket    │    │ ✅ Test Gen     │    │ ✅ Execution    │    │ ✅ Secure       │
│ ✅ TypeScript   │    │ ✅ Validation   │    │ ✅ Monitoring   │    │ ✅ Auto-cleanup │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
   Port 3000              Port 8000              Port 8001           Dynamic Ports
```

### 📦 Container Responsibilities

| Container           | Purpose            | Technology Stack                 | Key Features                                  |
| ------------------- | ------------------ | -------------------------------- | --------------------------------------------- |
| **Frontend**        | User Interface     | Nuxt.js 3, TypeScript, Vuetify 3 | Code input, results display, WebSocket client |
| **Backend**         | AI & Orchestration | FastAPI, Python 3.12             | AI integration, test generation, coordination |
| **Test Runner**     | Execution Manager  | FastAPI, Kubernetes client       | Job management, result collection             |
| **Test Containers** | Isolated Execution | Python 3.11-slim                 | Secure test execution, auto-cleanup           |

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Kubernetes cluster (for production) or Docker Desktop with Kubernetes
- AI API key (Gemini or Anthropic Claude)

### 1. Clone and Deploy

```bash
# Clone the repository
git clone https://github.com/JakubTuta/CodeLens.git
cd CodeLens

# Deploy with Docker Compose (Development)
docker-compose up --build

# OR Deploy to Kubernetes (Production)
kubectl apply -f k8s/
```

### 2. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Test Runner**: http://localhost:8001

### 3. Using the Platform

1. Enter your AI API key (Gemini or Claude)
2. Paste Python function code
3. Generate tests, documentation, and improvements
4. View execution results with detailed logs

## 🛠️ Development Setup

### Local Development with Hot Reload

```bash
# Frontend development
cd frontend
bun install
bun run dev

# Backend development
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Test runner development
cd test-runner
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

## 📋 Deployment Options

### Option 1: Docker Compose (Recommended for Development)

```bash
# Build and deploy all containers
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Option 2: Kubernetes (Recommended for Production)

```bash
# Deploy RBAC and services
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/test-runner.yaml
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/frontend.yaml

# Check status
kubectl get pods
kubectl get services
```

### Option 3: Automated Deployment Scripts

#### Linux/macOS

```bash
chmod +x deploy.sh
./deploy.sh --compose              # Docker Compose
./deploy.sh --kubernetes --push    # Kubernetes with registry push
```

#### Windows PowerShell

```powershell
.\deploy.ps1 -Compose              # Docker Compose
.\deploy.ps1 -Kubernetes -Push     # Kubernetes with registry push
```

## 🔄 Data Flow

### Complete Test Generation Flow

```
1. 🖥️  Frontend User Input
   └── WebSocket → Backend

2. 🤖 AI Test Generation
   └── Backend → AI Services (Gemini/Claude)

3. 🚀 Test Execution Request
   └── Backend → WebSocket → Test Runner

4. ☸️  Kubernetes Job Creation
   └── Test Runner → K8s API → Dynamic Containers

5. 🔍 Test Execution & Results
   └── Containers → Test Runner → Backend → Frontend
```

## 🔒 Security Features

- **Container Isolation**: Each test runs in a separate, ephemeral container
- **Resource Limits**: CPU and memory constraints prevent resource exhaustion
- **Network Isolation**: Test containers have no external network access
- **Automatic Cleanup**: Jobs and resources are automatically deleted after execution
- **RBAC**: Kubernetes role-based access control for test runner permissions

## 📊 Monitoring & Observability

### Logging

```bash
# Docker Compose logs
docker-compose logs -f frontend
docker-compose logs -f backend
docker-compose logs -f test-runner

# Kubernetes logs
kubectl logs -l component=frontend
kubectl logs -l component=backend
kubectl logs -l component=test-runner
```

## 🧪 Test Types Supported

| Type                  | Description           | Container Features               |
| --------------------- | --------------------- | -------------------------------- |
| **Unit Tests**        | Function validation   | Basic Python 3.11 environment    |
| **Memory Tests**      | Memory usage analysis | pytest-memory-profiler installed |
| **Performance Tests** | Execution timing      | Profiling tools included         |

## 🔧 Configuration

### Frontend Configuration

- Uses environment variables for runtime configuration
- Configure via `.env` files or runtime environment

### Backend & Test Runner Configuration

- Uses global constants defined in source code
- No environment variables required
- All configuration values are compile-time constants

### Kubernetes Resource Limits

```yaml
resources:
  limits:
    cpu: "500m"
    memory: "512Mi"
  requests:
    cpu: "100m"
    memory: "128Mi"
```

## 📖 API Documentation

### WebSocket Messages (Frontend ↔ Backend)

- `test_ai` - Validate AI API key
- `verify_code` - Validate code format
- `generate_tests` - Generate and execute tests
- `generate_docs` - Generate documentation
- `generate_improvements` - Generate code improvements

### Internal Messages (Backend ↔ Test Runner)

- Batch test execution requests
- Structured result responses

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Follow the coding guidelines in `.github/copilot-instructions.md`
4. Test your changes with both Docker Compose and Kubernetes
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: See `/docs` folder for detailed guides
- **Issues**: Create GitHub issues for bugs or feature requests
- **Architecture**: Review `/docs/architecture.md` for system design details

---

**CodeLens** - Transforming code quality through AI-powered testing in secure, scalable containers.
