#!/bin/bash
# Quick fix for connection refused - ensures everything is set up correctly

echo "🔧 Quick Fix for Connection Refused..."
echo ""

# Step 1: Make sure Ollama is running
echo "1. Checking Ollama container..."
if ! docker ps | grep -q kali-orchestrator-ollama; then
    echo "   Starting Ollama..."
    docker-compose up -d ollama
    sleep 10
fi
echo "   ✅ Ollama container running"

# Step 2: Check if model is pulled
echo ""
echo "2. Checking for llama3.2 model..."
if docker exec kali-orchestrator-ollama ollama list 2>/dev/null | grep -q llama3.2; then
    echo "   ✅ Model llama3.2 is available"
else
    echo "   ❌ Model not found. Pulling now (this takes 5-10 minutes)..."
    docker exec kali-orchestrator-ollama ollama pull llama3.2
    echo "   ✅ Model pulled"
fi

# Step 3: Verify environment variable
echo ""
echo "3. Checking environment variable..."
if docker exec kali-orchestrator printenv KALI_ORCHESTRATOR_LLM__OLLAMA__BASE_URL | grep -q ollama; then
    echo "   ✅ Environment variable set correctly: http://ollama:11434"
else
    echo "   ⚠️  Environment variable not set or incorrect"
    echo "   Restarting orchestrator to set it..."
    docker-compose restart orchestrator
    sleep 5
fi

# Step 4: Test connection
echo ""
echo "4. Testing connection..."
if docker exec kali-orchestrator curl -s http://ollama:11434/api/tags > /dev/null 2>&1; then
    echo "   ✅ Connection successful!"
else
    echo "   ❌ Connection failed"
    echo ""
    echo "   Trying to fix..."
    docker-compose restart
    sleep 10
    echo "   Retesting..."
    if docker exec kali-orchestrator curl -s http://ollama:11434/api/tags > /dev/null 2>&1; then
        echo "   ✅ Connection successful after restart!"
    else
        echo "   ❌ Still failing. Check logs:"
        echo "      docker logs kali-orchestrator"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Next steps:"
echo "   1. Check orchestrator logs: docker logs kali-orchestrator | grep Ollama"
echo "   2. Refresh browser at http://localhost:7860"
echo "   3. Try typing 'hi' again"
echo ""

