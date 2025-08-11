# CodeLens 🔍 

**Transform your Python code with AI-powered testing, documentation, and improvements**

✨ **Try it live at [https://codelens.online](https://codelens.online)** ✨

CodeLens analyzes your Python functions and automatically generates:
- 🧪 **Comprehensive test suites** with edge cases and mocking
- 📚 **Professional documentation** with examples and type hints  
- 🚀 **Code improvements** for performance, readability, and best practices
- 🔍 **Real-time execution** in secure, isolated containers

All powered by AI (Gemini/Claude) and executed in secure Kubernetes containers.

## 🎯 What Makes CodeLens Special

- **Zero Setup Required** - Just paste your code and get instant results
- **AI-Powered Analysis** - Leverages Google Gemini and Anthropic Claude
- **Secure Execution** - Each test runs in isolated Kubernetes containers  
- **Real-time Results** - WebSocket-based live updates
- **Production Ready** - Microservices architecture with full observability

## 🏗️ Infrastructure Overview

```
Frontend (Nuxt.js) ←→ Backend (FastAPI) ←→ Test Runner ←→ Kubernetes Jobs
     ↓                     ↓                   ↓              ↓
  User Interface      AI Integration    Job Management   Isolated Execution
```

## 🚀 Quick Local Setup

**Prerequisites:** Docker Desktop with Kubernetes enabled

### Option 1: One-Command Setup (Recommended)
```powershell
# Clone and start everything
git clone https://github.com/JakubTuta/CodeLens.git
cd CodeLens
.\scripts\local.ps1
```

### Option 2: Manual Steps  
```powershell
# Build images
.\scripts\build.ps1

# Deploy to local Kubernetes
kubectl apply -f k8s/local/

# Access at http://localhost:3000
```

**That's it!** The scripts handle all the complexity - building images, deploying to Kubernetes, and setting up port forwarding.

## 🌐 Deployment Options

| Environment | Command | Access |
|-------------|---------|---------|
| **Local Development** | `.\scripts\local.ps1` | http://localhost:3000 |
| **Production (GCP)** | `.\scripts\deploy.ps1` | https://codelens.online |

💡 **For detailed deployment guides**, see the comprehensive documentation in:
- `GCP-DEPLOYMENT-GUIDE.md` - Complete GCP setup with custom domains and SSL
- `k8s/README.md` - Kubernetes configuration details

## 🛡️ Security & Features

- **🔒 Container Isolation** - Each test runs in a separate, ephemeral container
- **⚡ Resource Limits** - CPU and memory constraints prevent resource exhaustion  
- **🌐 Network Security** - Test containers have no external network access
- **🧹 Auto-cleanup** - Jobs and resources are automatically deleted after execution
- **📊 Full Observability** - Comprehensive logging and monitoring

---

**CodeLens** - Making Python code analysis as simple as pasting your function and hitting enter. ✨
