#!/bin/bash
# Test script to verify web app launches correctly

echo "🧪 Testing Kali AI Orchestrator Web App Launch..."
echo ""

# Check if container is running
if ! docker ps | grep -q kali-orchestrator; then
    echo "❌ Container is not running. Start it first:"
    echo "   docker-compose up -d"
    exit 1
fi

echo "✅ Container is running"
echo ""

# Check logs for errors
echo "📋 Checking recent logs for errors..."
ERRORS=$(docker logs kali-orchestrator 2>&1 | tail -50 | grep -i "error\|exception\|traceback\|failed" | head -5)

if [ -z "$ERRORS" ]; then
    echo "✅ No errors found in recent logs"
else
    echo "⚠️  Potential issues found:"
    echo "$ERRORS"
fi
echo ""

# Check if Gradio is running
echo "🔍 Checking if Gradio server is running..."
if docker exec kali-orchestrator ps aux | grep -q "[p]ython.*web_app"; then
    echo "✅ Python web_app process is running"
else
    echo "❌ Python web_app process is NOT running"
    echo "   Check logs: docker logs kali-orchestrator"
    exit 1
fi
echo ""

# Test HTTP connection
echo "🌐 Testing HTTP connection..."
MAX_ATTEMPTS=10
ATTEMPT=0
SUCCESS=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:7860 | grep -q "200\|302"; then
        echo "✅ Web interface is responding!"
        SUCCESS=1
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    echo -n "."
    sleep 2
done

echo ""

if [ $SUCCESS -eq 1 ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🎉 SUCCESS! Web app is running!"
    echo ""
    echo "   Open in browser: http://localhost:7860"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
else
    echo ""
    echo "❌ Web interface is not responding"
    echo ""
    echo "📋 Full container logs:"
    docker logs --tail=30 kali-orchestrator
    echo ""
    echo "💡 Try:"
    echo "   docker-compose restart orchestrator"
    echo "   docker-compose logs -f orchestrator"
    exit 1
fi

