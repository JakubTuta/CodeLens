# CodeLens - Development Made Simple 🚀

## One Command to Rule Them All

```powershell
.\run-app.ps1
```

That's it! This single command will:

- ✅ Build all your containers
- ✅ Stop any old version
- ✅ Start your new application
- ✅ Connect everything automatically

## Quick Access

Your application will be available at:

- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **Test Runner**: http://localhost:8001

## Prerequisites

1. Install **Docker Desktop**
2. Enable **Kubernetes** in Docker Desktop settings
3. Wait for Kubernetes to start (green icon)

## File Organization

```
CodeLens/
├── run-app.ps1           # 🚀 Main script - does everything!
├── scripts/              # 📁 Individual scripts (if you need them)
│   ├── build.ps1         # Build containers
│   ├── start.ps1         # Start application
│   ├── stop.ps1          # Stop application
│   ├── connect.ps1       # Interactive connection
│   └── SIMPLE-GUIDE.md   # Detailed guide
├── frontend/             # Nuxt.js application
├── backend/              # FastAPI application
├── test-runner/          # Test execution service
└── k8s/                  # Kubernetes manifests
```

## Development Workflow

1. **Make your code changes**
2. **Run `.\run-app.ps1`**
3. **Your changes are live!**

## Stopping Everything

```powershell
# Stop port forwarding
Stop-Job *port-forward*; Remove-Job *port-forward*

# Stop the application
.\scripts\stop.ps1
```

## Need Help?

- Run `.\run-app.ps1 -Help` for detailed info
- Check `scripts\SIMPLE-GUIDE.md` for troubleshooting
- All scripts have clear error messages and instructions

---

**No more complex commands. No more multiple terminals. Just one script that does everything!** 🎉
