#!/bin/bash
# Kali AI Orchestrator - One-Click Start Script
# Automatically installs Docker if needed

set -e

echo "🚀 Starting Kali AI Orchestrator Web App Setup..."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "🐳 Docker not found. Installing Docker on Kali Linux..."
    echo ""
    
    # Check if we're on Kali Linux
    if [ ! -f /etc/os-release ] || ! grep -q "Kali" /etc/os-release 2>/dev/null; then
        echo "⚠️  Warning: This script is optimized for Kali Linux."
        echo "   Docker installation may vary on other distributions."
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Update package list
    echo "📦 Updating package list..."
    sudo apt update
    
    # Install docker.io (Kali's recommended Docker package)
    echo "📥 Installing Docker..."
    sudo apt install -y docker.io
    
    # Install docker-compose if missing
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null 2>/dev/null; then
        echo "📥 Installing docker-compose..."
        sudo apt install -y docker-compose
    fi
    
    # Start and enable Docker service
    echo "🔧 Starting Docker service..."
    sudo systemctl enable docker --now
    
    # Add current user to docker group (so no sudo needed later)
    echo "👤 Adding user to docker group..."
    sudo usermod -aG docker $USER
    
    echo ""
    echo "✅ Docker installed successfully!"
    echo ""
    echo "⚠️  IMPORTANT: You need to log out and log back in (or reboot) for the docker group change to take effect."
    echo "   After logging back in, simply run this script again: ./start.sh"
    echo ""
    echo "   Alternatively, you can run: newgrp docker"
    echo "   Then run this script again in the new shell."
    echo ""
    exit 0
fi

# Check if user is in docker group (to avoid sudo issues)
if ! groups | grep -q docker; then
    echo "⚠️  You are not in the docker group. Adding you now..."
    sudo usermod -aG docker $USER
    echo "⚠️  You need to log out and back in for this to take effect."
    echo "   Or run: newgrp docker"
    echo "   Then run this script again."
    exit 0
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null 2>/dev/null; then
    echo "📥 Installing docker-compose..."
    sudo apt update
    sudo apt install -y docker-compose
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "🔧 Starting Docker daemon..."
    sudo systemctl start docker
fi

echo "✅ Docker is ready. Proceeding with orchestrator setup..."
echo ""

# Use docker compose (v2) if available, otherwise docker-compose (v1)
if docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

echo "🔨 Building and starting containers (this may take a few minutes the first time)..."
echo ""

# Start services
$DOCKER_COMPOSE up -d --build

echo ""
echo "✅ Kali AI Orchestrator is starting..."
echo ""
echo "🌐 Web interface will be available at: http://localhost:7860"
echo ""
echo "⏳ Waiting for services to be ready (this may take a minute)..."
echo ""

# Wait for web interface to be ready
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:7860 > /dev/null 2>&1; then
        echo "✅ Web interface is ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo -n "."
    sleep 2
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎯 Kali AI Orchestrator is running!"
echo ""
echo "   Web Interface: http://localhost:7860"
echo "   Ollama API:    http://localhost:11434"
echo "   hexstrike-ai:  http://localhost:8888"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Useful commands:"
echo "   View logs:        $DOCKER_COMPOSE logs -f"
echo "   Stop services:    $DOCKER_COMPOSE down"
echo "   Restart:          $DOCKER_COMPOSE restart"
echo "   View status:      $DOCKER_COMPOSE ps"
echo ""
echo "💡 Tip: Open http://localhost:7860 in your browser to start using the orchestrator!"
echo ""

