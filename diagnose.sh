#!/bin/bash
# Comprehensive diagnostic script

echo "🔍 Comprehensive Diagnostic..."
echo ""

# 1. Check containers
echo "1. Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "kali-orchestrator|NAME"
echo ""

# 2. Check Ollama specifically
echo "2. Ollama Container:"
if docker ps | grep -q kali-orchestrator-ollama; then
    echo "   ✅ Running"
    echo "   Status: $(docker ps --format '{{.Status}}' --filter name=kali-orchestrator-ollama)"
else
    echo "   ❌ NOT running"
    echo "   Start it: docker-compose up -d ollama"
    exit 1
fi
echo ""

# 3. Check if model is available
echo "3. Ollama Models:"
MODELS=$(docker exec kali-orchestrator-ollama ollama list 2>&1)
if echo "$MODELS" | grep -q "llama3.2"; then
    echo "   ✅ llama3.2 is available"
    echo "$MODELS" | grep llama3.2
else
    echo "   ❌ llama3.2 NOT found"
    echo "   Available models:"
    echo "$MODELS"
    echo ""
    echo "   💡 Pull it: docker exec kali-orchestrator-ollama ollama pull llama3.2"
fi
echo ""

# 4. Test network connectivity
echo "4. Network Connectivity:"
if docker exec kali-orchestrator ping -c 1 -W 2 ollama > /dev/null 2>&1; then
    echo "   ✅ Can ping 'ollama' hostname"
else
    echo "   ❌ Cannot ping 'ollama' hostname"
    echo "   Network issue detected!"
fi
echo ""

# 5. Test HTTP connection
echo "5. HTTP Connection Test:"
HTTP_TEST=$(docker exec kali-orchestrator curl -s -w "\nHTTP_CODE:%{http_code}" http://ollama:11434/api/tags 2>&1)
HTTP_CODE=$(echo "$HTTP_TEST" | grep "HTTP_CODE" | cut -d: -f2)
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ HTTP connection successful (200 OK)"
    echo "   Response preview:"
    echo "$HTTP_TEST" | head -3
else
    echo "   ❌ HTTP connection failed"
    echo "   HTTP Code: $HTTP_CODE"
    echo "   Full response:"
    echo "$HTTP_TEST" | head -10
fi
echo ""

# 6. Check environment variable
echo "6. Environment Variables:"
ENV_URL=$(docker exec kali-orchestrator printenv KALI_ORCHESTRATOR_LLM__OLLAMA__BASE_URL 2>/dev/null)
if [ -n "$ENV_URL" ]; then
    echo "   ✅ KALI_ORCHESTRATOR_LLM__OLLAMA__BASE_URL=$ENV_URL"
else
    echo "   ❌ Environment variable NOT set"
    echo "   Should be: http://ollama:11434"
fi
echo ""

# 7. Check what the app is actually using
echo "7. Application Logs (Ollama URL):"
docker logs kali-orchestrator 2>&1 | grep -i "ollama url" | tail -3
if [ $? -ne 0 ]; then
    echo "   ⚠️  No Ollama URL found in logs"
    echo "   Recent logs:"
    docker logs kali-orchestrator 2>&1 | tail -5
fi
echo ""

# 8. Check for errors
echo "8. Recent Errors:"
ERRORS=$(docker logs kali-orchestrator 2>&1 | grep -i "error\|refused\|connection" | tail -5)
if [ -n "$ERRORS" ]; then
    echo "   Found errors:"
    echo "$ERRORS"
else
    echo "   ✅ No recent errors found"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Summary:"
echo ""

# Determine issue
if ! docker exec kali-orchestrator-ollama ollama list 2>&1 | grep -q llama3.2; then
    echo "❌ ISSUE: Model 'llama3.2' is not pulled"
    echo "   FIX: docker exec kali-orchestrator-ollama ollama pull llama3.2"
elif [ "$HTTP_CODE" != "200" ]; then
    echo "❌ ISSUE: Cannot connect to Ollama HTTP API"
    echo "   Check network and Ollama logs: docker logs kali-orchestrator-ollama"
elif [ -z "$ENV_URL" ]; then
    echo "❌ ISSUE: Environment variable not set"
    echo "   FIX: docker-compose restart orchestrator"
else
    echo "✅ All checks passed - connection should work!"
    echo "   If still getting errors, check: docker logs kali-orchestrator"
fi
echo ""

