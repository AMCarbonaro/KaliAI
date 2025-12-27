#!/bin/bash
# Test Ollama connection from orchestrator container

echo "🔍 Testing Ollama Connection..."
echo ""

# Check if orchestrator container is running
if ! docker ps | grep -q kali-orchestrator; then
    echo "❌ Orchestrator container is not running"
    exit 1
fi

echo "1. Testing network connectivity..."
if docker exec kali-orchestrator ping -c 1 ollama > /dev/null 2>&1; then
    echo "   ✅ Can ping 'ollama' hostname"
else
    echo "   ❌ Cannot ping 'ollama' hostname"
    echo "   Check network: docker network inspect kali-ai-orchestrator_orchestrator-network"
fi

echo ""
echo "2. Testing HTTP connection to Ollama..."
HTTP_CODE=$(docker exec kali-orchestrator curl -s -o /dev/null -w "%{http_code}" http://ollama:11434/api/tags 2>&1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ HTTP connection successful (200 OK)"
    echo ""
    echo "   Available models:"
    docker exec kali-orchestrator curl -s http://ollama:11434/api/tags | grep -o '"name":"[^"]*"' | head -5
else
    echo "   ❌ HTTP connection failed (code: $HTTP_CODE)"
    echo ""
    echo "   Full response:"
    docker exec kali-orchestrator curl -v http://ollama:11434/api/tags 2>&1 | head -20
fi

echo ""
echo "3. Checking environment variable..."
OLLAMA_URL=$(docker exec kali-orchestrator printenv KALI_ORCHESTRATOR_LLM__OLLAMA__BASE_URL)
if [ -n "$OLLAMA_URL" ]; then
    echo "   ✅ Environment variable set: $OLLAMA_URL"
else
    echo "   ⚠️  Environment variable not set"
    echo "   Should be: http://ollama:11434"
fi

echo ""
echo "4. Checking config file..."
CONFIG_URL=$(docker exec kali-orchestrator grep -A 2 "ollama:" /app/kali_orchestrator/config.yaml | grep "base_url" | awk '{print $2}' || echo "not found")
echo "   Config file base_url: $CONFIG_URL"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 If connection fails:"
echo "   1. Make sure Ollama is running: docker ps | grep ollama"
echo "   2. Check Ollama logs: docker logs kali-orchestrator-ollama"
echo "   3. Pull model if needed: docker exec kali-orchestrator-ollama ollama pull llama3.2"
echo "   4. Restart: docker-compose restart"

