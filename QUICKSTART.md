# Quick Start Guide - Web App

## 🚀 One-Command Start (Zero Installation Required!)

The script automatically installs Docker if needed - you don't need to do anything!

### Step 1: Download
```bash
git clone https://github.com/AMCarbonaro/KaliAI.git
cd KaliAI
```

### Step 2: Start (Auto-Installs Docker if Needed)
```bash
chmod +x start.sh
./start.sh
```

**First time?** The script will:
- ✅ Automatically install Docker (if not present)
- ✅ Install docker-compose
- ✅ Set up everything for you
- ⚠️ **Note:** After first Docker install, you'll need to log out and back in (or run `newgrp docker`), then run `./start.sh` again

### Step 3: Use
Open your browser to: **http://localhost:7860**

That's it! No manual installation, no pip install, no configuration files to edit - everything is automatic!

## What You Get

- ✅ Full web interface with chat UI
- ✅ All Kali tools pre-configured
- ✅ Ollama LLM included (local, private)
- ✅ Session management
- ✅ Report generation
- ✅ Agent personas

## First Query Example

Try this in the web interface:

```
Scan 192.168.1.0/24 for open HTTP services and suggest next steps
```

The orchestrator will:
1. Check scope (make sure 192.168.1.0/24 is in your config.yaml)
2. Run Nmap scan
3. Detect HTTP services
4. Suggest vulnerability scans
5. Display results in the chat

## Stopping the App

```bash
docker-compose down
```

## Troubleshooting

**Port already in use?**
- Change port in `docker-compose.yml`: `7860:7860` → `8080:7860`
- Then access at http://localhost:8080

**Docker installation issues?**
- The script auto-installs Docker, but if you have problems:
  1. First run: `./start.sh` (it will install Docker)
  2. Log out and back in (or run `newgrp docker`)
  3. Run `./start.sh` again
- Manual install (if auto-install fails):
  ```bash
  sudo apt update
  sudo apt install -y docker.io docker-compose
  sudo systemctl enable docker --now
  sudo usermod -aG docker $USER
  # Log out and back in
  ```

**Need help?**
- Check logs: `docker-compose logs -f`
- View status: `docker-compose ps`

