#!/bin/bash
# Quick fix script for connection refused errors

echo "🔧 Fixing Connection Issues..."
echo ""

# Check if Ollama container is running
if ! docker ps | grep -q kali-orchestrator-ollama; then
    echo "❌ Ollama container is not running"
    echo "   Starting it..."
    docker-compose up -d ollama
    echo "   Waiting 30 seconds for Ollama to start..."
    sleep 30
fi

# Check if model is pulled
echo "📦 Checking if model 'llama3.2' is available..."
MODELS=$(docker exec kali-orchestrator-ollama ollama list 2>/dev/null | grep -c llama3.2 || echo "0")

if [ "$MODELS" -eq "0" ]; then
    echo "❌ Model 'llama3.2' is not pulled"
    echo "   Pulling it now (this will take 5-10 minutes)..."
    docker exec kali-orchestrator-ollama ollama pull llama3.2
    echo "✅ Model pulled successfully"
else
    echo "✅ Model 'llama3.2' is available"
fi

# Test connection
echo ""
echo "🔗 Testing connection..."
if docker exec kali-orchestrator curl -s http://ollama:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Connection successful!"
else
    echo "❌ Connection still failing"
    echo ""
    echo "💡 Try these steps:"
    echo "   1. Restart both containers:"
    echo "      docker-compose restart"
    echo "   2. Wait 30 seconds, then check logs:"
    echo "      docker logs kali-orchestrator-ollama"
    echo "   3. Check network:"
    echo "      docker network inspect kali-ai-orchestrator_orchestrator-network"
fi

echo ""
echo "📋 Current status:"
docker ps | grep -E "kali-orchestrator|NAME"

