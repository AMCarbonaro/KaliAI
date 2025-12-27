#!/bin/bash
# Quick script to check Ollama connection

echo "🔍 Checking Ollama connection..."
echo ""

# Check if Ollama container is running
if docker ps | grep -q kali-orchestrator-ollama; then
    echo "✅ Ollama container is running"
else
    echo "❌ Ollama container is NOT running"
    echo "   Start it: docker-compose up -d ollama"
    exit 1
fi

# Check Ollama health
echo ""
echo "🏥 Checking Ollama health..."
if docker exec kali-orchestrator-ollama curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama is responding"
else
    echo "❌ Ollama is NOT responding"
    echo "   It may still be starting up. Wait a minute and try again."
fi

# Test from orchestrator container
echo ""
echo "🔗 Testing connection from orchestrator container..."
if docker exec kali-orchestrator curl -s http://ollama:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Orchestrator can reach Ollama at http://ollama:11434"
else
    echo "❌ Orchestrator CANNOT reach Ollama"
    echo ""
    echo "💡 Troubleshooting:"
    echo "   1. Check if both containers are on the same network:"
    echo "      docker network inspect kali-ai-orchestrator_orchestrator-network"
    echo "   2. Check Ollama logs: docker logs kali-orchestrator-ollama"
    echo "   3. Restart both: docker-compose restart"
fi

echo ""
echo "📋 Ollama container logs (last 10 lines):"
docker logs --tail=10 kali-orchestrator-ollama

