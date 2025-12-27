#!/bin/bash
# Kali AI Orchestrator - One-Click Start Script

set -e

echo "🚀 Starting Kali AI Orchestrator..."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Install: curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install docker-compose first."
    echo "   Install: sudo apt install docker-compose"
    exit 1
fi

# Use docker compose (v2) if available, otherwise docker-compose (v1)
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

echo "📦 Building and starting containers..."
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

