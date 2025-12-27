# Complete Setup Guide - Kali AI Orchestrator

## Step-by-Step Instructions (Start Here!)

### Step 1: Open Terminal on Your Kali Machine
```bash
# Open a terminal (Ctrl+Alt+T or Applications > Terminal)
```

### Step 2: Navigate to Your Home Directory
```bash
cd ~
```

### Step 3: Clone the Repository
```bash
git clone https://github.com/AMCarbonaro/KaliAI.git
```

### Step 4: Enter the Project Directory
```bash
cd KaliAI
```

### Step 5: Make the Start Script Executable
```bash
chmod +x start.sh
```

### Step 6: Run the Start Script (Auto-Installs Everything)
```bash
./start.sh
```

**What happens:**
- ✅ Checks if Docker is installed (installs if missing)
- ✅ Installs docker-compose if needed
- ✅ Builds Docker containers
- ✅ Starts Ollama and the web app

**First time only:** If Docker was just installed, you'll see:
```
⚠️  IMPORTANT: You need to log out and log back in...
```

**If you see that message:**
1. Log out of your Kali session
2. Log back in
3. Run `./start.sh` again

### Step 7: Wait for Containers to Start
```bash
# Check if containers are running (wait 1-2 minutes for first build)
docker ps
```

You should see:
- `kali-orchestrator-ollama`
- `kali-orchestrator`

### Step 8: Pull the LLM Model (First Time Only)
```bash
# This downloads the AI model (takes 5-10 minutes depending on internet)
docker exec kali-orchestrator-ollama ollama pull llama3.2
```

**Wait for it to finish** - you'll see progress like:
```
pulling manifest
pulling 8b8d... 
pulling 8b8d... 100% ▕████████████████▏ 4.7 GB
```

### Step 9: Verify Everything is Working
```bash
# Check Ollama is ready
docker exec kali-orchestrator-ollama ollama list

# Should show:
# NAME      ID          SIZE    MODIFIED
# llama3.2  abc123...   4.7GB   just now
```

### Step 10: Open the Web Interface
Open your web browser and go to:
```
http://localhost:7860
```

### Step 11: Test It!
In the web interface, type:
```
hey
```

You should get a response from the AI!

---

## Troubleshooting

### If containers won't start:
```bash
# View logs
docker-compose logs -f

# Restart everything
docker-compose down
docker-compose up -d
```

### If web interface won't load:
```bash
# Check if port 7860 is accessible
curl http://localhost:7860

# Check container status
docker ps

# View orchestrator logs
docker logs kali-orchestrator
```

### If you get "Connection refused" error:
```bash
# Make sure Ollama model is pulled
docker exec kali-orchestrator-ollama ollama list

# If empty, pull it:
docker exec kali-orchestrator-ollama ollama pull llama3.2
```

### If Docker isn't working:
```bash
# Check Docker service
sudo systemctl status docker

# Start Docker if needed
sudo systemctl start docker

# Add yourself to docker group (if not done)
sudo usermod -aG docker $USER
# Then log out and back in
```

---

## Quick Reference Commands

```bash
# Start everything
./start.sh

# Stop everything
docker-compose down

# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Check status
docker ps

# Pull model
docker exec kali-orchestrator-ollama ollama pull llama3.2

# Check models
docker exec kali-orchestrator-ollama ollama list
```

---

## That's It!

Once you complete these steps, you'll have:
- ✅ Web interface at http://localhost:7860
- ✅ AI-powered pentesting orchestrator
- ✅ All tools ready to use

Just open your browser and start chatting with the AI!

