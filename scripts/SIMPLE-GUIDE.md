# CodeLens - Simple Setup Guide

## 🚀 Super Simple 1-Step Process

### Step 1: Setup (One Time Only)

1. Install **Docker Desktop**
2. In Docker Desktop settings, enable **Kubernetes**
3. Wait for Kubernetes to start (green icon in Docker Desktop)

### Step 2: Run Everything with One Command

```powershell
.\run-app.ps1
```

This single command will:

- ✅ Build all your container images
- ✅ Stop any old version running
- ✅ Start your new application
- ✅ Set up all connections automatically

**That's it!** Your app will be running at:

- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **Test Runner**: http://localhost:8001

## 📋 Available Commands

### Main Command (Recommended)

| Command         | What it does                                                 |
| --------------- | ------------------------------------------------------------ |
| `.\run-app.ps1` | **Does everything!** Build, stop old, start new, connect all |

### Individual Scripts (in scripts/ folder)

| Command                 | What it does                |
| ----------------------- | --------------------------- |
| `.\scripts\build.ps1`   | Build all container images  |
| `.\scripts\start.ps1`   | Start the application       |
| `.\scripts\stop.ps1`    | Stop the application        |
| `.\scripts\connect.ps1` | Interactive connection menu |

## 🔄 Development Workflow

**Simple workflow:**

1. **Make code changes**
2. **Run `.\run-app.ps1`** (rebuilds and restarts everything)
3. **Your changes are live!**

**Advanced workflow** (if you want more control):

1. **Make code changes**
2. **Run `.\scripts\build.ps1`** (rebuilds with your changes)
3. **Run `.\scripts\stop.ps1`** (stop old version)
4. **Run `.\scripts\start.ps1`** (start new version)
5. **Run `.\scripts\connect.ps1`** (connect to services)

## 🆘 Troubleshooting

**Problem**: "kubectl not found"

- **Solution**: Enable Kubernetes in Docker Desktop settings

**Problem**: "Cannot connect to cluster"

- **Solution**: Make sure Docker Desktop is running and Kubernetes is enabled

**Problem**: "Build failed"

- **Solution**: Check if Docker Desktop is running

**Problem**: "Port already in use"

- **Solution**: Run `Stop-Job *port-forward*; Remove-Job *port-forward*` then try again

**Problem**: Can't access http://localhost:3000

- **Solution**: Wait a few moments after running the script, services need time to start

## 🧹 Clean Up

To completely stop and remove everything:

```powershell
# Stop port forwarding
Stop-Job *port-forward*; Remove-Job *port-forward*

# Stop the application
.\scripts\stop.ps1
```

That's it! Keep it simple! 🎉
